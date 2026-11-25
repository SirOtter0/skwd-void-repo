# Use Skwd-wall beta29_2 on Void Linux

This external community port targets Void Linux x86_64 glibc with runit. Start with the [installation guide](INSTALLATION.md).

Start Skwd-wall as your desktop user. If Deck is already running in the session, reuse it. [Startup commands](../README.md#running-skwd-wall)

## Installation and updates

The [recommended native installation](INSTALLATION.md#install-with-native-xbps) uses the public repository. The [authenticated channel](../README.md#authenticated-installation) adds signed index and freshness checks. The [advanced manual procedure](../README.md#advanced-manual-verification) verifies a versioned release directly.

Native users update with `sudo xbps-install -Su`. XBPS resolves the exact Wall dependencies for Deck and Paper and updates Lens if it is installed. For authenticated users, run:

```sh
sudo /usr/local/sbin/skwd-xbps-sync && sudo xbps-install -Su
```

Keep a backup of Skwd settings and catalogue data, and retain a previous verified package set for rollback. If the authenticated origin is unavailable or verification fails, its helper keeps the previous snapshot. Plain XBPS uses that snapshot and continues to use the configured Void repositories for the rest of the system.

## Switching repository methods

Use only one Skwd repository for routine XBPS transactions. Both methods use `/etc/xbps.d/30-skwd-void.conf`. Check for duplicate Skwd declarations in `/etc/xbps.d` and `/usr/share/xbps.d` before switching. Wait for XBPS and synchronization to finish before editing the file.

**Authenticated to native.** This is an explicit choice to use native package signatures without the channel's signed index and freshness checks. Probe the native origin and check its key fingerprint against the independent reference in the [installation guide](INSTALLATION.md#install-with-native-xbps):

```sh
sudo xbps-install -i -R https://sirotter0.github.io/skwd-void-repo -S
sudoedit /etc/xbps.d/30-skwd-void.conf
```

Replace the repository line only if it currently says `repository=/var/lib/skwd-xbps/current`. Set it to `repository=https://sirotter0.github.io/skwd-void-repo`. Keep the helper and its snapshots if you might switch back. Then run `sudo xbps-install -Su`.

**Native to authenticated.** Install and verify the helper as documented, then run `sudo /usr/local/sbin/skwd-xbps-sync` without `--configure` to authenticate a local snapshot. Use `sudoedit /etc/xbps.d/30-skwd-void.conf` to replace the native URL with `repository=/var/lib/skwd-xbps/current`. Use the authenticated update command thereafter. Both migrations keep installed packages and user data. Check any manually configured XBPS holds or repository locks if packages do not move to the selected repository.

## Uninstalling

Stop the Skwd processes you started. Review the dry run before removing the packages, and omit `skwd-lens-local` from both commands if it is not installed. Verify package database integrity afterward.

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

Run the following in Bash. Enter the absolute directory containing the verified index and the required packages. Enter the exact version, such as `1.0.0beta29_1` for the historical backup. The command always selects Wall, Deck and Paper at that version. It selects Lens at the same version only if Lens is currently installed.

```bash
set -euo pipefail
read -r -p 'Verified repository directory: ' previous
read -r -p 'Exact package version: ' previous_version
[[ $previous == /* && -f $previous/x86_64-repodata ]]
[[ $previous_version =~ ^1\.0\.0beta[0-9]+_[1-9][0-9]*$ ]]
components=(skwd-wall-v2-local skwd-deck-local skwd-paper-local)
if xbps-query -p pkgver skwd-lens-local >/dev/null 2>&1; then
    components+=(skwd-lens-local)
fi
old=()
for name in "${components[@]}"; do
    old+=("$name-$previous_version")
done
sudo xbps-install -i -M -n -f -R "$previous" "${old[@]}"
```

Proceed when the dry run selects only the listed packages at the exact version and their dependencies are satisfied. If Lens was absent, check that the plan leaves it uninstalled. Use the same Bash shell for the downgrade and checks:

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
- **A system library is missing:** Inspect the XBPS dry run and resolve the dependency from a trusted official Void repository. Keep the installed Skwd packages at the same revision.
- **Wall opens without a catalogue:** Run `skwd-helm list --json` in the same graphical session as Deck. Check that the daemon and picker use the same user and session. Keep one daemon per session.
- **Wall fails to open its surface:** Check your Wayland session and working Vulkan driver. The verified graphical coverage is Niri/Wayland with NVIDIA RTX 4060 Ti.
- **Report a Void packaging issue:** Include package versions, XBPS version, compositor, GPU and driver, and the failing command. Redact credentials and personal paths. [Issue tracker](https://github.com/SirOtter0/skwd-void-repo/issues)

## Historical release attachment

The [original Spanish installation document](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/BETA29-2-SIGNED-INSTALLATION.md) is preserved as released. Follow the [current installation guide](INSTALLATION.md) for new installations.
