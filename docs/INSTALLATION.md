# Install Skwd-wall v2 on Void Linux

Skwd-wall `1.0.0beta29_2` is a community port for Void Linux x86_64 glibc with runit. It requires glibc `2.41_1` or later. Run Wall in a Wayland session with a working Vulkan implementation. The port was tested on Niri with an NVIDIA RTX 4060 Ti.

## Install with native XBPS

Native XBPS is the recommended method. It uses the public HTTPS repository and resolves system libraries through the official Void repositories. Wall installs matching versions of Deck and Paper.

```sh
sudo sh -c 'set -C; printf "%s\n" "repository=https://sirotter0.github.io/skwd-void-repo" > /etc/xbps.d/30-skwd-void.conf' &&
sudo xbps-install -S skwd-wall-v2-local
```

When XBPS asks to import the repository key, accept it only if its fingerprint is `cb:49:33:d0:b1:e9:be:a6:3d:85:96:11:04:c4:50:e8` and matches a reference you trust independently of the download. [Historical production key record](https://github.com/SirOtter0/skwd-void-repo/blob/97e727af21fe36479402102ea45757d16a672e93/review/production-key.json)

The registration command refuses to overwrite an existing file. If the file already contains the native URL, run only the second command. If it selects the authenticated snapshot, follow the [migration procedure](USERS.md#switching-repository-methods) to switch explicitly.

Lens is optional and provides semantic features. Install it from the native repository with:

```sh
sudo xbps-install skwd-lens-local
```

## Update

```sh
sudo xbps-install -Su
```

XBPS refreshes the repository and verifies package signatures. Wall's dependencies keep Deck and Paper on their matching versions. If Lens is installed, XBPS includes it in normal updates.

## Run Skwd-wall

As your regular desktop user, start Deck in a terminal inside the Wayland session if it is not already running:

```sh
skwd-walld
```

In a second terminal in the same session, check the catalogue connection and open Wall:

```sh
skwd-helm list --json
skwd-wall-v2
```

Paper supplies the renderers. Session startup is left to your desktop configuration.

## Authenticated and manual installation

Native XBPS verifies package signatures over HTTPS. The [authenticated channel](../README.md#authenticated-installation) additionally verifies the signed index, checks expiry, and rejects older releases after establishing local state. Users of that method synchronize before running XBPS:

```sh
sudo /usr/local/sbin/skwd-xbps-sync && sudo xbps-install -Su
```

For a specific release, the [manual verification procedure](../README.md#advanced-manual-verification) checks the independently trusted production key, signed manifest, and package signatures before installing from a local snapshot. It also verifies the corresponding-source archive.

## Maintenance and recovery

- [Switch between native and authenticated repositories](USERS.md#switching-repository-methods)
- [Uninstall packages while keeping user data](USERS.md#uninstalling)
- [Restore a previous verified package set](USERS.md#rollback)
- [Recover from trust, dependency, and startup errors](USERS.md#troubleshooting)

[Signed beta29_2 release and original assets](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2)
