#!/bin/bash
set -euo pipefail
media=$1
[[ $(cat /sys/block/vda/serial) == skwd-channel-lab ]]
export SSL_CERT_FILE="$media/tls-cert.pem"
export SSL_CA_CERT_FILE="$media/tls-cert.pem"
root=$(cat "$media/origin")
repo="$root/native"
config=/etc/xbps.d/30-skwd-void.conf
pkgs=(skwd-wall-v2-local skwd-deck-local skwd-paper-local skwd-lens-local)
fp=$(cat "$media/xbps-fingerprint")
select_case() { python3 -I -c 'from urllib.request import urlopen; urlopen(__import__("sys").argv[1], timeout=15).close()' "$root/select/$1"; }
versions() {
    for pkg in "${pkgs[@]}"; do
        [[ $(xbps-query -p pkgver "$pkg") == "$pkg-$1" ]]
    done
}
native_update() { printf 'y\n' | xbps-install -Su; }

iface=$(basename "$(find /sys/class/net -mindepth 1 -maxdepth 1 ! -name lo -print -quit)")
ip link set "$iface" up
ip address replace 10.0.2.15/24 dev "$iface"
ip route del default 2>/dev/null || true
ip -6 route del default 2>/dev/null || true
printf '%s\n' '10.0.2.2 repo.skwd.test' >> /etc/hosts
# Replace distribution mirrors inside the disposable guest with the separate lab dependency origin.
for conf in /usr/share/xbps.d/*repository*.conf /etc/xbps.d/*repository*.conf; do
    [[ -f $conf ]] || continue
    printf '# offline VM fixture\n' > "/etc/xbps.d/${conf##*/}"
done
printf 'repository=%s/void\n' "$root" > /etc/xbps.d/00-native-lab.conf
(select_case initial; set -C; printf 'repository=%s\n' "$repo" > "$config")
if (set -C; printf 'repository=%s\n' "$repo" > "$config") 2>/dev/null; then exit 1; fi
grep -Fx "repository=$repo" "$config"
xbps-query -i -M -v -R --repository "$repo" -L | grep -F "$fp"
printf 'n\nn\n' | xbps-install -S > /tmp/native-key-prompt 2>&1 || true
grep -F "$fp" /tmp/native-key-prompt
test ! -e "/var/db/xbps/keys/$fp.plist"
printf 'y\ny\ny\n' | xbps-install -S skwd-wall-v2-local
test -f "/var/db/xbps/keys/$fp.plist"
for pkg in "${pkgs[@]:0:3}"; do
    [[ $(xbps-query -p pkgver "$pkg") == "$pkg-1.0.0beta29_2" ]]
done
xbps-query -p pkgver skwd-lab-system-dependency
! xbps-query skwd-lens-local
printf 'y\n' | xbps-install skwd-lens-local
versions 1.0.0beta29_2
echo 'PASS native config, fingerprint, Wall dependencies and optional Lens'

select_case stale
native_update
versions 1.0.0beta29_2
echo 'PASS stale index leaves installed versions unchanged'

for scenario in bad-signature interrupted inconsistent unavailable; do
    select_case "$scenario"
    code=0
    native_update > "/tmp/skwd-$scenario.log" 2>&1 || code=$?
    cat "/tmp/skwd-$scenario.log"
    versions 1.0.0beta29_2
    case "$scenario" in
        bad-signature) grep -Eiq 'invalid signature|signature.*(fail|invalid|not valid)|signature verification failed' "/tmp/skwd-$scenario.log"; [[ $code != 0 ]];;
        interrupted|inconsistent) [[ $code != 0 ]];;
        unavailable) grep -Eiq '503|unavailable|failed' "/tmp/skwd-$scenario.log";;
    esac
    echo "PASS native $scenario preserves installed versions (exit $code)"
done
select_case update
if ! native_update; then
    versions 1.0.0beta29_2
    echo 'Retrying plain -Su after XBPS rejected stale cached bytes'
    native_update
fi
versions 1.0.0beta29_3
xbps-pkgdb -a
echo 'PASS native -Su discovers coordinated update after stale index'

previous=()
for pkg in "${pkgs[@]}"; do previous+=("$pkg-1.0.0beta29_2"); done
xbps-install -i -M -n -f -R "$root/history" "${previous[@]}"
printf 'y\n' | xbps-install -i -M -f -R "$root/history" "${previous[@]}"
versions 1.0.0beta29_2
echo 'PASS explicit coordinated native rollback'

# Explicit migration on the same XBPS configuration path, preserving the staged snapshot.
select_case initial
python3 -I "$media/test-sync-channel.py"
local_repo=/var/lib/skwd-xbps-lab/current
snapshot=$(readlink "$local_repo")
printf 'repository=%s\n' "$local_repo" > "$config"
python3 -I "$media/test-sync-channel.py" --configure
native_update
versions 1.0.0beta29_2
printf 'repository=%s\n' "$repo" > "$config"
select_case update
native_update
versions 1.0.0beta29_3
[[ $(readlink "$local_repo") == "$snapshot" ]]
xbps-pkgdb -a
echo 'PASS migration preserves authenticated state and allows native -Su'
