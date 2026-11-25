#!/bin/bash
set -euo pipefail
media=$1
export SSL_CERT_FILE="$media/tls-cert.pem"
export SSL_CA_CERT_FILE="$media/tls-cert.pem"
root=$(cat "$media/origin")
select_case() { python3 -I -c 'from urllib.request import urlopen; urlopen(__import__("sys").argv[1], timeout=15).close()' "$root/select/$1"; }
helper=(python3 -I "$media/test-sync-channel.py")
install() { xbps-install -C /run/skwd-channel-lab-conf "$@"; }
version_is() {
    for p in skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local; do
        [[ $(xbps-query -p pkgver "$p") == "$p-$1" ]]
    done
}
reject() {
    select_case "$1"
    previous=$(readlink /var/lib/skwd-xbps-lab/current)
    if "${helper[@]}"; then echo "FAIL accepted $1"; exit 1; fi
    [[ $(readlink /var/lib/skwd-xbps-lab/current) == "$previous" ]]
    version_is 1.0.0beta29_2
    printf 'PASS rejected %s and kept installed/current state\n' "$1"
}
# The guest starts from the known pre-beta29 base. Use no external repositories.
for p in skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local; do
    if xbps-query "$p" >/dev/null 2>&1; then echo "FAIL guest already has $p"; exit 1; fi
done
nics=(/sys/class/net/*)
for nic in "${nics[@]}"; do
    device=${nic##*/}
    if [[ $device != lo ]]; then
        ip link set "$device" up
        ip address replace 10.0.2.15/24 dev "$device"
        break
    fi
done
# Use the host loopback through QEMU slirp. Keep the guest offline otherwise.
ip route del default 2>/dev/null || true
ip -6 route del default 2>/dev/null || true
printf '%s\n' '10.0.2.2 repo.skwd.test' >> /etc/hosts
ip -br address
select_case initial
mkdir -p /run/skwd-channel-lab-conf
# Mask distribution repository defaults for this offline lab only.
for conf in /usr/share/xbps.d/*repository*.conf; do
    printf '# masked for offline lab\n' > "/run/skwd-channel-lab-conf/${conf##*/}"
done
echo 'PASS HTTPS with guest-only TLS trust'

"${helper[@]}" --configure
previous=$(readlink /var/lib/skwd-xbps-lab/current)
"${helper[@]}" --configure
[[ $(readlink /var/lib/skwd-xbps-lab/current) == "$previous" ]]
echo 'PASS repeat configuration'
local_repo=/var/lib/skwd-xbps-lab/current
fingerprint=$(cat "$media/xbps-fingerprint")
receipt="/var/db/xbps/keys/$fingerprint.plist"
printf 'n\n' | install -i -R "$local_repo" -S > /run/skwd-channel-key-prompt 2>&1 || true
grep -F "$fingerprint" /run/skwd-channel-key-prompt
test ! -e "$receipt"
printf 'y\n' | install -i -R "$local_repo" -S
test -e "$receipt"
echo 'PASS native XBPS verified-snapshot key import and prompt refusal'
install -y skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
version_is 1.0.0beta29_2
xbps-pkgdb -a
echo 'PASS clean installation of the four synthetic packages'

for scenario in interrupted bad-index bad-signature unavailable expired bad-key; do
    reject "$scenario"
done
select_case update
# A sync of XBPS reads the verified local snapshot only.
install -Suy </dev/null
version_is 1.0.0beta29_2
"${helper[@]}"
install -Suy </dev/null
version_is 1.0.0beta29_3
xbps-pkgdb -a
echo 'PASS simulated coordinated update with xbps-install -Su after authentication'
bad_previous=$(readlink /var/lib/skwd-xbps-lab/current)
for scenario in initial newer-sequence-older-version; do
    select_case "$scenario"
    if "${helper[@]}"; then echo "FAIL accepted replay $scenario"; exit 1; fi
    [[ $(readlink /var/lib/skwd-xbps-lab/current) == "$bad_previous" ]]
    version_is 1.0.0beta29_3
done
echo 'PASS replay and version rollback refused'
previous="/var/lib/skwd-xbps-lab/$previous"
old=(skwd-wall-v2-local-1.0.0beta29_2 skwd-deck-local-1.0.0beta29_2 skwd-lens-local-1.0.0beta29_2 skwd-paper-local-1.0.0beta29_2)
install -i -R "$previous" -n -f "${old[@]}"
install -i -R "$previous" -y -f "${old[@]}"
version_is 1.0.0beta29_2
[[ $(readlink /var/lib/skwd-xbps-lab/current) == "$bad_previous" ]]
xbps-pkgdb -a
echo 'PASS explicit rollback, stable cursor unchanged'

# Probe native remote XBPS after the authenticated local-channel scenarios.
select_case initial
direct="$root/releases/xbps-beta29_2"
fingerprint=$(cat "$media/xbps-fingerprint")
if timeout 20 xbps-query -i -M -v -R --repository "$direct" -L | grep -F "$fingerprint"; then
    timeout 20 xbps-install -i -M -D -y -c /run/skwd-channel-native-cache \
        -C /run/skwd-channel-lab-conf -R "$direct" skwd-lens-local
    echo 'PASS native remote signed package download'
else
    echo 'NOT TESTED native remote key import with the lab HTTPS transport'
fi
