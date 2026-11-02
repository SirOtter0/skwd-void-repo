#!/usr/bin/env bash
# Run ONLY inside a disposable, pre-provisioned Void x86_64 glibc build VM.
set -euo pipefail
umask 077
[[ $EUID -ne 0 ]] || { echo 'Build as a normal user' >&2; exit 1; }
[[ $# == 1 && ! -e $1 ]] || { echo 'Usage: build-candidate.sh NEW-ABSOLUTE-WORK-DIRECTORY' >&2; exit 1; }
[[ $1 == /* && $1 != *[[:space:]]* ]] || exit 1
[[ $(uname -m) == x86_64 && -f /etc/os-release ]] || exit 1
grep -q '^ID=void$' /etc/os-release
getconf GNU_LIBC_VERSION
for tool in git curl python3 bwrap xbps-query xbps-create xbps-rindex; do command -v "$tool" >/dev/null; done
infra=$(cd -- "$(dirname -- "$0")/.." && pwd)
port_commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["port_commit"])' "$infra/policy/release.json")
[[ $port_commit =~ ^[a-f0-9]{40}$ ]] || exit 1
[[ $(rustc --version | cut -d' ' -f2) == 1.99.0 ]] || { echo 'Unreviewed Rust version' >&2; exit 1; }
mkdir -m700 -- "$1"
work=$(realpath -- "$1")
exec > >(tee "$work/build.log") 2>&1
xbps-query -l > "$work/build-packages.txt"
uname -a > "$work/kernel.txt"
for tool in rustc cargo cc bwrap; do "$tool" --version > "$work/$tool-version.txt" 2>&1; done
xbps-create -V > "$work/xbps-create-version.txt" 2>&1
# No credentials persisted and no build input is taken from the workstation.
GIT_CONFIG_NOSYSTEM=1 git -c credential.helper= clone --no-checkout --single-branch --branch feat/void-linux-support https://github.com/SirOtter0/skwd-wall.git "$work/port"
git -C "$work/port" checkout --detach "$port_commit"
[[ $(git -C "$work/port" rev-parse HEAD) == "$port_commit" ]]
cd "$work/port"
python3 - "$work/official-suite.tar.xz" <<'FETCH'
import hashlib,json,pathlib,sys,urllib.request
m=json.loads(pathlib.Path('security/void-beta26/sources.json').read_text());p=pathlib.Path(sys.argv[1])
with urllib.request.urlopen(m['archive_url'],timeout=120) as src,p.open('xb') as dst:
 while data:=src.read(1024*1024):dst.write(data)
assert p.stat().st_size==m['archive_bytes']
with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==m['original_archive_sha256']
FETCH
python3 packaging/void/prepare-source.py "$work/official-suite.tar.xz" "$work/source" --fetch-missing-crates --fetch-ffmpeg
python3 "$infra/scripts/license-inventory.py" "$work/source/suite" "$work/license-inventory.json"
mkdir "$work/build"
for component in wall deck lens paper; do
 packaging/void/build.sh "$work/source/suite" "$work/build/$component" "$component"
done
SOURCE_DATE_EPOCH=1792079636 python3 packaging/void/package.py --build-root "$work/build" --output "$work/packages"
python3 "$infra/scripts/repository.py" inspect "$work/packages/repository" > "$work/package-inspection.json"
# Source archive is prepared locally for review, not uploaded or published.
# It contains the exact patched vendor/sources, FFmpeg source and public recipes.
mkdir "$work/source-delivery"
git archive HEAD | tar xf - -C "$work/source-delivery"
cp "$work/source/sources.json" "$work/source-delivery/PREPARED-SOURCES.json"
tar --sort=name --mtime=@1792079636 --owner=0 --group=0 --numeric-owner -cJf "$work/corresponding-source.tar.xz" -C "$work/source" suite -C "$work/source-delivery" .
python3 - "$work" <<'PROVENANCE'
import pathlib,json,sys
r=pathlib.Path(sys.argv[1]); data={'build_packages':(r/'build-packages.txt').read_text().splitlines(),'kernel':(r/'kernel.txt').read_text().strip(),'tool_versions':{p.name.removesuffix('-version.txt'):p.read_text().strip() for p in r.glob('*-version.txt')}}
(r/'build-environment.json').write_text(json.dumps(data,indent=2)+'\n')
PROVENANCE
python3 "$infra/scripts/repository.py" stage "$work/packages/repository" "$work/corresponding-source.tar.xz" "$work/source/sources.json" "$work/candidate" --build-environment "$work/build-environment.json"
echo 'Unsigned LOCAL candidate only. Complete licensing, clean installation tests and owner review before any upload/signing.'
