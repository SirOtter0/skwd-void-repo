#!/usr/bin/env python3
"""Fetch immutable official license/attribution texts, checking their Git blob IDs."""
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.parse
import argparse

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('suite',type=Path);args=parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review/upstream-notices'
OUT.mkdir(exist_ok=True)
records = []


def api(repo, suffix):
    with urllib.request.urlopen('https://api.github.com/repos/' + repo + '/' + suffix, timeout=60) as response:
        return json.load(response)


def tree(repo, commit):
    data = api(repo, 'git/trees/' + commit + '?recursive=1')
    if data.get('truncated'):
        raise ValueError('Truncated tree')
    return data['tree']


def fetch(repo, commit, path, blob, label):
    url = 'https://raw.githubusercontent.com/' + repo + '/' + commit + '/' + urllib.parse.quote(path, safe='/')
    destination = OUT / label / path
    data = destination.read_bytes() if destination.is_file() else urllib.request.urlopen(url, timeout=60).read()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if actual != blob:
        raise ValueError('Git object mismatch: ' + path)
    destination = OUT / label / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    records.append({'repository': repo, 'commit': commit, 'path': path, 'url': url, 'git_blob_sha1': blob,
                    'sha256': hashlib.sha256(data).hexdigest(), 'file': str(destination.relative_to(ROOT))})


nerd_repo = 'ryanoasis/nerd-fonts';nerd_commit = 'fa7b859994228a9c8759f99c55a8d31ee92a1b5e'
items = tree(nerd_repo, nerd_commit)
for item in items:
    path = item['path'];name = Path(path).name.lower()
    if item['type'] == 'blob' and (path == 'LICENSE' or path == 'src/glyphs/README.md' or path.endswith('license-audit.md') or
       (path.startswith(('src/glyphs/', 'src/unpatched-fonts/NerdFontsSymbolsOnly/')) and (any(x in name for x in ['license', 'copying', 'notice', 'copyright']) or name in ['ofl.txt','readme.md','readme.rst']))):
        fetch(nerd_repo, nerd_commit, path, item['sha'], 'nerd-fonts-3.4.0')
font = args.suite / 'skwd-wall/assets/SymbolsNerdFont-Regular.ttf'
data=font.read_bytes();font_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
matches=[{'path':p['path'],'git_blob_sha1':p['sha']} for p in items if p['type']=='blob' and p['sha']==font_blob]
if not matches:raise ValueError('Embedded Symbols font does not match the official pinned Nerd release tree')
(OUT/'nerd-font-match.json').write_text(json.dumps({'repository':nerd_repo,'commit':nerd_commit,'embedded_font_sha256':hashlib.sha256(data).hexdigest(),'matches':matches},indent=2)+'\n')

for repo,commit,label,keep in [
 ('googlefonts/roboto-3-classic','5166f3d07889bf7d3732fb72e09623d7e52f862b','roboto',lambda p:p=='OFL.txt'),
 ('notofonts/noto-cjk','f8d157532fbfaeda587e826d4cd5b21a49186f7c','noto-cjk',lambda p:p in ['LICENSE','Sans/LICENSE','Serif/LICENSE','README.md','Sans/README.md']),
 ('notofonts/noto-fonts','ffebf8c1ee449e544955a7e813c54f9b73848eac','noto',lambda p:p=='LICENSE' or (Path(p).name.upper() in ['LICENSE','OFL.TXT'] and any(s in p for s in ['NotoSansArabicUI/','NotoSansBengaliUI/','NotoSansDevanagariUI/','NotoSansSymbols2/'])))]:
    for item in tree(repo,commit):
        if item['type']=='blob' and keep(item['path']):fetch(repo,commit,item['path'],item['sha'],label)

repo='Traverse-Research/intel-tex-rs-2';commit='9a05fb8926d635014fddfcadb02ffd5c84822688';items=tree(repo,commit)
submodules=[p for p in items if p['type']=='commit'];print('Intel submodules:',submodules)
for item in items:
    if item['path']=='.gitmodules':fetch(repo,commit,item['path'],item['sha'],'intel-wrapper')
for item in submodules:
    if item['path']=='vendor':
        native_repo='GameTechDev/ISPCTextureCompressor';native_commit=item['sha']
        for child in tree(native_repo,native_commit):
            if child['type']=='blob' and (child['path'].lower().startswith(('license','notice','copying')) or (child['path'].startswith('ispc_texcomp/') and Path(child['path']).name.lower().startswith(('license','notice','copying')))):
                fetch(native_repo,native_commit,child['path'],child['sha'],'intel-native')
(OUT/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
print('Verified official notice files:',len(records));print('Exact Nerd font matches:',matches)
