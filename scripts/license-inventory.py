#!/usr/bin/env python3
"""Conservative lockfile inventory for review; not a legal clearance or build graph."""
import argparse
import hashlib
import json
from pathlib import Path
import tomllib


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(suite):
    vendor = {}
    for path in sorted((suite / 'vendor').glob('*/Cargo.toml')):
        if path.is_symlink():
            raise ValueError('Unexpected manifest symlink')
        package = tomllib.loads(path.read_text()).get('package', {})
        vendor[(package.get('name'), package.get('version'))] = (path.parent, package)
    result = {'scope': 'Registry packages in four lockfiles; includes optional/build/platform-only entries. Assets and native subcomponents require manual review.', 'cleared_for_distribution': False, 'components': {}}
    for component in ('wall', 'deck', 'lens', 'paper'):
        source = suite / ('skwd-' + component)
        lock = source / 'Cargo.lock'
        rows = []
        for package in tomllib.loads(lock.read_text())['package']:
            if not package.get('source', '').startswith('registry+'):
                continue
            directory, info = vendor.get((package['name'], package['version']), (None, {}))
            if directory is None:
                raise ValueError('Locked source missing: ' + package['name'] + '-' + package['version'])
            notices = []
            for path in sorted(directory.rglob('*')):
                name = path.name.upper()
                if path.is_file() and name.startswith(('LICENSE', 'LICENCE', 'COPYING', 'COPYRIGHT', 'NOTICE', 'AUTHORS')):
                    if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
                        raise ValueError('Unexpected notice symlink')
                    notices.append({'path': str(path.relative_to(directory)), 'sha256': sha(path)})
            rows.append({'name': package['name'], 'version': package['version'], 'source': package['source'],
                         'lock_checksum': package.get('checksum'), 'license_expression': info.get('license'),
                         'license_file': info.get('license-file'), 'notice_files': notices})
        result['components'][component] = {'project_license': 'MIT', 'project_license_sha256': sha(source / 'LICENSE'),
                                           'lock_sha256': sha(lock), 'packages': rows}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Output must be new')
    args.output.write_text(json.dumps(inventory(args.suite), indent=2) + '\n')
