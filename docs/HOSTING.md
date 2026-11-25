# Release hosting

## Versioned releases

The [versioned GitHub release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2) serves beta29_2 over HTTPS. Anonymous downloads and XBPS access to the release asset prefix were checked. Use the [manual verification guide](../README.md#advanced-manual-verification) to install a specific release from a verified local snapshot.

## Stable channel

Keep packages and corresponding sources on versioned GitHub Releases. A signed channel file on the default branch selects one release, and a local helper authenticates it before exposing the index to XBPS. [Stable channel design and promotion procedure](STABLE-CHANNEL.md)

## Native repository

GitHub Pages is the default package repository. It serves the versioned release's existing signed package bytes and index at the public XBPS origin. [Native hosting, policy and deployment](NATIVE-XBPS.md)
