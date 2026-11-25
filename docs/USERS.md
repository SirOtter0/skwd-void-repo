# Use Skwd-wall beta29_2 on Void Linux

This external community port targets Void Linux x86_64 glibc with runit. See the [installation methods](../README.md#quick-installation) for native XBPS, the authenticated channel and manual verification. The [original installation guide attached to beta29_2](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/BETA29-2-SIGNED-INSTALLATION.md) remains available in Spanish. [Public beta29_2 release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2)

Start Skwd-wall as your desktop user. If Deck is already running in the session, reuse it. [Startup commands](../README.md#running-skwd-wall)

## Installation and updates

[Quick installation](../README.md#quick-installation) describes the proposed native method. It will be available after Pages activation. Use the [authenticated channel](../README.md#authenticated-installation) or the [advanced manual procedure](../README.md#advanced-manual-verification) in the meantime.

Native users update with `sudo xbps-install -Su`. XBPS resolves the exact Wall dependencies for Deck and Paper and updates Lens if it is installed. For authenticated users, run:

```sh
sudo /usr/local/sbin/skwd-xbps-sync && sudo xbps-install -Su
```

Keep a backup of Skwd settings and catalogue data, and retain a previous verified package set for rollback. If the authenticated origin is unavailable or verification fails, its helper keeps the previous snapshot. Plain XBPS uses that snapshot and continues to use the configured Void repositories for the rest of the system.

## Switching repository methods

Use only one Skwd repository for routine XBPS transactions. Both methods use `/etc/xbps.d/30-skwd-void.conf`. Check for duplicate Skwd declarations in `/etc/xbps.d` and `/usr/share/xbps.d` before switching. Wait for XBPS and synchronization to finish before editing the file.

**Authenticated to native.** This is an explicit choice to use native package signatures without the channel's signed index and freshness checks. After Pages activation, probe the native origin and check its key fingerprint against the independent reference in Quick installation:

```sh
sudo xbps-install -i -R https://sirotter0.github.io/skwd-void-repo -S
sudoedit /etc/xbps.d/30-skwd-void.conf
```

Replace the repository line only if it currently says `repository=/var/lib/skwd-xbps/current`. Set it to `repository=https://sirotter0.github.io/skwd-void-repo`. Keep the helper and its snapshots if you might switch back. Then run `sudo xbps-install -Su`.

**Native to authenticated.** Install and verify the helper as documented, then run `sudo /usr/local/sbin/skwd-xbps-sync` without `--configure` to authenticate a local snapshot. Use `sudoedit /etc/xbps.d/30-skwd-void.conf` to replace the native URL with `repository=/var/lib/skwd-xbps/current`. Use the authenticated update command thereafter. Both migrations keep installed packages and user data. Check any manually configured XBPS holds or repository locks if packages do not move to the selected repository.

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

To remove the Skwd repository, remove its configuration after checking which method it selects. Remove the helper only if you installed it for authenticated updates. The verified snapshots under `/var/lib/skwd-xbps` remain available for recovery.

```sh
sudo unlink /etc/xbps.d/30-skwd-void.conf
# If you installed the authenticated helper and no longer need it:
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
