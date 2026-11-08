#!/usr/bin/env python3
"""Root inside a disposable VM only: controlled XBPS acceptance/negative tests."""
import argparse
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'));import repository
PACKAGES=['skwd-wall-v2-local','skwd-deck-local','skwd-lens-local','skwd-paper-local']


def fetch(a,name,target):
    if Path(name).name!=name:raise ValueError('Unsafe file name')
    with urllib.request.urlopen(a.url+'/'+name,timeout=60) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)


def run(a,label,args,trust=False,expected=0):
    command=['xbps-install','-i','-R',a.url,'-C',str(a.root/'conf'),'-c',str(a.root/('cache-'+label)),*args]
    p=subprocess.Popen(['stdbuf','-o0','-e0',*command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,TERM='dumb'))
    data=b'';answered=False;deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        if select.select([p.stdout],[],[],.2)[0]:
            chunk=os.read(p.stdout.fileno(),65536)
            if not chunk:break
            data+=chunk
            if len(data)>4*1024*1024:raise RuntimeError('Unexpected log size')
            if trust and b'Do you want to import this public key' in data and not answered:
                if a.fingerprint.encode() not in data:
                    (a.root/(label+'.log')).write_text(data.decode(errors='replace'));p.kill();p.wait()
                    raise ValueError('Unexpected native key fingerprint; refused import')
                p.stdin.write(b'y\n');p.stdin.flush();answered=True
        elif p.poll() is not None:break
    else:
        os.killpg(p.pid,signal.SIGKILL);raise RuntimeError('XBPS timeout')
    data+=p.stdout.read();code=p.wait(timeout=10);text=data.decode(errors='replace');(a.root/(label+'.log')).write_text(text)
    if expected==0 and code!=0:raise RuntimeError(label+' failed: '+text[-1600:])
    if expected!=0 and code==0:raise RuntimeError('Negative test unexpectedly succeeded')
    return {'exit':code,'native_key_prompt_confirmed':answered,'log':label+'.log'},text


def versions():
    result={}
    for name in PACKAGES:
        p=subprocess.run(['xbps-query','-p','pkgver',name],capture_output=True,text=True);result[name]=p.stdout.strip() if p.returncode==0 else None
    return result


def init(a):
    a.root.mkdir(mode=0o700,exist_ok=True);(a.root/'conf').mkdir(exist_ok=True)
    before=versions()
    if any(before.values()):raise ValueError('Client already has a port package')
    (a.root/'conf/10-lab.conf').write_text('repository='+a.url+'\n')
    keys=sorted(p.name for p in Path('/var/db/xbps/keys').iterdir())
    routes=subprocess.check_output(['ip','route'],text=True)
    if 'default' in routes:raise ValueError('Lab client has an external route')
    fetch(a,'x86_64-repodata',a.root/'preflight-repodata')
    with tarfile.open(a.root/'preflight-repodata') as archive:
        members=repository.members(archive);meta=repository.plistlib.loads(archive.extractfile(members['index-meta.plist']).read())
    public=a.root/'lab-public.pem';public.write_bytes(meta['public-key']);identity=repository.public_identity(public)
    if identity['spki_sha256']!=a.key_sha256 or identity['xbps_md5_fingerprint']!=a.fingerprint:raise ValueError('Preflight key identity mismatch')
    if a.fingerprint+'.plist' in keys:raise ValueError('Lab key was already trusted')
    sync,text=run(a,'import-key',['-S'],trust=True)
    if a.fingerprint not in text or not (Path('/var/db/xbps/keys')/(a.fingerprint+'.plist')).is_file():raise ValueError('Native XBPS import not demonstrated')
    repository.write(a.root/'state.json',{'initial_versions':before,'initial_keys':keys,'identity':identity,'network_routes':routes,'checks':{'key_import':sync}})
    print('Clean client imported the independently checked disposable key')


def signed_copy(a):
    out=a.root/'verified-signed-release';out.mkdir(exist_ok=True)
    for name in ['public.pem','release.json','release.json.sig']:fetch(a,name,out/name)
    if repository.public_identity(out/'public.pem')['spki_sha256']!=a.key_sha256:raise ValueError('Release key mismatch')
    subprocess.run(['openssl','dgst','-sha256','-verify',str(out/'public.pem'),'-signature',str(out/'release.json.sig'),str(out/'release.json')],check=True)
    manifest=repository.load(out/'release.json')
    for name,expected in manifest['files'].items():
        if Path(name).name!=name:raise ValueError('Unsafe signed artifact name')
        if (out/name).exists():
            if repository.digest(out/name)!=expected:raise ValueError('Existing release file mismatch')
            continue
        cached=a.root/'cache-upgrade'/name
        if cached.is_file() and repository.digest(cached)==expected:shutil.copyfile(cached,out/name)
        else:fetch(a,name,out/name)
    repository.verify(out,a.key_sha256)
    return {'signed_manifest_and_all_artifact_hashes':'PASS','packages_and_signatures':4,'corresponding_source_sha256':manifest['source_bundle']['sha256']}


def phase(a):
    state=repository.load(a.root/'state.json')
    if a.mode=='baseline':
        outcome,text=run(a,'install-baseline',['-y',*PACKAGES]);current=versions()
        if not all(v and v.endswith('-1.0.0beta26_3') for v in current.values()):raise ValueError('Wrong baseline installation')
        state['checks']['baseline_install']=dict(outcome,versions=current)
    elif a.mode=='rollback':
        outcome,text=run(a,'rollback-baseline',['-S','-f','-y',*PACKAGES]);current=versions()
        if not all(v and v.endswith('-1.0.0beta26_3') for v in current.values()):raise ValueError('Fixture rollback failed')
        state['checks']['fixture_rollback']=dict(outcome,versions=current)
    elif a.mode=='plan':
        before=versions();run(a,'sync-before-upgrade-plan',['-S'])
        outcome,text=run(a,'upgrade-plan',['-n','-u',*PACKAGES])
        if versions()!=before or text.count('1.0.0beta26_4')<4:raise ValueError('Update simulation did not offer four unchanged-state updates')
        state['checks']['upgrade_simulation']=dict(outcome,installed_versions_unchanged=True)
    elif a.mode=='upgrade':
        outcome,text=run(a,'upgrade',['-S','-y','-u',*PACKAGES]);current=versions()
        if not all(v and v.endswith('-1.0.0beta26_4') for v in current.values()):raise ValueError('Wrong revised installation')
        state['checks']['revised_install']=dict(outcome,versions=current)
        state['checks']['signed_release']=signed_copy(a)
        subprocess.run(['xbps-pkgdb','-a'],check=True,stdout=(a.root/'pkgdb-after-upgrade.log').open('w'),stderr=subprocess.STDOUT)
        state['lens_sha256']=repository.digest(Path('/usr/bin/skwd-lens'))
    elif a.mode in ['bad-package','bad-signature']:
        before=versions();outcome,text=run(a,a.mode,['-f','-y','skwd-lens-local'],expected=1)
        if versions()!=before or repository.digest(Path('/usr/bin/skwd-lens'))!=state['lens_sha256']:raise ValueError('Rejected transaction changed installed payload')
        if not re.search(r'(signature|hash|checksum).*(invalid|not valid|mismatch|failed|error)|(?:invalid|failed).*signature',text,re.I|re.S):raise ValueError('Failure was not an integrity rejection: '+text[-1000:])
        state['checks'][a.mode]=dict(outcome,installed_payload_unchanged=True,integrity_rejected=True)
    elif a.mode=='remove':
        p=subprocess.run(['xbps-remove','-y',*PACKAGES],capture_output=True,text=True);(a.root/'remove.log').write_text(p.stdout+p.stderr)
        if p.returncode or any(versions().values()):raise ValueError('Package removal failed')
        services=subprocess.check_output(['ls','-l','/var/service'],text=True)
        if services!=(a.root/'initial-services.txt').read_text():raise ValueError('Services changed during package test')
        key=Path('/var/db/xbps/keys')/(a.fingerprint+'.plist');key.unlink()
        (a.root/'conf/10-lab.conf').unlink();(a.root/'conf').rmdir()
        if sorted(p.name for p in Path('/var/db/xbps/keys').iterdir())!=state['initial_keys']:raise ValueError('Trust store did not return to baseline')
        state['checks']['removal']={'exit':0,'port_packages_absent':True,'lab_repository_config_removed':True,'temporary_key_untrusted':True,'services_unchanged':True}
    repository.write(a.root/'state.json',state);print(json.dumps(state['checks'],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--url',default='http://10.44.0.1:8080/repository');p.add_argument('--key-sha256',required=True);p.add_argument('--fingerprint',required=True);p.add_argument('--lab-only',action='store_true');p.add_argument('mode',choices=['init','baseline','rollback','plan','upgrade','bad-package','bad-signature','remove']);a=p.parse_args()
    if not a.lab_only or os.geteuid()!=0:raise SystemExit('Explicit disposable guest-root lab required')
    if a.url!='http://10.44.0.1:8080/repository':raise SystemExit('Only the private two-VM lab endpoint is allowed')
    if a.mode=='init':init(a)
    else:phase(a)
