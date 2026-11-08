#!/usr/bin/env python3
"""DISPOSABLE VM ONLY: sign real fixtures; no production key/policy or public server."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import repository


def init(a):
    if not a.lab_only or os.geteuid()==0 or not sys.stdin.isatty():raise ValueError('Explicit interactive unprivileged lab required')
    if not ipaddress.ip_address(a.bind).is_private:raise ValueError('Private lab bind required')
    if subprocess.check_output(['findmnt','-n','-o','FSTYPE','--target',str(a.key_dir.parent)],text=True).strip()!='tmpfs':raise ValueError('Disposable key must stay in tmpfs')
    if a.resume:
        assert a.lab_root.is_dir() and a.key_dir.is_dir()
    else:
        a.lab_root.mkdir(mode=0o700);a.key_dir.mkdir(mode=0o700)
    key=a.key_dir/'private.pem';public=a.lab_root/'lab-public.pem'
    if not key.exists():
        subprocess.run(['openssl','genrsa','-traditional','-out',str(key),'4096'],check=True,timeout=90)
        key.chmod(0o600)
    with public.open('wb') as out:subprocess.run(['openssl','pkey','-in',str(key),'-pubout'],stdout=out,check=True)
    identity=repository.public_identity(public)
    base=a.lab_root/'baseline';base.mkdir(exist_ok=True)
    for path in sorted(a.baseline_repo.glob('*.xbps')):
        if not (base/path.name).exists():shutil.copyfile(path,base/path.name)
    assert len(list(base.glob('*.xbps')))==4
    subprocess.run(['xbps-rindex','-a',*[str(p) for p in sorted(base.glob('*.xbps'))]],check=True)
    for path in sorted(base.glob('*.xbps')):subprocess.run(['xbps-rindex','--privkey',str(key),'--sign-pkg',str(path)],check=True)
    subprocess.run(['xbps-rindex','--privkey',str(key),'--sign','--signedby','DISPOSABLE XBPS LAB KEY - NOT FOR PRODUCTION',str(base)],check=True)
    policy=repository.load(ROOT/'policy/release.json')
    # Separate lab fixture, never overwrite or clear the production policy.
    policy['distribution_approved']=True;policy['lab_only']=True
    policy['signing']={'public_key_spki_sha256':identity['spki_sha256'],'xbps_md5_fingerprint':identity['xbps_md5_fingerprint'],'identity':'DISPOSABLE XBPS LAB KEY - NOT FOR PRODUCTION'}
    revised=a.lab_root/'revised'
    if not revised.exists():repository.stage(SimpleNamespace(source_bundle=a.source_bundle,packages=a.revised_repo,output=revised,sources_manifest=a.sources_manifest,build_environment=None),policy)
    policy['license_review']={'approved':True,'reviewer':'USER-AUTHORIZED PRIVATE LAB ONLY','evidence':'Temporary cryptographic rehearsal; DOES NOT AUTHORIZE PUBLIC DISTRIBUTION','approved_candidate_sha256':repository.digest(revised/'candidate.json'),'blockers':[]}
    repository.write(a.lab_root/'lab-policy.json',policy)
    if not (revised/'release.json').exists():repository.sign(SimpleNamespace(directory=revised,private_key=key,approve_signing=True),policy)
    repository.verify(revised,identity['spki_sha256'])
    http=a.lab_root/'http';http.mkdir(exist_ok=True)
    active=http/'repository'
    if not active.exists():shutil.copytree(base,active)
    log=(a.lab_root/'http.log').open('ab')
    pidfile=a.lab_root/'http.pid'
    if not pidfile.exists():
        worker=subprocess.Popen([sys.executable,'-m','http.server',str(a.port),'--bind',a.bind,'--directory',str(http)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);pidfile.write_text(str(worker.pid))
    result={'scope':'DISPOSABLE PRIVATE LAB ONLY','identity':identity,'key_storage':'private tmpfs; no private material exported','url':'http://'+a.bind+':'+str(a.port)+'/repository','source_sha256':repository.digest(a.source_bundle),'revised_candidate_sha256':repository.digest(revised/'candidate.json'),'manifest_verified':True,'baseline_packages':{p.name:repository.digest(p) for p in sorted(base.glob('*.xbps'))},'revised_packages':{p.name:repository.digest(p) for p in sorted(revised.glob('*.xbps'))}}
    repository.write(a.lab_root/'server-results.json',result);print(json.dumps(result,indent=2))


def activate(a):
    src=a.lab_root/a.revision;dst=a.lab_root/'http/repository'
    # Retain old version files for cached-index clients; move index last.
    for path in sorted(src.iterdir()):
        if path.is_file() and path.name!='x86_64-repodata' and not path.name.endswith('-lock'):shutil.copyfile(path,dst/path.name)
    shutil.copyfile(src/'x86_64-repodata',dst/'next-repodata');(dst/'next-repodata').replace(dst/'x86_64-repodata')
    print('Active lab revision:',a.revision)


def mutate(a):
    filename='skwd-lens-local-1.0.0beta26_4.x86_64.xbps'+('.sig2' if a.kind=='signature' else '')
    original=a.lab_root/'revised'/filename;target=a.lab_root/'http/repository'/filename
    data=bytearray(original.read_bytes());data[len(data)//2]^=1;target.write_bytes(data)
    print('Modified test copy only:',filename)


def restore(a):
    for suffix in ['', '.sig2']:
        name='skwd-lens-local-1.0.0beta26_4.x86_64.xbps'+suffix
        shutil.copyfile(a.lab_root/'revised'/name,a.lab_root/'http/repository'/name)
    print('Original test payload and signature restored')


def cleanup(a):
    pidfile=a.lab_root/'http.pid'
    if pidfile.exists():
        pid=int(pidfile.read_text());command=Path('/proc/'+str(pid)+'/cmdline')
        if command.exists():
            data=command.read_bytes()
            if b'http.server' not in data or str(a.lab_root/'http').encode() not in data:raise ValueError('Refusing to stop an unrelated PID')
            os.kill(pid,signal.SIGTERM)
        pidfile.unlink()
    key=a.key_dir/'private.pem'
    if key.exists():key.unlink()
    if a.key_dir.exists():a.key_dir.rmdir()
    repository.write(a.lab_root/'key-destruction.json',{'private_key_deleted':not key.exists(),'storage':'tmpfs','production_key_created':False})
    print('Lab server stopped; disposable tmpfs key removed')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lab-root',type=Path,required=True)
    s=p.add_subparsers(dest='mode',required=True)
    x=s.add_parser('init');x.add_argument('--baseline-repo',type=Path,required=True);x.add_argument('--revised-repo',type=Path,required=True);x.add_argument('--source-bundle',type=Path,required=True);x.add_argument('--sources-manifest',type=Path,required=True);x.add_argument('--key-dir',type=Path,required=True);x.add_argument('--bind',default='10.44.0.1');x.add_argument('--port',type=int,default=8080);x.add_argument('--lab-only',action='store_true');x.add_argument('--resume',action='store_true')
    x=s.add_parser('activate');x.add_argument('revision',choices=['baseline','revised'])
    x=s.add_parser('mutate');x.add_argument('kind',choices=['package','signature'])
    s.add_parser('restore');x=s.add_parser('cleanup');x.add_argument('--key-dir',type=Path,required=True)
    a=p.parse_args();{'init':init,'activate':activate,'mutate':mutate,'restore':restore,'cleanup':cleanup}[a.mode](a)
