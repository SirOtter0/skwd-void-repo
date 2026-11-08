#!/usr/bin/env python3
"""Inspect packages; prepare local candidates; sign/verify only after explicit approval."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def members(archive):
    """Read without extracting or executing; reject ambiguous archive paths."""
    result = {}
    for member in archive.getmembers():
        name = member.name.removeprefix('./')
        if name in ('', '.'):
            continue
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or name in result:
            raise ValueError('Unsafe/duplicate archive member')
        if not (member.isfile() or member.isdir() or member.issym()):
            raise ValueError('Unsupported archive entry')
        if member.mode & (stat.S_ISUID | stat.S_ISGID):
            raise ValueError('Privileged archive entry')
        if member.issym():
            target = Path(member.linkname)
            if target.is_absolute() or '..' in target.parts:
                raise ValueError('Unexpected symlink target')
        result[name] = member
    return result


def inspect(path, policy):
    if Path(path).is_symlink() or not Path(path).is_file():
        raise ValueError('Package must be a regular file')
    with tarfile.open(path, 'r:*') as archive:
        entries = members(archive)
        props = plistlib.loads(archive.extractfile(entries['props.plist']).read())
        if props['architecture'] != 'x86_64' or props['pkgname'] not in policy['packages']:
            raise ValueError('Unexpected package/architecture')
        if props['pkgver'] != props['pkgname'] + '-' + policy['package_version']:
            raise ValueError('Unexpected package version')
        expected = props['pkgver'] + '.x86_64.xbps'
        if Path(path).name != expected:
            raise ValueError('Package filename does not match properties')
        for name in entries:
            if name in ('props.plist', 'files.plist', 'usr'):
                continue
            if not name.startswith('usr/') or any(part in name.split('/') for part in ('systemd', 'autostart', 'runit')):
                raise ValueError('Unexpected persistent payload: ' + name)
        deps = props.get('run_depends', [])
        if any(re.match(r'systemd(?:[-<>=]|$)', dep) for dep in deps):
            raise ValueError('Unexpected systemd dependency')
        return {'file': expected, 'name': props['pkgname'], 'version': props['pkgver'],
                'sha256': digest(path), 'bytes': Path(path).stat().st_size,
                'dependencies': sorted(deps), 'license': props.get('license'),
                'archive_entries': len(entries)}


def check_candidates(directory, policy):
    rows = [inspect(path, policy) for path in sorted(Path(directory).glob('*.xbps'))]
    if len(rows) != 4 or {row['name'] for row in rows} != set(policy['packages']):
        raise ValueError('Expected exactly the four coordinated packages')
    return rows


def source_inputs(path):
    data = load(path)
    # Deliberately do not forward private build paths or arbitrary manifest fields.
    return {key: data[key] for key in ('original_archive_sha256', 'commits', 'locks', 'patches', 'ffmpeg')}


def stage(args, policy):
    source = args.source_bundle
    if source.is_symlink() or not source.is_file():
        raise ValueError('Source bundle must be a regular file')
    rows = check_candidates(args.packages, policy)
    output = args.output.resolve()
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    for row in rows:
        shutil.copyfile(args.packages / row['file'], output / row['file'])
    shutil.copyfile(source, output / 'corresponding-source.tar.xz')
    subprocess.run(['xbps-rindex', '-a', *[str(output / row['file']) for row in rows]], check=True)
    candidate = {'schema': 1, 'architecture': 'x86_64', 'libc': 'glibc',
                 'port_commit': policy['port_commit'], 'packages': rows,
                 'source_bundle': {'file': 'corresponding-source.tar.xz', 'sha256': digest(source)},
                 'source_inputs': source_inputs(args.sources_manifest),
                 'build_environment': load(args.build_environment) if args.build_environment else None,
                 'distribution_status': 'unsigned-local-review-only'}
    write(output / 'candidate.json', candidate)
    print('Local unsigned candidate SHA256:', digest(output / 'candidate.json'))


def gate(policy, candidate_path):
    review = policy['license_review']
    if not (policy['distribution_approved'] and review['approved'] and review['reviewer'] and review['evidence']):
        raise ValueError('Distribution/license approval not granted')
    if review['approved_candidate_sha256'] != digest(candidate_path):
        raise ValueError('License review does not approve this exact candidate')
    if review['blockers']:
        raise ValueError('Unresolved distribution blockers')
    if not re.fullmatch('[0-9a-f]{64}', policy['signing']['public_key_spki_sha256'] or ''):
        raise ValueError('Approved signing identity not configured')


def rsa_ssh_blob(der):
    """Encode OpenSSL-validated PKCS#1 public integers as RFC4251 ssh-rsa."""
    def tlv(data, position, expected):
        if position + 2 > len(data) or data[position] != expected:
            raise ValueError('Invalid public DER tag')
        size = data[position + 1]; position += 2
        if size & 0x80:
            count = size & 0x7f
            if count == 0 or count > 4 or position + count > len(data):
                raise ValueError('Invalid public DER length')
            size = int.from_bytes(data[position:position+count], 'big'); position += count
        if position + size > len(data):raise ValueError('Truncated public DER')
        return data[position:position+size], position+size
    sequence, end = tlv(der, 0, 0x30)
    if end != len(der):raise ValueError('Extra public DER data')
    modulus, position = tlv(sequence, 0, 2)
    exponent, end = tlv(sequence, position, 2)
    if end != len(sequence) or not modulus or not exponent or modulus[0]&0x80 or exponent[0]&0x80:
        raise ValueError('Invalid RSA public integers')
    def string(value):return len(value).to_bytes(4, 'big')+value
    return string(b'ssh-rsa')+string(exponent)+string(modulus)


def public_identity(public):
    der = subprocess.check_output(['openssl', 'pkey', '-pubin', '-in', str(public), '-outform', 'DER'])
    rsa = subprocess.check_output(['openssl', 'rsa', '-pubin', '-in', str(public), '-RSAPublicKey_out', '-outform', 'DER'], stderr=subprocess.PIPE)
    fingerprint = hashlib.md5(rsa_ssh_blob(rsa), usedforsecurity=False).digest()
    return {'spki_sha256': hashlib.sha256(der).hexdigest(),
            'xbps_md5_fingerprint': ':'.join(f'{byte:02x}' for byte in fingerprint)}


def verify(directory, expected_key):
    directory = Path(directory)
    public = directory / 'public.pem'
    if public_identity(public)['spki_sha256'] != expected_key:
        raise ValueError('Public key does not match independently trusted identity')
    subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(public), '-signature',
                    str(directory / 'release.json.sig'), str(directory / 'release.json')], check=True)
    manifest = load(directory / 'release.json')
    for name, expected in manifest['files'].items():
        if Path(name).name != name or name in ('.', '..'):
            raise ValueError('Unsafe signed manifest filename')
        path = directory / name
        if path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise ValueError('Signed artifact hash mismatch: ' + name)
    if len(manifest['packages']) != 4:
        raise ValueError('Expected four signed packages')
    for row in manifest['packages']:
        name = row['file']
        if Path(name).name != name or not name.endswith('.x86_64.xbps'):
            raise ValueError('Invalid signed package filename')
        if manifest['files'].get(name) != row['sha256'] or name + '.sig2' not in manifest['files']:
            raise ValueError('Package missing from signed manifest')
        subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(public), '-signature',
                        str(directory / (name + '.sig2')), str(directory / name)], check=True)
    with tarfile.open(directory / 'x86_64-repodata') as archive:
        entries = members(archive)
        meta = plistlib.loads(archive.extractfile(entries['index-meta.plist']).read())
        index = plistlib.loads(archive.extractfile(entries['index.plist']).read())
        if meta['public-key'] != public.read_bytes():
            raise ValueError('XBPS repository key mismatch')
        if set(index) != {row['name'] for row in manifest['packages']}:
            raise ValueError('Repository package set mismatch')
        for row in manifest['packages']:
            item = index[row['name']]
            if item['pkgver'] != row['version'] or item['filename-sha256'] != row['sha256']:
                raise ValueError('Repository metadata disagrees with signed package')
    return manifest


def sign(args, policy):
    if os.geteuid() == 0 or not args.approve_signing or not sys.stdin.isatty() or os.environ.get('CI'):
        raise ValueError('Interactive, explicitly approved offline signing required')
    directory = args.directory.resolve()
    gate(policy, directory / 'candidate.json')
    key = args.private_key
    info = key.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Private key must be an owned regular file with private permissions')
    parent = key.parent.lstat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid() or parent.st_mode & 0o077:
        raise ValueError('Signing key directory must be owned and private')
    if key.resolve().is_relative_to(ROOT) or key.resolve().is_relative_to(directory):
        raise ValueError('Private key must be outside repository and candidate trees')
    if (directory / 'release.json').exists():
        raise ValueError('Refusing to overwrite an existing signed release')
    public = directory / 'public.pem'
    with public.open('wb') as stream:
        subprocess.run(['openssl', 'pkey', '-in', str(key), '-pubout'], stdout=stream, check=True)
    identity = public_identity(public)
    if identity['spki_sha256'] != policy['signing']['public_key_spki_sha256']:
        raise ValueError('Private key does not match approved public identity')
    if identity['xbps_md5_fingerprint'] != policy['signing']['xbps_md5_fingerprint']:
        raise ValueError('XBPS fingerprint mismatch')
    candidate = load(directory / 'candidate.json')
    rows = check_candidates(directory, policy)
    if rows != candidate['packages'] or digest(directory / candidate['source_bundle']['file']) != candidate['source_bundle']['sha256']:
        raise ValueError('Candidate inputs changed after review')
    for row in rows:
        subprocess.run(['xbps-rindex', '--privkey', str(key), '--sign-pkg', str(directory / row['file'])], check=True)
    subprocess.run(['xbps-rindex', '--privkey', str(key), '--sign', '--signedby',
                    policy['signing']['identity'], str(directory)], check=True)
    write(directory / 'fingerprints.json', identity)
    allowed = {row['file'] for row in rows} | {row['file'] + '.sig2' for row in rows}
    allowed |= {'public.pem', 'fingerprints.json', 'candidate.json', 'corresponding-source.tar.xz', 'x86_64-repodata'}
    files = [directory / name for name in sorted(allowed)]
    if any(not p.is_file() or p.is_symlink() for p in files):
        raise ValueError('Missing or symlinked release file')
    if any(p.name not in allowed and not p.name.endswith('-lock') for p in directory.iterdir()):
        raise ValueError('Unexpected files in signing directory; refusing publication')
    manifest = dict(candidate, distribution_status='signed-release', key=identity,
                    files={p.name: digest(p) for p in sorted(files)})
    write(directory / 'release.json', manifest)
    subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(key), '-out',
                    str(directory / 'release.json.sig'), str(directory / 'release.json')], check=True)
    verify(directory, identity['spki_sha256'])


def promote(args, policy):
    manifest = verify(args.directory, policy['signing']['public_key_spki_sha256'])
    gate(policy, args.directory / 'candidate.json')
    if args.channel == 'stable' and not args.accept_tested_release:
        raise ValueError('Stable promotion requires explicit validation approval')
    output = args.output.resolve()
    output.mkdir(mode=0o755, parents=False, exist_ok=False)
    for name in [*manifest['files'], 'release.json', 'release.json.sig']:
        shutil.copyfile(args.directory / name, output / name)
    verify(output, policy['signing']['public_key_spki_sha256'])
    print('Prepared local', args.channel, 'tree; no network publication performed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, default=ROOT / 'policy/release.json')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('inspect'); p.add_argument('packages', type=Path)
    p = sub.add_parser('stage'); p.add_argument('packages', type=Path); p.add_argument('source_bundle', type=Path); p.add_argument('sources_manifest', type=Path); p.add_argument('output', type=Path); p.add_argument('--build-environment', type=Path)
    p = sub.add_parser('identity'); p.add_argument('public_key', type=Path)
    p = sub.add_parser('sign'); p.add_argument('directory', type=Path); p.add_argument('private_key', type=Path); p.add_argument('--approve-signing', action='store_true')
    p = sub.add_parser('verify'); p.add_argument('directory', type=Path); p.add_argument('--expected-key-sha256', required=True)
    p = sub.add_parser('promote'); p.add_argument('directory', type=Path); p.add_argument('output', type=Path); p.add_argument('--channel', choices=['testing', 'stable'], required=True); p.add_argument('--accept-tested-release', action='store_true')
    args = parser.parse_args(); policy = load(args.policy)
    if args.command == 'inspect': print(json.dumps(check_candidates(args.packages, policy), indent=2))
    elif args.command == 'stage': stage(args, policy)
    elif args.command == 'identity': print(json.dumps(public_identity(args.public_key), indent=2))
    elif args.command == 'sign': sign(args, policy)
    elif args.command == 'verify': verify(args.directory, args.expected_key_sha256)
    elif args.command == 'promote': promote(args, policy)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
