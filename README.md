# Skwd-wall v2 for Void Linux

Community packaging for Skwd-wall on **Void Linux x86_64 glibc/runit**, maintained externally by **SirOtter0**. The current coordinated release is **`1.0.0beta29_2`** and contains Wall, Deck, Lens and Paper.

- [Public beta29_2 release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2)
- [Authenticated installation, update, uninstall and rollback](docs/USERS.md)
- [Public beta29_2 port branch](https://github.com/SirOtter0/skwd-wall/tree/release/beta29_2-candidate)
- [Report a Void packaging issue](https://github.com/SirOtter0/skwd-void-repo/issues)

Verify the production public-key fingerprints and **`SHA256SUMS.sig` before using the index**. The release contains the four XBPS, four `.sig2` files, signed manifest, index, sources and license notices. See [KEYS.md](docs/KEYS.md) for the production identity and signing model.

The public HTTPS release installed from an authenticated local snapshot in a clean Void guest; `xbps-pkgdb -a` passed. Wall also ran in a user-confirmed Niri/Wayland session using NVIDIA RTX 4060 Ti. See the [release notes](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/RELEASE-NOTES.md) for tested limits. This is an independent community port. Upstream Skwd-wall is maintained by [liixini](https://github.com/liixini/skwd-wall).

The repository also retains historical build and publication rehearsal policies. Those older policies are separate from the published beta29_2 release.
