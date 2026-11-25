#!/usr/bin/env python3
"""Assemble a GitHub Pages XBPS repository from approved, signed releases."""

import argparse
import hashlib
from pathlib import Path
import json
import os
import plistlib
import re
import runpy
import shutil
import subprocess
import tarfile
import tempfile


channel = runpy.run_path(str(Path(__file__).with_name("sync-channel.py")))
INDEX = channel["INDEX"]
PACKAGES = channel["PACKAGES"]
SPKI = channel["SPKI"]
digest = channel["digest"]
fetch = channel["fetch"]
verify = channel["verify"]
SITE_LIMIT = 900_000_000
INDEX_LIMIT = 8 * 1024**2


def release_order(version):
    match = re.fullmatch(r"1\.0\.0beta([0-9]+)_([1-9][0-9]*)", version)
    if not match:
        raise ValueError(f"Invalid native release version: {version}")
    return tuple(map(int, match.groups())), "xbps-beta" + "_".join(match.groups())


def public_key_hash(key):
    public = subprocess.check_output(
        ["openssl", "pkey", "-pubin", "-in", str(key), "-outform", "DER"]
    )
    return hashlib.sha256(public).hexdigest()


def verified_manifest(work, manifest_digest):
    manifest = work / "SHA256SUMS"
    if digest(manifest) != manifest_digest:
        raise ValueError("Release manifest differs from the approved digest")
    if public_key_hash(work / "xbps-public.pem") != SPKI:
        raise ValueError("Unexpected release signing key")
    verify(work / "xbps-public.pem", work / "SHA256SUMS.sig", manifest)
    hashes = {}
    for line in manifest.read_text(encoding="ascii").splitlines():
        entry = re.fullmatch(r"([0-9a-f]{64}) [ *]([A-Za-z0-9_.+-]+)", line)
        if not entry or entry[2] in hashes:
            raise ValueError("Invalid or duplicate signed manifest entry")
        hashes[entry[2]] = entry[1]
    return hashes


def read_index(work, version, hashes):
    records = {}
    with tarfile.open(work / INDEX, "r:zst") as archive:
        for member in archive:
            if member.name not in ("index.plist", "index-meta.plist"):
                continue
            if not member.isfile() or member.size > INDEX_LIMIT or member.name in records:
                raise ValueError("Unexpected XBPS index member")
            records[member.name] = plistlib.loads(archive.extractfile(member).read())
    if set(records) != {"index.plist", "index-meta.plist"}:
        raise ValueError("Missing XBPS index metadata")
    index = records["index.plist"]
    meta = records["index-meta.plist"]
    if meta["signature-type"] != "rsa" or meta["public-key-size"] != 4096:
        raise ValueError("Unexpected XBPS signature metadata")
    embedded = work / "index-key.pem"
    embedded.write_bytes(meta["public-key"])
    if public_key_hash(embedded) != SPKI:
        raise ValueError("Unexpected public key in XBPS index")
    if set(index) != set(PACKAGES):
        raise ValueError("XBPS index must list the four coordinated packages")
    wall, deck, lens, paper = PACKAGES
    for name, record in index.items():
        pkgver = f"{name}-{version}"
        filename = f"{pkgver}.x86_64.xbps"
        if (record["architecture"] != "x86_64" or record["pkgver"] != pkgver
                or record["filename-sha256"] != hashes[filename]):
            raise ValueError(f"Unexpected XBPS index record for {name}")
        depends = record.get("run_depends", [])
        if name == wall and not {f"{deck}-{version}", f"{paper}-{version}"} <= set(depends):
            raise ValueError("Wall must require the matching Deck and Paper versions")
        if name != lens and any(re.match(rf"{re.escape(lens)}(?:[<>=]|-[0-9]|$)", dep)
                                for dep in depends):
            raise ValueError(f"Lens must remain optional for {name}")
    return index


def stage_release(work, release, source):
    version = release["version"]
    _, tag = release_order(version)

    def get(name, limit):
        target = work / name
        if source is None:
            fetch(f'{channel["RELEASES"]}/{tag}/{name}', target, limit)
        else:
            original = source / tag / name
            if not original.is_file() or original.stat().st_size > limit:
                raise ValueError(f"Missing or oversized local input: {original}")
            shutil.copyfile(original, target)
        return target

    for name, limit in (("xbps-public.pem", 16384), ("SHA256SUMS", 65536), ("SHA256SUMS.sig", 16384)):
        get(name, limit)
    hashes = verified_manifest(work, release["manifest_sha256"])
    if digest(get(INDEX, INDEX_LIMIT)) != hashes[INDEX]:
        raise ValueError("Index differs from authenticated release")
    index = read_index(work, version, hashes)
    for name in PACKAGES:
        filename = f"{name}-{version}.x86_64.xbps"
        signature = filename + ".sig2"
        size = index[name]["filename-size"]
        if type(size) is not int or not 0 < size < SITE_LIMIT:
            raise ValueError(f"Invalid package size: {filename}")
        package = get(filename, size)
        if (package.stat().st_size != size or digest(package) != hashes[filename]
                or digest(get(signature, 16384)) != hashes[signature]):
            raise ValueError(f"Package or signature differs from authenticated release: {filename}")
        verify(work / "xbps-public.pem", work / signature, package)
        yield package
        yield work / signature


def build(policy, output, source):
    data = json.loads(policy.read_text())
    releases = data["releases"]
    orders = [release_order(entry["version"])[0] for entry in releases]
    if data["schema"] != 1 or not orders or orders != sorted(set(orders)):
        raise ValueError("Release policy must list unique versions in increasing order")
    if os.path.lexists(output):
        raise ValueError(f"Output already exists: {output}")
    total = 0
    with tempfile.TemporaryDirectory(prefix=".native-pages-", dir=output.parent) as directory:
        temporary = Path(directory)
        site = temporary / "site"
        site.mkdir()
        for i, release in enumerate(releases):
            work = temporary / str(i)
            work.mkdir()
            for asset in stage_release(work, release, source):
                total += asset.stat().st_size
                if total > SITE_LIMIT:
                    raise ValueError("Pages repository exceeds the 900 MB staging budget")
                asset.rename(site / asset.name)
            if i == len(releases) - 1:
                total += (work / INDEX).stat().st_size
                if total > SITE_LIMIT:
                    raise ValueError("Pages repository exceeds the 900 MB staging budget")
                (work / INDEX).rename(site / INDEX)
        site.rename(output)
    print(f"Staged {releases[-1]['version']} and {len(releases) - 1} retained releases ({total} bytes)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", type=Path, help="Offline mirror with one subdirectory per release tag")
    args = parser.parse_args()
    try:
        build(args.policy, args.output, args.source)
    except (OSError, ValueError, TypeError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Native Pages: {error}\n")


if __name__ == "__main__":
    main()
