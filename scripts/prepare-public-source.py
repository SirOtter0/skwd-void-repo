#!/usr/bin/env python3
"""Create source delivery without optional Steam SDK payload or private build state."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import os
import repository

ROOT=Path(__file__).resolve().parents[1]


def sdk_plan(suite, closure):
    used={name for item in closure['components'].values() for name in item['runtime_registry_packages']+item['build_only_or_proc_macro_packages']}
    if any(name.startswith(('steamworks-','steamworks-sys-')) for name in used):
        raise ValueError('Core build unexpectedly uses Steam SDK wrapper; exclusions cannot be assumed safe')
    excluded=[];observed=[]
    for directory in sorted((suite/'vendor').glob('steamworks-sys-*')):
        files=sorted(p for p in (directory/'lib').rglob('*') if p.is_file()) if (directory/'lib').exists() else []
        observed.append({'crate':directory.name,'sdk_lib_file_count':len(files),'needed_by_four_components':False,'wrapper_rust_sources_retained':True})
        for path in files:
            if path.is_symlink():raise ValueError('Unexpected SDK symlink')
            excluded.append({'path':str(path.relative_to(suite)),'sha256':repository.digest(path),'reason':'Optional third-party SDK/runtime; wrapper license is not a redistribution grant; not used by four core packages'})
    return {'observations':observed,'excluded_files':excluded,'note':'An empty SDK directory is not evidence that a proprietary runtime is shipped. Original coordinated suite already omits native SDK files; preserve Rust wrapper/manifests for unchanged Cargo resolution.'}


def is_build_state(path, root):
    if path.name in ('.git', '.skwd-package', 'node_modules'):
        return True
    return path.name == 'target' and (path.parent == root or (path.parent / 'Cargo.toml').is_file())


def prepare(args):
    if os.geteuid()==0:raise ValueError('Prepare sources as normal user')
    if any(p.is_symlink() for p in args.suite.rglob('*')):raise ValueError('Unexpected input symlink')
    inputs=repository.load(args.suite.parent/'sources.json')
    for component,expected in inputs['locks'].items():
        if repository.digest(args.suite/('skwd-'+component)/'Cargo.lock')!=expected:raise ValueError('Lockfile changed')
    plan=sdk_plan(args.suite,repository.load(args.closure))
    args.output.mkdir(mode=0o700,exist_ok=False)
    destination=args.output/'suite';shutil.copytree(args.suite,destination)
    for item in plan['excluded_files']:
        target=destination/item['path'];target.unlink()
        directory=next(parent for parent in target.parents if parent.name.startswith('steamworks-sys-'))
        checksums=directory/'.cargo-checksum.json';data=repository.load(checksums)
        data['files'].pop(str(target.relative_to(directory)),None);repository.write(checksums,data)
    for bad in destination.rglob('*'):
        if bad.is_dir() and is_build_state(bad, destination):
            raise ValueError('Build/private state in source input: '+str(bad.relative_to(destination)))
    port_archive=args.port_recipes
    if not port_archive.is_file() or port_archive.is_symlink():raise ValueError('Verified public port recipe archive required')
    port_destination=args.output/'port-recipes';port_destination.mkdir()
    with tarfile.open(port_archive) as archive:
        entries=repository.members(archive)
        for name in entries:
            if name!='LICENSE' and name not in ('packaging','security') and not name.startswith(('packaging/void','security/void-beta26')):
                raise ValueError('Unexpected public port recipe path')
        archive.extractall(port_destination,filter='data')
    repository.write(args.output/'PORT-RECIPES.json',{'repository':'https://github.com/SirOtter0/skwd-wall','commit':'466e95c608b37000491633bdbec6ca801a059714','archive_sha256':repository.digest(port_archive),'included':['LICENSE','packaging/void','security/void-beta26']})
    (args.output/'REBUILD.md').write_text('Extract this archive in a clean Void x86_64 glibc builder with the documented prerequisite packages.\nThe exact patched/vendor sources are suite/. The validated public build and original packaging recipes are port-recipes/packaging/void/.\nUse build.sh on suite/ with a new per-component output; its locks and source checks read adjacent sources.json.\nCompile wall, deck, lens and paper offline; package with the original recipe, then apply infrastructure/scripts/build-closure.py and repack-notices.py for coordinated legal revision4.\nThe infrastructure/legal and review/ notice manifests are included; the repacker adds notices and requires unchanged ELF bytes.\nRepack an existing recorded build with the strict default hashes, or pass --build-inventory to consume the new original packager inventory in a fresh controlled build.\nSee infrastructure/docs/BUILD.md. Do not run build scripts as root. No personal cache or signing key is needed.\n')
    shutil.copyfile(args.suite.parent/'sources.json',args.output/'sources.json')
    repository.write(args.output/'SDK-EXCLUSIONS.json',plan)
    # Only Git-indexed public infrastructure; never work/, VM artifacts or key directories.
    infrastructure=args.output/'infrastructure';infrastructure.mkdir()
    snapshot=ROOT/'PUBLIC-SNAPSHOT.json'
    if snapshot.is_file():
        data=repository.load(snapshot);paths=list(data['files'])
        for name,expected in data['files'].items():
            if repository.digest(ROOT/name)!=expected:raise ValueError('Public infrastructure snapshot changed')
        origin=data['git_tree']
    else:
        paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0');origin=subprocess.check_output(['git','write-tree'],cwd=ROOT,text=True).strip()
    for name in paths:
        if not name:continue
        path=ROOT/name
        if path.is_symlink() or not path.is_file():raise ValueError('Unsafe public infrastructure path')
        if path.suffix in ('.pem','.key','.p12','.pfx','.xbps','.qcow2'):raise ValueError('Private/binary artifact in public index')
        target=infrastructure/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    source_files={str(p.relative_to(args.output)):repository.digest(p) for p in sorted(args.output.rglob('*')) if p.is_file()}
    repository.write(args.output/'SOURCE-FILES.json',{'sha256':source_files,'inputs':inputs,'infrastructure_git_tree':origin,'scope':'Exact indexed public infrastructure snapshot and corresponding source; no key/build cache included'})
    archive=args.output.with_suffix('.tar.xz')
    if archive.exists():raise ValueError('Archive must be new')
    subprocess.run(['tar','--sort=name','--mtime=@1792079636','--owner=0','--group=0','--numeric-owner','-cJf',str(archive),'-C',str(args.output),'.'],env=dict(os.environ,XZ_OPT='-0'),check=True)
    repository.write(args.output.parent/(args.output.name+'-receipt.json'),{'archive':archive.name,'sha256':repository.digest(archive),'sdk_review':plan,'source_file_count':len(source_files),'source_lockfiles_unchanged':True})
    print(archive.name,repository.digest(archive),'files',len(source_files),'SDK exclusions',len(plan['excluded_files']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('suite',type=Path);p.add_argument('closure',type=Path);p.add_argument('output',type=Path);p.add_argument('--port-recipes',type=Path,required=True);args=p.parse_args();prepare(args)
