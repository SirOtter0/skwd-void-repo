#!/usr/bin/env python3
"""Repackage verified revision3 ELF bytes as coordinated revision4 with legal notices."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tarfile
import tomllib
import repository

ROOT = Path(__file__).resolve().parents[1]
EPOCH = 1792079636
NAMES = {'wall':'skwd-wall-v2-local','deck':'skwd-deck-local','lens':'skwd-lens-local','paper':'skwd-paper-local'}
PREFIXES = ('LICENSE','LICENCE','COPYING','NOTICE','COPYRIGHT','AUTHORS','ATTRIBUTION')


def copy(source, target):
    if source.is_symlink() or not source.is_file():raise ValueError('Unsafe notice input')
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);target.chmod(0o644)


def hash_elfs(stage):
    result={}
    for path in stage.rglob('*'):
        if not path.is_file() or path.is_symlink():continue
        with path.open('rb') as stream:magic=stream.read(4)
        if magic==b'\x7fELF':result['/'+str(path.relative_to(stage))]=repository.digest(path)
    return result


def repack(args):
    if os.geteuid()==0:raise ValueError('Repackage as an unprivileged user')
    args.output.mkdir(mode=0o700,exist_ok=False);repo=args.output/'repository';repo.mkdir()
    closure=repository.load(args.closure)['components'];manifest=repository.load(ROOT/'review/crate-upstream-notices/manifest.json')
    if args.build_inventory:
        expected={p['name']:{'sha256':p['archive_sha256']} for p in repository.load(args.build_inventory)}
    else:
        expected={p['name']:p for p in repository.load(ROOT/'review/package-inspection.json')}
    asset_manifest=repository.load(ROOT/'review/upstream-notices/manifest.json')
    result=[]
    for component,name in NAMES.items():
        original=args.packages/(name+'-1.0.0beta26_3.x86_64.xbps')
        if repository.digest(original)!=expected[name]['sha256']:raise ValueError('Original build hash mismatch')
        stage=args.output/'stage'/name;stage.mkdir(parents=True)
        with tarfile.open(original) as archive:
            entries=repository.members(archive);props=plistlib.loads(archive.extractfile(entries['props.plist']).read())
            archive.extractall(stage,members=[m for p,m in entries.items() if p=='usr' or p.startswith('usr/')],filter='data')
        before=hash_elfs(stage)
        license_name={'wall':'skwd-wall-v2','deck':'skwd-deck','lens':'skwd-lens','paper':'skwd-paper'}[component]
        notices=stage/'usr/share/licenses'/license_name/'compliance';notices.mkdir(parents=True)
        detail=[];missing=[]
        runtime=set(closure[component]['runtime_registry_packages'])
        compiled=runtime|set(closure[component]['build_only_or_proc_macro_packages'])
        for package in sorted(compiled):
            source=args.suite/'vendor'/package
            cargo=tomllib.loads((source/'Cargo.toml').read_text())['package']
            scope='runtime-conservative' if package in runtime else 'build-tool-or-proc-macro-not-runtime'
            files=[]
            for path in sorted(source.rglob('*')):
                if path.is_file() and path.name.upper().startswith(PREFIXES):
                    destination=notices/'crates'/package/path.relative_to(source);copy(path,destination)
                    files.append({'path':str(destination.relative_to(notices)),'sha256':repository.digest(path)})
            if package in manifest:
                for entry in manifest[package]['notices']:
                    source_notice=ROOT/entry['file']
                    if repository.digest(source_notice)!=entry['sha256']:raise ValueError('Supplemental notice modified')
                    destination=notices/'crates'/package/'upstream-workspace'/entry['path'];copy(source_notice,destination)
                    files.append({'path':str(destination.relative_to(notices)),'sha256':entry['sha256'],'url':entry['url'],'commit':entry['commit']})
            if not files and package in runtime:missing.append(package)
            detail.append({'package':package,'license':cargo.get('license'),'scope':scope,'notices':files})
        if missing:raise ValueError('Runtime notices missing: '+repr(missing))
        repository.write(notices/'DEPENDENCIES.json',detail)
        (notices/'NOTICE.txt').write_text('This community package preserves the original project MIT license and third-party rights.\nDEPENDENCIES.json distinguishes the conservative linked runtime closure from build-only/proc-macro tools.\nPer-crate and nested native license/copyright/NOTICE files are retained without relicensing.\nSee SOURCE-OFFER.txt for the exact corresponding source; see ASSETS.md where fonts/icons are embedded.\nDeck scanner uses the private FFmpeg supplied by Paper; its LGPL/JPEG notices are in /usr/share/licenses/skwd-paper/compliance/.\n')
        for path in args.rust_notices.iterdir():
            if path.is_file() and path.name.upper().startswith(PREFIXES):copy(path,notices/'rust-standard-library'/path.name)
        if component=='wall':
            for entry in asset_manifest:
                if entry['file'].split('/')[2] in ('intel-native','intel-wrapper'):continue
                source_notice=ROOT/entry['file']
                if repository.digest(source_notice)!=entry['sha256']:raise ValueError('Asset notice changed')
                copy(source_notice,notices/'assets'/str(Path(entry['file']).relative_to('review/upstream-notices')))
            for entry in repository.load(ROOT/'review/asset-supplemental-notices/manifest.json'):
                if repository.digest(ROOT/entry['file'])!=entry['sha256']:raise ValueError('Supplemental asset notice changed')
                copy(ROOT/entry['file'],notices/'assets-supplemental'/str(Path(entry['file']).relative_to('review/asset-supplemental-notices')))
            copy(ROOT/'legal/ASSETS.md',notices/'ASSETS.md')
            copy(ROOT/'review/upstream-notices/nerd-font-match.json',notices/'nerd-font-match.json')
        if 'intel_tex_2-0.5.0' in runtime:
            for entry in asset_manifest:
                if '/intel-native/' in entry['file'] or '/intel-wrapper/' in entry['file']:
                    if repository.digest(ROOT/entry['file'])!=entry['sha256']:raise ValueError('Intel notice changed')
                    copy(ROOT/entry['file'],notices/'native-intel'/Path(entry['path']).name)
            copy(ROOT/'legal/INTEL.md',notices/'native-intel/PROVENANCE.md')
        if any(row['license']=='CC0-1.0' for row in detail):copy(ROOT/'legal/CC0-1.0.txt',notices/'CC0-1.0.txt')
        copy(ROOT/'legal/SOURCE-OFFER.txt',notices/'SOURCE-OFFER.txt')
        copy(ROOT/'legal/NATIVE.md',notices/'NATIVE.md')
        if component=='paper':
            copy(ROOT/'legal/FFMPEG.md',notices/'FFMPEG.md')
            copy(ROOT/'legal/ffmpeg-configure.txt',notices/'ffmpeg-configure.txt')
            copy(ROOT/'legal/ffmpeg-source-changes.diff',notices/'ffmpeg-source-changes.diff')
            ffmpeg_tar=next((stage/'usr/share/licenses/skwd-paper/ffmpeg').glob('ffmpeg-*.tar.xz'))
            if repository.digest(ffmpeg_tar)!='cf38e0e28c7e5605942c4a77755349b0145804a397af37eb1fb4c77cb237f635':raise ValueError('FFmpeg source changed')
            with tarfile.open(ffmpeg_tar) as archive:
                headers=[]
                for file in ['libavcodec/jfdctfst.c','libavcodec/jfdctint_template.c','libavcodec/jrevdct.c']:
                    data=archive.extractfile('ffmpeg-9.0.1/'+file).read().decode();headers.append(file+'\n'+data[:data.index('*/')+2]+'\n')
                (notices/'JPEG-SOURCE-NOTICES.txt').write_text('\n'.join(headers))
        if before!=hash_elfs(stage):raise ValueError('Repack changed executable/library bytes')
        deps=[x.replace('-1.0.0beta26_3','-1.0.0beta26_4') if any(x.startswith(n+'-') for n in NAMES.values()) else x for x in props.get('run_depends',[])]
        if len(deps)!=len(props.get('run_depends',[])):raise ValueError('Dependency set changed')
        for path in [*stage.rglob('*'),stage]:
            if path.is_dir():path.chmod(0o755)
            os.utime(path,(EPOCH,EPOCH),follow_symlinks=False)
        version=name+'-1.0.0beta26_4'
        expressions={'MIT','Apache-2.0'}
        expressions.update(row['license'] for row in detail if row['scope']=='runtime-conservative' and row['license'])
        if component=='wall':expressions.update(['OFL-1.1','CC-BY-4.0','CC-BY-3.0','Unlicense'])
        if component=='paper':expressions.update(['LGPL-2.1-or-later','BSD-2-Clause','BSD-3-Clause'])
        licenses=', '.join(sorted(expressions))
        command=['xbps-create','-A','x86_64','-n',version,'-s',props['short_desc']+'; complete notices','-l',licenses,'-H',props['homepage'],'-B','Void community legal revision4; unchanged validated ELF','-D',' '.join(deps),'--shlib-requires',' '.join(props.get('shlib-requires',[])),str(stage)]
        subprocess.run(command,cwd=repo,env=dict(os.environ,SOURCE_DATE_EPOCH=str(EPOCH)),check=True)
        archive=repo/(version+'.x86_64.xbps')
        result.append({'name':name,'component':component,'version':version,'file':archive.name,'sha256':repository.digest(archive),'dependencies':deps,'unchanged_elf':before,'runtime_crates':len(runtime),'built_but_not_runtime':len(compiled-runtime)})
        repository.write(args.output/'repack.json',result)
    subprocess.run(['xbps-rindex','-a',*[str(repo/r['file']) for r in result]],check=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('packages',type=Path);p.add_argument('suite',type=Path);p.add_argument('closure',type=Path);p.add_argument('output',type=Path);p.add_argument('--build-inventory',type=Path);p.add_argument('--rust-notices',type=Path,default=Path('/usr/share/licenses/rust'));a=p.parse_args();repack(a)
