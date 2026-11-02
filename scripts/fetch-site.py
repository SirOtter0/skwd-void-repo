#!/usr/bin/env python3
"""Download an owner-approved site bundle, verify every channel, never install."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.parse
import urllib.request
import repository

LIMIT = 900_000_000


class HTTPSOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != 'https':
            raise ValueError('Non-HTTPS redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def unpack(bundle, output):
    output.mkdir(mode=0o700, exist_ok=False)
    total = 0
    seen = set()
    with tarfile.open(bundle, 'r|gz') as archive:
        for member in archive:
            name = member.name.removeprefix('./').rstrip('/')
            if not name:
                continue
            path = Path(name)
            if path.is_absolute() or '..' in path.parts or name in seen or len(seen) >= 100:
                raise ValueError('Unsafe/oversized site member list')
            seen.add(name)
            if path.parts[0] not in ('testing', 'stable') or len(path.parts) > 2:
                raise ValueError('Unexpected site layout')
            if member.isdir():
                (output / path).mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile() or member.size < 0:
                raise ValueError('Only regular files/directories allowed')
            total += member.size
            if total > LIMIT:
                raise ValueError('Site exceeds conservative Pages size limit')
            target = output / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as dst:
                shutil.copyfileobj(archive.extractfile(member), dst, length=1024*1024)
            target.chmod(0o644)


def verify_site(site, policy):
    if not policy['distribution_approved']:
        raise ValueError('Publication not approved')
    testing = site / 'testing'
    repository.verify(testing, policy['signing']['public_key_spki_sha256'])
    repository.gate(policy, testing / 'candidate.json')
    stable = site / 'stable'
    if policy['hosting']['stable_url'] and not stable.is_dir():
        raise ValueError('Would remove the existing stable channel')
    if stable.exists():
        repository.verify(stable, policy['signing']['public_key_spki_sha256'])
        approved = policy.get('stable_approved_candidate_sha256')
        if not approved or repository.digest(stable / 'candidate.json') != approved:
            raise ValueError('Stable channel has not been explicitly approved')
    for channel in (testing, stable):
        if not channel.exists():
            continue
        manifest = repository.load(channel / 'release.json')
        expected = set(manifest['files']) | {'release.json', 'release.json.sig'}
        if {p.name for p in channel.iterdir()} != expected:
            raise ValueError('Unexpected channel files')
    (site / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Skwd Void community packages</title><h1>Unofficial Skwd packages for Void x86_64 glibc</h1><p>Independent of official Void and Skwd releases.</p><p>This software uses FFmpeg under LGPLv2.1-or-later; exact corresponding sources and license notices accompany each signed channel.</p><p><a href="testing/corresponding-source.tar.xz">Testing corresponding sources</a> · <a href="testing/release.json">Signed release metadata</a></p>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url'); parser.add_argument('expected_sha256'); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    parsed = urllib.parse.urlsplit(args.url)
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('Public HTTPS URL without credentials required')
    if not repository.re.fullmatch('[0-9a-f]{64}', args.expected_sha256):
        raise ValueError('Invalid owner-reviewed bundle digest')
    policy = repository.load(repository.ROOT / 'policy/release.json')
    if not policy['distribution_approved']:
        raise ValueError('Publication disabled by policy')
    with tempfile.TemporaryDirectory(prefix='skwd-reviewed-site-') as temp:
        bundle = Path(temp) / 'site.tar.gz'; count = 0
        opener = urllib.request.build_opener(HTTPSOnly())
        with opener.open(args.url, timeout=60) as src, bundle.open('xb') as dst:
            while data := src.read(1024*1024):
                count += len(data)
                if count > LIMIT:
                    raise ValueError('Download exceeds limit')
                dst.write(data)
        if repository.digest(bundle) != args.expected_sha256:
            raise ValueError('Site bundle digest mismatch')
        unpack(bundle, args.output)
    verify_site(args.output, policy)


if __name__ == '__main__':
    main()
