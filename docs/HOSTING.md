# Release hosting

## Current public origin

The [versioned GitHub release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2) serves beta29_2 over HTTPS. Anonymous downloads and XBPS access to the release asset prefix were checked. Users should follow the [installation guide](../README.md#advanced-verified-installation) and install from the authenticated local snapshot after verifying `SHA256SUMS.sig`. This release uses GitHub Releases.

## Stable channel

Keep packages and corresponding sources on versioned GitHub Releases. A signed channel file on the default branch selects one release, and a local helper authenticates it before exposing the index to XBPS. [Stable channel design and promotion procedure](STABLE-CHANNEL.md)

## Proposed native repository

The proposed GitHub Pages origin is an additional installation option. It would reuse the versioned release's signed package bytes and index. [Native hosting, policy and deployment](NATIVE-XBPS.md)
