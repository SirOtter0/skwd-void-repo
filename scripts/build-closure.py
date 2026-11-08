#!/usr/bin/env python3
"""Recover actual Cargo runtime/build-only sets from retained successful fingerprints."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tomllib


def collect(build_root):
    result = {'method': 'Retained successful Cargo fingerprints, dependency fingerprint hashes and dep-info paths; runtime set is conservative (LTO may remove unused code). Proc macros/build scripts are excluded from runtime traversal.', 'components': {}}
    for component in ('wall', 'deck', 'lens', 'paper'):
        build = build_root / component
        suite = build / 'suite'
        target = build / ('target/private-ffmpeg/release' if component in ('deck', 'paper') else 'target/host/release')
        source_map = {}
        for path in (suite / 'vendor').glob('*/Cargo.toml'):
            data = tomllib.loads(path.read_text());package = data.get('package', {})
            source_map[path.parent.name] = {'name': package['name'], 'version': package['version'], 'vendor': path.parent.name, 'proc_macro': data.get('lib', {}).get('proc-macro', False)}
        records = []
        for path in sorted((target / '.fingerprint').glob('*/*.json')):
            if not path.name.startswith(('lib-', 'bin-')):
                continue
            kind, name = path.stem.split('-', 1)
            fingerprint = path.with_suffix('')
            if not fingerprint.is_file():
                continue
            metadata = json.loads(path.read_text())
            hash_value = int.from_bytes(bytes.fromhex(fingerprint.read_text().strip()), 'little')
            suffix = path.parent.name.rsplit('-', 1)[1]
            depfile = target / 'deps' / (name.replace('-', '_') + '-' + suffix + '.d')
            dependencies = depfile.read_text() if depfile.is_file() else ''
            vendors = set(re.findall(r'/work/suite/vendor/([^/\s]+)/', dependencies))
            # Only the crate's direct dep-info sources, not all recursively linked source.
            if len(vendors) > 1:
                raise ValueError('Ambiguous crate dep-info: ' + name)
            package = source_map[next(iter(vendors))] if vendors else {'name': name.replace('_', '-'), 'version': 'workspace', 'vendor': None, 'proc_macro': False}
            records.append({'name': name.replace('-', '_'), 'kind': kind, 'hash': hash_value, 'package': package, 'deps': metadata['deps'], 'features': metadata['features']})
        mapping = {}
        for record in records:
            mapping.setdefault((record['name'], record['hash']), []).append(record)
        roots = [r for r in records if r['kind'] == 'bin']
        expected = {'wall': 1, 'deck': 4, 'lens': 1, 'paper': 4}[component]
        if len(roots) != expected:
            raise ValueError('Unexpected binary roots for ' + component + ': ' + str([r['name'] for r in roots]))
        runtime = {}; macros = {}; visited = set(); edges = []
        def visit(record):
            key = (record['name'], record['hash'])
            if key in visited:
                return
            visited.add(key)
            package = record['package']
            if package['proc_macro']:
                if package['vendor']:macros[package['vendor']] = package
                return
            if package['vendor']:
                runtime[package['vendor']] = package
            for _, name, _, fingerprint in record['deps']:
                if name.startswith('build_script_'):
                    continue
                matches = mapping.get((name, fingerprint), [])
                if not matches:
                    matches = [r for r in records if r['kind'] == 'lib' and r['hash'] == fingerprint]
                if len(matches) != 1:
                    raise ValueError('Cannot uniquely resolve linked dependency: ' + component + ':' + name + ':' + str(fingerprint))
                child = matches[0]
                edges.append([record['name'], child['name']])
                visit(child)
        for root in roots:visit(root)
        built = {r['package']['vendor']:r['package'] for r in records if r['package']['vendor']}
        build_only = {k:v for k,v in built.items() if k not in runtime}
        result['components'][component] = {'binaries': sorted(r['name'] for r in roots), 'runtime_registry_packages': sorted(runtime), 'build_only_or_proc_macro_packages': sorted(build_only), 'proc_macros_reached': sorted(macros), 'linked_edges': sorted(set(tuple(e) for e in edges)), 'compiled_package_details': built}
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('build_root',type=Path);parser.add_argument('output',type=Path);a=parser.parse_args()
    if a.output.exists():raise SystemExit('Output must be new')
    a.output.write_text(json.dumps(collect(a.build_root),indent=2)+'\n')
