# Use Skwd-wall beta29_2 on Void Linux

This external community port targets Void Linux x86_64 glibc with runit. Use the [English installation procedure](../README.md#installation) to authenticate the production key, verify `SHA256SUMS.sig`, check the signed hashes and package signatures, and install from the verified local snapshot. The [original installation guide attached to beta29_2](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/BETA29-2-SIGNED-INSTALLATION.md) remains available in Spanish. [Public beta29_2 release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2)

Start Skwd-wall as your desktop user. If Deck is already running in the session, reuse it. [Startup commands](../README.md#running-skwd-wall)

## Updating

Save your Skwd settings and catalogue, retain the complete previous verified XBPS set and stop any Skwd processes you started. Follow [Installation](../README.md#installation) with the intended release. Review the four version-pinned entries in the dry run, apply the coordinated update and run `xbps-pkgdb -a`. Restart Deck and Wall normally from the graphical session.

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

## Rollback

Restore the previous coordinated package set from a verified local snapshot. Authenticate its signed manifest and package signatures when available. For the historical beta29_1 backup, match the whole backup against its original trusted manifest. Keep the current snapshot and back up your data before downgrading.

For **beta29_1**, run the following in Bash. At the prompt, enter the absolute directory containing the verified beta29_1 index and all four XBPS files.

```bash
set -euo pipefail
read -r -p 'Verified beta29_1 repository directory: ' previous
[[ $previous == /* && -f $previous/x86_64-repodata ]]
old=(skwd-wall-v2-local-1.0.0beta29_1 skwd-deck-local-1.0.0beta29_1
     skwd-lens-local-1.0.0beta29_1 skwd-paper-local-1.0.0beta29_1)
sudo xbps-install -i -M -n -f -R "$previous" "${old[@]}"
```

Proceed when the dry run selects precisely those four versions and their dependencies are satisfied. Use the same Bash shell for the downgrade and checks:

```bash
sudo xbps-install -i -M -f -R "$previous" "${old[@]}"
for package in "${old[@]}"; do
    name=${package%-1.0.0beta29_1}
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
