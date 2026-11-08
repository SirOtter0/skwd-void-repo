#!/usr/bin/env python3
"""Recover omitted workspace license files using crate-recorded source revisions."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request
import urllib.parse

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('missing_inventory',type=Path);args=parser.parse_args()
root=Path(__file__).resolve().parents[1];output=root/'review/crate-upstream-notices';output.mkdir(exist_ok=True)
missing=json.loads(args.missing_inventory.read_text());groups={};mapping={};heads={}
for name,item in missing.items():
 repo=item['repository'].removeprefix('https://github.com/').removesuffix('.git').rstrip('/')
 if item['vcs']:
  commit=item['vcs']['git']['sha1'];provenance='exact revision from vendored .cargo_vcs_info.json'
 else:
  # The coordinated release omits VCS metadata for these in-workspace vendor overrides.
  # Obtain the authoritative project's license at a fixed revision; do not claim source equality.
  if repo not in heads:
   with urllib.request.urlopen('https://api.github.com/repos/'+repo+'/commits/HEAD') as response:heads[repo]=json.load(response)['sha']
  commit=heads[repo]
  provenance='crate declares MIT/repository; VCS absent in coordinated vendor, license only retrieved from pinned upstream revision'
 mapping[name]={'repository':repo,'commit':commit,'evidence':provenance};groups.setdefault((repo,commit),[]).append(name)


def group(key):
 repo,commit=key;records=[]
 for file in ['LICENSE','LICENSE.txt','LICENSE.md','LICENSE-MIT','LICENSE-APACHE','COPYING','NOTICE','NOTICE.md','NOTICE.txt','UNLICENSE']:
  url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+file
  existing=output/repo.replace('/','--')/commit/file
  try:
   data=existing.read_bytes() if existing.is_file() else urllib.request.urlopen(url,timeout=30).read()
  except urllib.error.HTTPError as error:
   if error.code==404:continue
   raise
  if len(data)>500000:raise ValueError('Unexpectedly large license file')
  path=output/repo.replace('/','--')/commit/file;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  records.append({'file':str(path.relative_to(root)),'repository':repo,'commit':commit,'path':file,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),'authenticity':'HTTPS official repository immutable commit URL; hash recorded (not a separate signature)'})
 if not records:
  for file in ['README.md','README.rst','README']:
   url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+file
   try:data=urllib.request.urlopen(url,timeout=30).read()
   except urllib.error.HTTPError as error:
    if error.code==404:continue
    raise
   if not any(x in data.lower() for x in [b'cc0',b'public domain',b'license',b'licence']):continue
   path=output/repo.replace('/','--')/commit/file;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
   records.append({'file':str(path.relative_to(root)),'repository':repo,'commit':commit,'path':file,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'kind':'upstream README license declaration'})
   break
 if not records and repo=='lifthrasiir/hexf':
  file='parse/Cargo.toml';url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+file;data=urllib.request.urlopen(url,timeout=30).read()
  if b'CC0-1.0' not in data:raise ValueError('Missing explicit CC0 declaration')
  path=output/repo.replace('/','--')/commit/'SOURCE-CARGO.toml';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  records.append({'file':str(path.relative_to(root)),'repository':repo,'commit':commit,'path':'SOURCE-CARGO.toml','url':url,'sha256':hashlib.sha256(data).hexdigest(),'kind':'exact upstream package manifest CC0 grant; canonical CC0 text supplied separately'})
 if not records:raise ValueError('No license found at recorded source revision: '+repo+' '+commit)
 return key,records

files={}
with ThreadPoolExecutor(max_workers=6) as pool:
 for key,rows in pool.map(group,groups):files[key]=rows
for name,info in mapping.items():info['notices']=files[(info['repository'],info['commit'])]
(output/'manifest.json').write_text(json.dumps(mapping,indent=2)+'\n')
print('Crates supplemented:',len(mapping),'source revisions:',len(groups),'notice files:',sum(len(x) for x in files.values()))
