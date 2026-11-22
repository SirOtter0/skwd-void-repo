# Install and maintain Skwd-wall beta29_2

Target: **Void Linux x86_64 glibc with runit**. SirOtter0 maintains this external community port. For package and Void-specific support, use [this repository's issues](https://github.com/SirOtter0/skwd-void-repo/issues). Mention your XBPS version, package revision, compositor and driver, and exclude credentials and personal configuration.

Start with the [public beta29_2 release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2) and follow the [complete authenticated installation guide](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/BETA29-2-SIGNED-INSTALLATION.md). The [public port branch](https://github.com/SirOtter0/skwd-wall/tree/release/beta29_2-candidate) contains the build and packaging recipes.

1. Obtain the production public key. Compare both fingerprints against the independently trusted [historical key record](https://github.com/SirOtter0/skwd-void-repo/blob/97e727af21fe36479402102ea45757d16a672e93/review/production-key.json). The XBPS fingerprint is `cb:49:33:d0:b1:e9:be:a6:3d:85:96:11:04:c4:50:e8`; the SHA-256 SPKI is `3860084bca30b2022dd851490ba2f920524feb1dd38b578f69252e0a76e9d987`.
2. Verify **`SHA256SUMS.sig`** with the authenticated public key. Download and check the exact files named in the manifest, including the index and four `.sig2` signatures. Verify the individual packages. XBPS repository key metadata does not authenticate every byte of the index.
3. Keep the authenticated snapshot together. Follow the guide to dry-run and install the exact beta29_2 versions of Wall, Deck, Lens and Paper from that snapshot. Use this same coordinated process to update, preserving your data and the previous verified distribution. Check each installed version and run `xbps-pkgdb -a`.
4. To uninstall, stop your Skwd processes normally and review a dry run of removing just those four packages. Run the removal and check `xbps-pkgdb -a` and your application data.
5. To roll back, use a verified snapshot of the complete previous set. Dry-run the explicit four-version downgrade from that local snapshot and review the transaction before applying it. Check versions and `xbps-pkgdb -a`. Restore user data only where necessary.

The packages require no automatic service startup or changes to personal Niri or Noctalia settings. Beta29_2 was exercised on Void glibc/runit and on Niri/Wayland with NVIDIA. Musl, other architectures and further GPU/media paths are outside the validated scope.
