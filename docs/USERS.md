# Use Skwd-wall beta29_2 on Void Linux

This external community port targets Void Linux x86_64 glibc with runit. Use the [installation guide](../README.md#advanced-verified-installation) to authenticate the production key, verify `SHA256SUMS.sig`, check the signed hashes and package signatures, and install from the verified local snapshot. The [original installation guide attached to beta29_2](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/BETA29-2-SIGNED-INSTALLATION.md) remains available in Spanish. [Public beta29_2 release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2)

Start Skwd-wall as your desktop user. If Deck is already running in the session, reuse it. [Startup commands](../README.md#running-skwd-wall)

## Stable channel

Follow [Quick installation](../README.md#quick-installation) to register the authenticated local snapshot. To retrieve a new version and apply regular Void updates:

```sh
sudo /usr/local/sbin/skwd-xbps-sync && sudo xbps-install -Su
```

When the server is unavailable or authentication fails, the helper leaves the last verified snapshot in place. `xbps-install -Su` alone uses that snapshot for Skwd and continues to use the configured Void repositories for the rest of the system. For rollback, retain a previous `snapshot-*` under `/var/lib/skwd-xbps` and use the explicit four-package procedure below. Keep the active snapshot and its channel metadata to preserve the replay check.

## Updating

Save your Skwd settings and catalogue, retain the complete previous verified XBPS set and stop any Skwd processes you started. Follow [Advanced verified installation](../README.md#advanced-verified-installation) with the intended release. Review the four version-pinned entries in the dry run, apply the coordinated update and run `xbps-pkgdb -a`. Restart Deck and Wall normally from the graphical session.

## Uninstalling

Stop the Skwd processes you started. Review the dry run first, then remove the four packages and verify package database integrity.

```sh
sudo xbps-remove -n skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
```

```sh
sudo xbps-remove skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
sudo xbps-pkgdb -a
```

Your configuration, catalogue and cache remain in your user directories.

To stop using the stable channel, remove its XBPS configuration and its helper if you installed them with Quick installation. The verified snapshots under `/var/lib/skwd-xbps` remain available for recovery.

```sh
sudo unlink /etc/xbps.d/30-skwd-void.conf
sudo unlink /usr/local/sbin/skwd-xbps-sync
```


## Rollback

Restore the previous coordinated package set from a verified local snapshot. Authenticate its signed manifest and package signatures when available. For the historical beta29_1 backup, match the whole backup against its original trusted manifest. Keep the current snapshot and back up your data before downgrading.

Run the following in Bash. Enter the absolute directory containing the verified index and all four packages. Enter the exact version, such as `1.0.0beta29_1` for the historical backup.

```bash
set -euo pipefail
read -r -p 'Verified repository directory: ' previous
read -r -p 'Exact package version: ' previous_version
[[ $previous == /* && -f $previous/x86_64-repodata ]]
[[ $previous_version =~ ^1\.0\.0beta[0-9]+_[1-9][0-9]*$ ]]
old=()
for name in skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local; do
    old+=("$name-$previous_version")
done
sudo xbps-install -i -M -n -f -R "$previous" "${old[@]}"
```

Proceed when the dry run selects precisely those four versions and their dependencies are satisfied. Use the same Bash shell for the downgrade and checks:

```bash
sudo xbps-install -i -M -f -R "$previous" "${old[@]}"
for package in "${old[@]}"; do
    name=${package%-$previous_version}
    version=$(xbps-query -p pkgver "$name")
    printf '%s\n' "$version"
    [[ $version == "$package" ]]
done
sudo xbps-pkgdb -a
```

Package rollback leaves your user data in place. Restore it from your backup where appropriate. If older packages need unsupported system library versions, recover from a known-good system or VM snapshot.

## Troubleshooting

- **Trust or integrity check fails:** Stop before installation. Recheck the production fingerprints independently and download the exact versioned snapshot again.
- **A system library is missing:** Inspect the XBPS dry run and resolve the dependency from a trusted official Void repository. Keep all four Skwd packages at the same revision.
- **Wall opens without a catalogue:** Run `skwd-helm list --json` in the same graphical session as Deck. Check that the daemon and picker use the same user and session. Keep one daemon per session.
- **Wall fails to open its surface:** Check your Wayland session and working Vulkan driver. The verified graphical coverage is Niri/Wayland with NVIDIA RTX 4060 Ti.
- **Report a Void packaging issue:** Include package versions, XBPS version, compositor, GPU and driver, and the failing command. Redact credentials and personal paths. [Issue tracker](https://github.com/SirOtter0/skwd-void-repo/issues)
