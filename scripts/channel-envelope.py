#!/usr/bin/env python3
"""Prepare stable metadata for offline signing and package a verified signature."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from runpy import run_path


def write(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    steps = parser.add_subparsers(dest="step", required=True)
    prepare = steps.add_parser("prepare")
    prepare.add_argument("version")
    prepare.add_argument("sequence", type=int)
    prepare.add_argument("manifest", type=Path)
    prepare.add_argument("output", type=Path)
    pack = steps.add_parser("pack")
    pack.add_argument("payload", type=Path)
    pack.add_argument("signature", type=Path)
    pack.add_argument("public_key", type=Path)
    pack.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.step == "prepare":
            version = re.fullmatch(r"1\.0\.0beta([0-9]+)_([1-9][0-9]*)", args.version)
            if not version or args.sequence < 1:
                parser.error("expected a beta package version and positive sequence")
            now = int(time.time())
            write(args.output, {
                "schema": 1, "sequence": args.sequence, "version": args.version,
                "tag": "xbps-beta" + "_".join(version.groups()),
                "issued": now, "expires": now + 60 * 86400,
                "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
            })
        else:
            der = subprocess.check_output(
                ["openssl", "pkey", "-pubin", "-in", args.public_key, "-outform", "DER"])
            if hashlib.sha256(der).hexdigest() != run_path(str(Path(__file__).with_name("sync-channel.py")))["SPKI"]:
                parser.error("expected the existing production public key")
            subprocess.run(["openssl", "dgst", "-sha256", "-verify", args.public_key,
                            "-signature", args.signature, args.payload], check=True)
            write(args.output, {
                "payload": base64.b64encode(args.payload.read_bytes()).decode("ascii"),
                "signature": base64.b64encode(args.signature.read_bytes()).decode("ascii"),
            })
    except (OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Channel envelope: {error}\n")


if __name__ == "__main__":
    main()
