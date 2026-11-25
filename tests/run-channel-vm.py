#!/usr/bin/env python3
"""Run the stable channel integration test using an existing clean Void/QEMU base."""

import argparse
import base64
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import tempfile
import threading
import time


REPO = Path(__file__).resolve().parents[1]
PACKAGES = ("skwd-wall-v2-local", "skwd-deck-local", "skwd-lens-local", "skwd-paper-local")
REV = ("1.0.0beta29_2", "1.0.0beta29_3")


def run(*argv, **kwargs):
    return subprocess.check_output([str(arg) for arg in argv], **kwargs)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sign(key, payload, signature):
    run("openssl", "dgst", "-sha256", "-sign", key, "-out", signature, payload)


def make_release(directory, payload, key, version, published_key, invalid_sig=False):
    directory.mkdir(parents=True)
    files = []
    for package in PACKAGES:
        dependencies = []
        if package == PACKAGES[0]:
            dependencies = ["-D", f"{PACKAGES[1]}-{version} {PACKAGES[3]}-{version}"]
        relative = payload / "usr/share/skwd-channel-lab" / package
        relative.parent.mkdir(parents=True, exist_ok=True)
        relative.write_text(version + "\n")
        run("xbps-create", "-A", "x86_64", "-n", f"{package}-{version}",
            "-s", "Skwd channel VM fixture", *dependencies, payload, cwd=directory)
        relative.unlink()
        files.append(directory / f"{package}-{version}.x86_64.xbps")
    run("xbps-rindex", "-a", *files)
    run("xbps-rindex", "--privkey", key, "--sign", "--signedby", "Skwd channel TEST ONLY", directory)
    run("xbps-rindex", "--privkey", key, "--sign-pkg", *files)
    if invalid_sig:
        sig = directory / (files[1].name + ".sig2")
        sig.write_bytes(b"intentional invalid signature\n")
    manifest = directory / "SHA256SUMS"
    assets = sorted([*files, *(directory.glob("*.sig2")), directory / "x86_64-repodata"])
    manifest.write_text("".join(f"{sha(path)}  {path.name}\n" for path in assets))
    sign(key, manifest, directory / "SHA256SUMS.sig")
    shutil.copyfile(published_key, directory / "xbps-public.pem")
    return sha(manifest)


def channel(case, version, sequence, manifest, key, expired=False):
    now = int(time.time())
    offset = 7200 if expired else 0
    body = json.dumps({"schema": 1, "tag": "xbps-beta" + version.split("beta")[1],
                       "version": version, "sequence": sequence, "issued": now - 60 - offset,
                       "expires": now + 3600 - offset, "manifest_sha256": manifest})
    payload = case / "body"
    payload.write_text(body)
    signature = case / "sig"
    sign(key, payload, signature)
    (case / "channel.json").write_text(json.dumps(
        {"payload": base64.b64encode(payload.read_bytes()).decode(),
         "signature": base64.b64encode(signature.read_bytes()).decode()}))


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        name = self.path
        if name.startswith("/select/"):
            case = name.rsplit("/", 1)[1]
            if case not in self.server.cases:
                self.send_error(404)
                return
            self.server.case = case
            self.send_response(200)
            self.end_headers()
            return
        case = self.server.case
        if case == "unavailable":
            self.send_error(503)
            return
        if name == "/stable/channel.json":
            self.path = f"/{case}/channel.json"
        elif name.startswith("/releases/"):
            file = name.rsplit("/", 1)[1]
            if case == "interrupted" and file.endswith(".xbps"):
                self.send_response(200)
                self.send_header("Content-Length", "40000")
                self.end_headers()
                self.wfile.write(b"incomplete")
                self.close_connection = True
                return
            self.path = f"/{case}/{file}"
        super().do_GET()


def build_fixture(work, media, origin):
    key = work / "test-key.pem"
    pub = work / "test-public.pem"
    run("openssl", "genrsa", "-out", key, "2048")
    run("openssl", "pkey", "-in", key, "-pubout", "-out", pub)
    web = work / "web"
    payload = work / "payload"
    for index, label in enumerate(("initial", "update")):
        case = web / label
        manifest = make_release(case, payload, key, REV[index], pub)
        channel(case, REV[index], index + 1, manifest, key)
    cases = {"initial", "update", "unavailable"}
    index = web / "update"
    for label in ("interrupted", "bad-index", "bad-signature", "expired", "bad-key",
                  "newer-sequence-older-version"):
        cases.add(label)
        version = REV[0] if label == "newer-sequence-older-version" else REV[1]
        case = web / label
        if label == "bad-signature":
            manifest = make_release(case, payload, key, version, pub, invalid_sig=True)
        else:
            shutil.copytree(web / "initial" if version == REV[0] else index, case)
            manifest = sha(case / "SHA256SUMS")
        channel(case, version, 3 if version == REV[0] else 2, manifest, key, label == "expired")
        if label == "bad-index":
            with (case / "x86_64-repodata").open("ab") as stream:
                stream.write(b"unexpected trailing data")
        if label == "bad-key":
            other = work / "other-test-key.pem"
            run("openssl", "genrsa", "-out", other, "2048")
            run("openssl", "pkey", "-in", other, "-pubout", "-out", case / "xbps-public.pem")
    metadata = run("xbps-query", "-i", "-v", "-R", "--repository", web / "initial", "-L")
    fingerprint = re.search(rb"(?:[0-9a-f]{2}:){15}[0-9a-f]{2}", metadata)[0].decode()
    spki = hashlib.sha256(run("openssl", "pkey", "-pubin", "-in", pub, "-outform", "DER")).hexdigest()
    replacements = {
        "CHANNEL": f"{origin}/stable/channel.json", "RELEASES": f"{origin}/releases",
        "SPKI": spki, "FINGERPRINT": fingerprint,
    }
    script = (REPO / "scripts/sync-channel.py").read_text()
    for name, value in replacements.items():
        script, count = re.subn(rf'^{name} = ".*"$', f'{name} = "{value}"', script, flags=re.M)
        assert count == 1
    script = script.replace("/var/lib/skwd-xbps", "/var/lib/skwd-xbps-lab")
    script = script.replace("/etc/xbps.d/30-skwd-void.conf", "/run/skwd-channel-lab-conf/skwd.conf")
    (media / "test-sync-channel.py").write_text(script)
    (media / "xbps-fingerprint").write_text(fingerprint + "\n")
    return web, cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path, help="known Void guest base qcow2")
    parser.add_argument("--console", required=True, type=Path, help="existing guest serial login helper")
    parser.add_argument("--output", type=Path, help="parent directory for the new test artifacts")
    args = parser.parse_args()
    os.umask(0o077)
    work = Path(tempfile.mkdtemp(prefix="skwd-xbps-channel.", dir=args.output))
    print(work, flush=True)
    media = work / "media"
    media.mkdir()
    tls_key = work / "tls-key.pem"
    run("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
        "-subj", "/CN=Skwd channel VM TEST ONLY", "-addext", "subjectAltName=DNS:repo.skwd.test",
        "-keyout", tls_key, "-out", media / "tls-cert.pem", stderr=subprocess.DEVNULL)
    shutil.copyfile(REPO / "tests/channel-vm-guest.sh", media / "guest.sh")
    run("qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", args.base.resolve(), work / "guest.qcow2")
    (work / "logs").mkdir()
    console = work / "console.py"
    shutil.copyfile(args.console, console)
    with ThreadingHTTPServer(("127.0.0.1", 0),
                             functools.partial(Handler, directory=work / "web")) as server:
        origin = f"https://repo.skwd.test:{server.server_port}"
        (media / "origin").write_text(origin + "\n")
        _, server.cases = build_fixture(work, media, origin)
        run("mkisofs", "-quiet", "-J", "-R", "-o", work / "bootstrap.iso", media)
        server.case = "initial"
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(media / "tls-cert.pem", tls_key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        serial = work / "serial"
        env = dict(os.environ, SKWD_VM_SERIAL=str(serial))
        with (work / "qemu.log").open("w") as log:
            qemu = subprocess.Popen(["qemu-system-x86_64", "-machine", "q35,vmport=off",
                "-accel", "tcg,thread=multi", "-cpu", "max", "-smp", "2", "-m", "2048",
                "-nodefaults", "-no-user-config", "-display", "none", "-monitor", "none",
                "-netdev", "user,id=lab",
                "-device", "virtio-net-pci,netdev=lab",
                "-drive", f"file={work / 'guest.qcow2'},format=qcow2,if=none,id=osdisk",
                "-device", "virtio-blk-pci,drive=osdisk,serial=skwd-channel-lab",
                "-drive", f"file={work / 'bootstrap.iso'},format=raw,media=cdrom,readonly=on",
                "-serial", f"unix:{serial},server=on,wait=off",
                "-sandbox", "on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny"],
                stdout=log, stderr=log)
            try:
                for _ in range(100):
                    if serial.is_socket():
                        break
                    if qemu.poll() is not None:
                        raise RuntimeError("QEMU exited at startup")
                    time.sleep(0.1)
                command = ('set -x; test "$(cat /sys/block/vda/serial)" = skwd-channel-lab && '
                           'mkdir -p /mnt/channel-lab && mount -o ro /dev/sr0 /mnt/channel-lab && '
                           'bash /mnt/channel-lab/guest.sh /mnt/channel-lab')
                with (work / "guest.log").open("w") as guest_log:
                    result = subprocess.run(["python3", "-u", str(console), "run", command, "360"],
                                            env=env, stdout=guest_log, stderr=subprocess.STDOUT)
                (work / "guest.exit").write_text(f"{result.returncode}\n")
                raise SystemExit(result.returncode)
            finally:
                qemu.terminate()
                qemu.wait(timeout=15)


if __name__ == "__main__":
    main()
