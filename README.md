# Skwd-wall v2 for Void Linux

## Overview

Skwd-wall **`1.0.0beta29_2`** is a coordinated community release of Wall, Deck, Lens and Paper. SirOtter0 maintains the Void packaging externally. [Download beta29_2](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2)

## Compatibility

- **System:** Void Linux **x86_64 glibc**, with runit. The packages require glibc `2.41_1` or newer.
- **Desktop:** Start Wall and Deck as your regular user inside a Wayland session. Wall requires a working Vulkan implementation. The port was tested on Niri with NVIDIA RTX 4060 Ti. Musl, other architectures and additional GPU and media paths remain outside the verified scope.
- **Runtime dependencies:** A working Wayland/Vulkan stack plus `alsa-lib`, `fontconfig`, `freetype`, `libdav1d`, `libdrm`, `libgcc`, `libglvnd`, `libva`, `libxkbcommon`, `shaderc`, `vulkan-loader`, `wayland` and `zlib`. The package dry run checks the exact requirements. [Signed dependency inventory](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/LICENSE-INVENTORY.json)

## Installation

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

## Updating

Back up your Skwd data and keep the previous verified package set. Repeat [Installation](#installation) with the new release's authenticated snapshot and all four exact versions. [Update instructions](docs/USERS.md#updating)

## Uninstalling

Stop the Skwd processes you started. Review the dry run before applying the removal. Package removal leaves your personal data in place. [Removal commands](docs/USERS.md#uninstalling)

## Rollback

Keep a verified copy of all four previous packages and the matching index. Review the explicit four-package downgrade before applying it. [Rollback commands for beta29_1](docs/USERS.md#rollback)

## Troubleshooting

For a signature or fingerprint mismatch, stop and obtain a fresh copy from the versioned release. For missing dependencies, review the dry run and use official Void repositories. If Wall cannot start, check your Wayland session, Vulkan driver and Deck IPC. Report reproducible Void packaging issues with the version, compositor and GPU driver. [Support and common checks](docs/USERS.md#troubleshooting)

## Security and signing

Verify **`SHA256SUMS.sig` before using the index**. XBPS key metadata identifies the repository key. The additional signed manifest authenticates the index contents, the packages and the source material. Keep installation tied to the verified local files. [Signing and trust model](docs/KEYS.md)

## Building from source

The [beta29_2 build and assembly guide](https://github.com/SirOtter0/skwd-wall/blob/release/beta29_2-candidate/docs/void/BETA29-2-REBUILD.md) explains the exact inputs, how Wall was rebuilt, which binaries were reused and how to compare the XBPS output.

## Upstream and maintenance

Skwd-wall is developed by [liixini](https://github.com/liixini/skwd-wall). This is an independent Void port maintained by **SirOtter0**. [Port source and recipes](https://github.com/SirOtter0/skwd-wall/tree/release/beta29_2-candidate) · [Void packaging issue tracker](https://github.com/SirOtter0/skwd-void-repo/issues) · [Upstream handoff](https://github.com/SirOtter0/skwd-wall/blob/release/beta29_2-candidate/docs/void/UPSTREAM.md)
