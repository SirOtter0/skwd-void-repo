# Skwd-wall v2 for Void Linux

## Overview

Skwd-wall **`1.0.0beta29_2`** is a coordinated community release of Wall, Deck, Lens and Paper. SirOtter0 maintains the Void packaging externally. [Download beta29_2](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2)

## Compatibility

- **System:** Void Linux **x86_64 glibc**, with runit. The packages require glibc `2.41_1` or newer.
- **Desktop:** Start Wall and Deck as your regular user inside a Wayland session. Wall requires a working Vulkan implementation. The port was tested on Niri with NVIDIA RTX 4060 Ti. Musl, other architectures and additional GPU and media paths remain outside the verified scope.
- **Runtime dependencies:** A working Wayland/Vulkan stack plus `alsa-lib`, `fontconfig`, `freetype`, `libdav1d`, `libdrm`, `libgcc`, `libglvnd`, `libva`, `libxkbcommon`, `shaderc`, `vulkan-loader`, `wayland` and `zlib`. The package dry run checks the exact requirements. [Signed dependency inventory](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/LICENSE-INVENTORY.json)

<a name="installation"></a>

## Quick installation

**Native XBPS is the recommended method once the Pages repository is enabled.** The proposed origin is `https://sirotter0.github.io/skwd-void-repo/`. Until activation, use [Authenticated installation](#authenticated-installation) or [Advanced manual verification](#advanced-manual-verification).

On Void Linux x86_64 glibc, run the following after activation. The configuration command refuses to overwrite an existing file. If it already contains the native URL, run the install command on its own. If you already use the authenticated channel, follow the [migration instructions](docs/USERS.md#switching-repository-methods) to switch deliberately.

```sh
sudo sh -c 'set -C; printf "%s\n" "repository=https://sirotter0.github.io/skwd-void-repo" > /etc/xbps.d/30-skwd-void.conf' &&
sudo xbps-install -S skwd-wall-v2-local
```

When XBPS asks to import the Skwd key, confirm only if its fingerprint is `cb:49:33:d0:b1:e9:be:a6:3d:85:96:11:04:c4:50:e8` and matches a reference you trust independently. Void repositories supply runtime libraries. Wall installs matching Deck and Paper automatically. [Historical production key record](https://github.com/SirOtter0/skwd-void-repo/blob/97e727af21fe36479402102ea45757d16a672e93/review/production-key.json)

## Updating

For native installations:

```sh
sudo xbps-install -Su
```

This syncs the native HTTPS index and verifies the package signatures while updating. For authenticated installations, [synchronize the verified local snapshot first](#updating-the-authenticated-channel).

## Running Skwd-wall

In your regular Wayland session, start Deck in a terminal if it is not already running:

```sh
skwd-walld
```

In a second terminal of the same session, check the catalogue connection and launch the picker:

```sh
skwd-helm list --json
skwd-wall-v2
```

Paper provides the renderers. Lens is optional for semantic features. The packages do not configure session startup.

## Optional components

Install Lens for semantic features if you use the native repository:

```sh
sudo xbps-install skwd-lens-local
```

Wall, Deck, and Paper work without Lens. An installed Lens participates in normal updates.

## Authenticated installation

Use Bash on Void Linux x86_64 glibc. Use this method for signed index authentication and release freshness checks. If you already use the native repository, follow the [migration instructions](docs/USERS.md#switching-repository-methods) before changing the repository configuration. Compare the helper's SHA-256 and the production key fingerprints listed below with a trusted reference independent of the download server. [Synchronization helper](scripts/sync-channel.py)

```bash
set -euo pipefail
sudo xbps-install -S python3 curl openssl ca-certificates coreutils
stage=$(mktemp -d)
curl -q --fail --silent --show-error --location \
    --proto '=https' --proto-redir '=https' \
    'https://raw.githubusercontent.com/SirOtter0/skwd-void-repo/main/scripts/sync-channel.py' \
    --output "$stage/skwd-xbps-sync"
printf '%s  %s\n' '40656bd1eb388842747e37879fd6e48829a874f15da137884d3978f0f5a44f5c' "$stage/skwd-xbps-sync" | sha256sum --strict -c -
cat "$stage/skwd-xbps-sync"
```

After reviewing the helper, use the same shell to register the repository.

```bash
sudo install -d /usr/local/sbin
sudo install -o root -g root -m 0755 "$stage/skwd-xbps-sync" /usr/local/sbin/skwd-xbps-sync
sudo /usr/local/sbin/skwd-xbps-sync --configure
```

Ask XBPS to load the already authenticated local repository. At the key prompt, confirm only if the fingerprint is `cb:49:33:d0:b1:e9:be:a6:3d:85:96:11:04:c4:50:e8` and matches your independent reference.

```sh
sudo xbps-install -i -R /var/lib/skwd-xbps/current -S
sudo xbps-install -n -R /var/lib/skwd-xbps/current skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
```

Review the dry run, then install the four packages and check the package database.

```sh
sudo xbps-install -R /var/lib/skwd-xbps/current skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
sudo xbps-pkgdb -a
```

The helper uses the production fingerprints listed in Advanced verified installation. It authenticates the signed channel and manifest, verifies the index and all four XBPS signatures, and registers the verified local snapshot. Subsequent runs preserve an identical configuration and refuse to replace a different one.

### Updating the authenticated channel

Back up your Skwd data and retain the previous verified snapshot. Synchronize Skwd before the usual Void update.

```sh
sudo /usr/local/sbin/skwd-xbps-sync && sudo xbps-install -Su
```

Running `xbps-install -Su` alone still updates Void and can install Skwd versions already staged locally. XBPS does not download or authenticate a new Skwd snapshot on its own. The sync step stages packages without installing them. Avoid running a separate XBPS transaction while synchronization is in progress. [Update and recovery procedures](docs/USERS.md)

<a name="advanced-verified-installation"></a>

## Advanced manual verification

Use Bash, XBPS, curl, OpenSSL and the Void CA bundle. The commands below use `sudo` for package operations. If you administer Void through a root shell, run the marked package commands there with the same verified absolute path. Use trusted official Void repositories to install missing tools:

```sh
sudo xbps-install -S bash curl openssl ca-certificates coreutils diffutils
```

Before downloading, compare both fingerprints with a reference you trust independently of the release download. The [historical production-key record](https://github.com/SirOtter0/skwd-void-repo/blob/97e727af21fe36479402102ea45757d16a672e93/review/production-key.json) records the values announced before release. Stop if either value differs.

| Fingerprint | Expected value |
|---|---|
| SHA-256 SPKI | `3860084bca30b2022dd851490ba2f920524feb1dd38b578f69252e0a76e9d987` |
| XBPS RSA fingerprint | `cb:49:33:d0:b1:e9:be:a6:3d:85:96:11:04:c4:50:e8` |

Open a Bash shell and run the following block as your normal user. It creates a fresh directory, follows HTTPS redirects, verifies the public key and signed manifest, and checks all twelve manifest entries and four package signatures.

```bash
set -euo pipefail
repo='https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2'
expected_spki='3860084bca30b2022dd851490ba2f920524feb1dd38b578f69252e0a76e9d987'
expected_xbps='cb:49:33:d0:b1:e9:be:a6:3d:85:96:11:04:c4:50:e8'
stage=$(mktemp -d)
cd "$stage"

get() {
    curl --fail --silent --show-error --location \
        --proto '=https' --proto-redir '=https' "$repo/$1" -o "$1"
}

for file in xbps-public.pem SHA256SUMS SHA256SUMS.sig; do get "$file"; done
actual=$(openssl pkey -pubin -in xbps-public.pem -outform DER | sha256sum)
[[ ${actual%% *} == "$expected_spki" ]]
openssl dgst -sha256 -verify xbps-public.pem -signature SHA256SUMS.sig SHA256SUMS

names=(skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local)
packages=()
files=(x86_64-repodata corresponding-source.tar.xz SOURCE-FILES.json LICENSE-INVENTORY.json)
for name in "${names[@]}"; do
    packages+=("$name-1.0.0beta29_2")
    file="$name-1.0.0beta29_2.x86_64.xbps"
    files+=("$file" "$file.sig2")
done
printf '%s\n' "${files[@]}" | sort | diff -u - <(awk '{print $2}' SHA256SUMS | sort)
for file in "${files[@]}"; do get "$file"; done
sha256sum --strict -c SHA256SUMS
for package in "${packages[@]}"; do
    file="$package.x86_64.xbps"
    openssl dgst -sha256 -verify xbps-public.pem -signature "$file.sig2" "$file"
done
xbps-query -i -v -R --repository "$stage" -L | grep -F "$expected_xbps"
printf 'Verified local repository: %s\n' "$stage"
```

In the **same shell**, review the transaction first:

```bash
sudo xbps-install -i -M -n -R "$stage" "${packages[@]}"
```

Proceed if it selects the four exact beta29_2 packages and leaves unrelated packages alone. If a dependency is missing, resolve it separately from trusted official Void repositories and repeat the dry run. For example, if the plan reports that `libdav1d` is missing or too old, review `sudo xbps-install -S -n libdav1d` and install it from your official Void repository before retrying. Keep the authenticated snapshot for future recovery. [Full user guide](docs/USERS.md)

```bash
sudo xbps-install -i -M -R "$stage" "${packages[@]}"
for name in "${names[@]}"; do
    version=$(xbps-query -p pkgver "$name")
    printf '%s\n' "$version"
    [[ $version == "$name-1.0.0beta29_2" ]]
done
sudo xbps-pkgdb -a
```

## Uninstalling

Stop the Skwd processes you started. Review the dry run before applying the removal. Package removal leaves your personal data in place. [Removal commands](docs/USERS.md#uninstalling)

## Rollback

Keep a verified copy of all four previous packages and the matching index. Review the explicit four-package downgrade before applying it. [Rollback commands](docs/USERS.md#rollback)

## Troubleshooting

If a download fails during Pages propagation, retry the same XBPS command after the origin recovers. If signature or fingerprint errors persist, stop and use the authenticated channel or a verified versioned release. For missing dependencies, review the dry run and use official Void repositories. If Wall cannot start, check your Wayland session, Vulkan driver and Deck IPC. Report reproducible Void packaging issues with the version, compositor and GPU driver. [Support and common checks](docs/USERS.md#troubleshooting)

## Security

Native XBPS uses HTTPS and verifies package signatures with the accepted repository key. It does not verify our detached signed manifest or enforce signed index freshness and replay protection. The authenticated helper verifies `SHA256SUMS.sig` before making the signed index and packages available to XBPS. The manual procedure verifies the full versioned release, including source materials. [Signing and trust model](docs/KEYS.md) · [Stable channel design](docs/STABLE-CHANNEL.md)

## Building from source

The [beta29_2 build and assembly guide](https://github.com/SirOtter0/skwd-wall/blob/release/beta29_2-candidate/docs/void/BETA29-2-REBUILD.md) explains the exact inputs, how Wall was rebuilt, which binaries were reused and how to compare the XBPS output.

## Upstream and maintenance

Skwd-wall is developed by [liixini](https://github.com/liixini/skwd-wall). This is an independent Void port maintained by **SirOtter0**. [Port source and recipes](https://github.com/SirOtter0/skwd-wall/tree/release/beta29_2-candidate) · [Void packaging issue tracker](https://github.com/SirOtter0/skwd-void-repo/issues) · [Upstream handoff](https://github.com/SirOtter0/skwd-wall/blob/release/beta29_2-candidate/docs/void/UPSTREAM.md)
