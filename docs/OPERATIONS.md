# Release and channel operations

The signed [beta29_2 GitHub release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2) is the immutable source of the native Pages repository and the authenticated channel. See the [user guide](USERS.md) for installation and recovery. Production signing and publishing require separate owner approval.

## Publish a coordinated version

1. Build and test Wall, Deck, Paper, and Lens in isolated Void guests. Check installation with official dependencies, coordinated updates and rollback. Review corresponding sources and licenses before signing. Keep Wall's exact Deck and Paper pins and keep Lens optional.
2. Sign the approved XBPS packages and release manifest offline with the existing production key. Verify the package signatures, index and manifest against the independent public identity. Keep the private key outside CI. [Signing procedure](KEYS.md)
3. Publish the versioned GitHub release with the four packages, their signatures, the index, the signed manifest, corresponding sources and notices. Verify anonymous HTTPS access and the signed digests before promoting it.
4. Append the reviewed version and manifest SHA-256 to [the Pages policy](../policy/native-pages.json). Use a new package version for any changed package bytes. Retain earlier policy entries while clients may still use their indexes.
5. Review the staged artifact and dispatch the [native Pages workflow](https://github.com/SirOtter0/skwd-void-repo/actions/workflows/native-xbps-pages.yml) manually from reviewed `main`. After assembly succeeds, an authorized reviewer approves the complete artifact in the protected `github-pages` environment. [Deployment procedure](NATIVE-XBPS.md#deployment-after-approval)
6. Separately prepare and sign the authenticated channel payload using the next sequence number. Verify its manifest binding and expiry before publishing the signed envelope. Renew the metadata before expiry even when the package version stays the same. [Authenticated channel procedure](STABLE-CHANNEL.md#maintainer-procedure)
7. Fetch and verify the public Pages files against the release. In a clean Void VM, check native installation and `xbps-install -Su` with official Void repositories. Verify the authenticated synchronization path independently, including the signed index, versions and sequence. Record the workflow and test results before announcing the version.

## Retention, propagation and rollback

The complete Pages artifact is capped at 900 MB against the 1 GB site limit. Track the 100 GB/month soft bandwidth limit and keep the site within the 10-minute deployment timeout. Keep old packages and their signatures on Pages long enough for cached indexes to resolve. CDN propagation can temporarily expose an index ahead of its packages. Retry after propagation and confirm that the package files and signatures match the approved release.

Keep historical versioned releases and their matching indexes for an explicit [client rollback](USERS.md#rollback). Pick the verified older set and dry-run a coordinated downgrade. Simply restoring an older index does not downgrade installed packages. The authenticated channel rejects decreasing release versions or sequence numbers, including during a native recovery. Handle a signing-key incident using the independently authenticated [rotation procedure](KEYS.md#rotation-and-incident-response). [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
