#!/usr/bin/python3 -I
"""Verify and atomically activate the Skwd-wall XBPS stable snapshot."""

import argparse
import base64
import fcntl
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener


CHANNEL = "https://raw.githubusercontent.com/SirOtter0/skwd-void-repo/main/stable/channel.json"
RELEASES = "https://github.com/SirOtter0/skwd-void-repo/releases/download"
SPKI = "3860084bca30b2022dd851490ba2f920524feb1dd38b578f69252e0a76e9d987"
FINGERPRINT = "cb:49:33:d0:b1:e9:be:a6:3d:85:96:11:04:c4:50:e8"
STATE = Path("/var/lib/skwd-xbps")
CONFIG = Path("/etc/xbps.d/30-skwd-void.conf")
MIN_VERSION = "1.0.0beta29_2"
PACKAGES = ("skwd-wall-v2-local", "skwd-deck-local", "skwd-lens-local", "skwd-paper-local")
INDEX = "x86_64-repodata"
MAX_AGE = 90 * 86400


def run(*argv):
    return subprocess.check_output(argv)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class HTTPSOnly(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != "https":
            raise ValueError("Refusing a non-HTTPS redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, target, limit):
    if urlsplit(url).scheme != "https":
        raise ValueError("Expected an HTTPS URL")
    deadline = time.monotonic() + 300
    with build_opener(HTTPSOnly()).open(url, timeout=15) as response, target.open("xb") as output:
        length = response.headers.get("Content-Length")
        if length is not None and not 0 <= int(length) <= limit:
            raise ValueError(f"Unexpected download size for {target.name}")
        total = 0
        while chunk := response.read1(1024 * 1024):
            total += len(chunk)
            if total > limit or time.monotonic() > deadline:
                raise ValueError(f"Download limit exceeded for {target.name}")
            output.write(chunk)
        if time.monotonic() > deadline:
            raise ValueError(f"Download deadline exceeded for {target.name}")
        if length is not None and total != int(length):
            raise ValueError(f"Incomplete download for {target.name}")


def verify(key, signature, payload):
    run("openssl", "dgst", "-sha256", "-verify", str(key), "-signature",
        str(signature), str(payload))


def compare(version, previous):
    code = subprocess.run(["xbps-uhelper", "cmpver", version, previous], check=False).returncode
    if code not in (0, 1, 255):
        raise ValueError("XBPS could not compare package versions")
    return -1 if code == 255 else code


def check_window(metadata):
    now = int(time.time())
    if not metadata["issued"] <= now < metadata["expires"]:
        raise ValueError("Signed channel is expired or not yet valid")


def read_channel(stage):
    fetch(CHANNEL, stage / "channel.json", 32768)
    envelope = json.loads((stage / "channel.json").read_bytes())
    for field, name in (("payload", "channel.payload"), ("signature", "channel.sig")):
        (stage / name).write_bytes(base64.b64decode(envelope[field], validate=True))
    metadata = json.loads((stage / "channel.payload").read_bytes())
    version = metadata["version"]
    match = re.fullmatch(r"1\.0\.0beta([0-9]+)_([1-9][0-9]*)", version)
    if not match or metadata["tag"] != "xbps-beta" + "_".join(match.groups()):
        raise ValueError("Invalid release version or tag")
    origin = f"{RELEASES}/{metadata['tag']}"
    key = stage / "xbps-public.pem"
    fetch(f"{origin}/xbps-public.pem", key, 16384)
    der = run("openssl", "pkey", "-pubin", "-in", str(key), "-outform", "DER")
    if hashlib.sha256(der).hexdigest() != SPKI:
        raise ValueError("Unexpected production public key")
    verify(key, stage / "channel.sig", stage / "channel.payload")
    seq, issued, expires = (metadata[k] for k in ("sequence", "issued", "expires"))
    if (metadata["schema"] != 1 or any(type(n) is not int for n in (seq, issued, expires))
            or seq < 1 or not (issued < expires <= issued + MAX_AGE)
            or compare(version, MIN_VERSION) < 0
            or not re.fullmatch(r"[0-9a-f]{64}", metadata["manifest_sha256"])):
        raise ValueError("Invalid or unsupported signed channel metadata")
    check_window(metadata)
    return metadata, origin


def read_manifest(stage, metadata, origin):
    for name in ("SHA256SUMS", "SHA256SUMS.sig"):
        fetch(f"{origin}/{name}", stage / name, 65536)
    manifest = stage / "SHA256SUMS"
    if digest(manifest) != metadata["manifest_sha256"]:
        raise ValueError("Release manifest does not match the signed channel")
    verify(stage / "xbps-public.pem", stage / "SHA256SUMS.sig", manifest)
    hashes = {}
    for line in manifest.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64}) [ *]([A-Za-z0-9_.+-]+)", line)
        if not match or match[2] in hashes:
            raise ValueError("Invalid or duplicate entry in release manifest")
        hashes[match[2]] = match[1]
    return hashes


def validate_snapshot(stage, metadata, origin):
    hashes = read_manifest(stage, metadata, origin)
    version = metadata["version"]
    packages = [f"{name}-{version}.x86_64.xbps" for name in PACKAGES]
    assets = {INDEX: 8 * 1024**2}
    for package in packages:
        assets[package] = 1024**3
        assets[f"{package}.sig2"] = 16384
    if not assets.keys() <= hashes.keys():
        raise ValueError("Release manifest is missing repository assets")
    for name, limit in assets.items():
        fetch(f"{origin}/{name}", stage / name, limit)
        if digest(stage / name) != hashes[name]:
            raise ValueError(f"Incorrect signed SHA-256 for {name}")
    for name in packages:
        verify(stage / "xbps-public.pem", stage / f"{name}.sig2", stage / name)
    query = ("xbps-query", "-i", "-R", "--repository", str(stage))
    if FINGERPRINT.encode() not in run(*query, "-v", "-L").split():
        raise ValueError("Unexpected XBPS index key fingerprint")
    listing = run(*query, "-s", "").decode().splitlines()
    versions = [line.split(maxsplit=2)[1] for line in listing]
    if sorted(versions) != sorted(f"{name}-{version}" for name in PACKAGES):
        raise ValueError("Index must contain exactly the four coordinated package versions")
    for name, package in zip(PACKAGES, packages):
        indexed = run(*query, "-p", "filename-sha256", name).decode().strip()
        if indexed != hashes[package]:
            raise ValueError(f"Index hash does not match the verified file for {name}")
    wall, deck, lens, paper = PACKAGES
    for name in (wall, deck, paper):
        depends = run(*query, "-p", "run_depends", name).decode().splitlines()
        if name == wall and not {f"{deck}-{version}", f"{paper}-{version}"} <= set(depends):
            raise ValueError("Wall must pin Deck and Paper to the same package version")
        if any(re.match(rf"{re.escape(lens)}(?:[<>=]|-[0-9]|$)", dep) for dep in depends):
            raise ValueError(f"Lens must remain optional for {name}")


def trusted_directory(path, private=False):
    for directory in (*reversed(path.parents), path):
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError(f"Expected a root-owned, non-writable directory: {directory}")
    if private and info.st_mode & 0o077:
        raise ValueError(f"State must be a root-only directory: {path}")


def safe_regular(directory, name, flags, mode=0o600, forbidden=0o022):
    fd = os.open(directory / name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, mode)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1
                or info.st_mode & forbidden):
            raise ValueError(f"Unsafe file: {directory / name}")
        return fd
    except BaseException:
        os.close(fd)
        raise


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def activate(stage, metadata):
    with tempfile.TemporaryDirectory(prefix="publish-", dir=STATE) as hold:
        hold = Path(hold)
        generation = hold / "repository"
        for path in stage.iterdir():
            with path.open("rb") as file:
                os.fsync(file.fileno())
        sync_dir(stage)
        stage.rename(generation)
        final = STATE / f"snapshot-{metadata['sequence']}-{hold.name}"
        generation.rename(final)
        sync_dir(STATE)
        cursor = hold / "current"
        cursor.symlink_to(final.name)
        check_window(metadata)
        cursor.replace(STATE / "current")
        sync_dir(STATE)


def synchronize():
    with tempfile.TemporaryDirectory(prefix=".download-", dir=STATE) as directory:
        stage = Path(directory)
        metadata, origin = read_channel(stage)
        current = STATE / "current"
        if os.path.lexists(current):
            target = os.readlink(current)
            if not re.fullmatch(r"snapshot-[1-9][0-9]*-publish-[a-z0-9_]{8}", target):
                raise ValueError("Invalid current repository pointer")
            directory = STATE / target
            trusted_directory(directory, private=True)
            with os.fdopen(safe_regular(directory, "channel.payload", os.O_RDONLY), "rb") as previous:
                previous_payload = previous.read(32768)
            old = json.loads(previous_payload)
            order = compare(metadata["version"], old["version"])
            if metadata["sequence"] < old["sequence"] or order < 0:
                raise ValueError("Refusing an older signed channel or package version")
            if metadata["sequence"] == old["sequence"]:
                if previous_payload != (stage / "channel.payload").read_bytes():
                    raise ValueError("Conflicting payload for the current sequence")
                return metadata
            if order == 0 and metadata["manifest_sha256"] != old["manifest_sha256"]:
                raise ValueError("Refusing changed artifacts under the same package version")
        validate_snapshot(stage, metadata, origin)
        activate(stage, metadata)
        return metadata


def configure():
    content = f"repository={STATE / 'current'}\n"
    trusted_directory(CONFIG.parent.parent)
    CONFIG.parent.mkdir(exist_ok=True)
    trusted_directory(CONFIG.parent)
    with tempfile.NamedTemporaryFile(mode="w", dir=CONFIG.parent) as config:
        config.write(content)
        config.flush()
        os.fchmod(config.fileno(), 0o644)
        os.fsync(config.fileno())
        try:
            os.link(config.name, CONFIG)
        except FileExistsError:
            with os.fdopen(safe_regular(CONFIG.parent, CONFIG.name, os.O_RDONLY), "rb") as existing:
                contents = existing.read(len(content) + 1)
            if contents != content.encode("ascii"):
                raise ValueError(f"Existing XBPS configuration differs: {CONFIG}")
        sync_dir(CONFIG.parent)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configure", action="store_true", help="register the verified local repository")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("run as root")
    os.umask(0o077)
    os.environ["LC_ALL"] = "C"
    os.environ["PATH"] = "/usr/bin:/usr/sbin:/bin:/sbin"
    try:
        trusted_directory(STATE.parent)
        STATE.mkdir(mode=0o700, exist_ok=True)
        trusted_directory(STATE, private=True)
        lock_fd = safe_regular(STATE, ".lock", os.O_WRONLY | os.O_CREAT, forbidden=0o077)
        with os.fdopen(lock_fd, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            metadata = synchronize()
            if args.configure:
                configure()
            print(f"Verified stable release {metadata['version']} (sequence {metadata['sequence']})")
    except (OSError, ValueError, TypeError, LookupError, HTTPException, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Skwd channel: {error}\n")


if __name__ == "__main__":
    main()
