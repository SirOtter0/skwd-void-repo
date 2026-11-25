# Native XBPS repository

The native XBPS origin is `https://sirotter0.github.io/skwd-void-repo/`. It serves [x86_64-repodata](https://sirotter0.github.io/skwd-void-repo/x86_64-repodata) and the eight package and signature files. The directory URL itself returns 404 in a browser because the repository has no homepage. The authenticated channel remains available. [Installation methods](../README.md#quick-installation)

## Hosting and trust

GitHub Pages can serve a flat index and binary packages over HTTPS. Use the artifact workflow to keep large binaries out of Git. The beta29_2 site is 91,399,323 bytes. Public GitHub Pages has no additional hosting charge under the free plan. The published-site limit is 1 GB, the soft bandwidth limit is 100 GB per month, and Pages deployments time out after 10 minutes. At today's full-suite size, 100 GB is roughly 1,090 downloads before retries and index traffic. The builder caps the site at 900 MB. Standard Actions runners for public repositories are free, subject to service limits. [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) · [Actions limits](https://docs.github.com/en/actions/reference/limits)

A versioned Releases asset prefix works over HTTPS for one release and is retained for rollback. Using `latest/download` as the repository leaves clients fetching files independently across release changes. Prefer Pages for stable paths and old-file retention. If traffic outgrows Pages, use a static HTTPS mirror with the same flat layout and review its costs before provisioning. No custom domain, redirect layer or sync service is needed.

XBPS checks HTTPS and verifies native package signatures with the accepted RSA key. The repo fingerprint is `cb:49:33:d0:b1:e9:be:a6:3d:85:96:11:04:c4:50:e8`. Compare it against a trusted source. Native clients do not check `SHA256SUMS.sig`, independently authenticate all index bytes, or enforce expiry or replay protection. The deployment job does verify the signed manifest, index and package bytes, and pins SPKI SHA-256 `3860084bca30b2022dd851490ba2f920524feb1dd38b578f69252e0a76e9d987` for both copies of the public key. This protects assembly. See the [authenticated channel](STABLE-CHANNEL.md) for client-side index authentication and freshness checks. [Void signing documentation](https://docs.voidlinux.org/xbps/repositories/signing.html)

## Deployment after approval

1. Verify the versioned release and its signed manifest. Keep its existing signatures and metadata. Add the reviewed version and signed manifest digest to [the release policy](../policy/native-pages.json). Entries are ordered oldest first. Keep prior entries in the policy while clients may still carry their indexes. Do not republish a package filename with different bytes.
2. Run the assembly on the reviewed branch using Python 3.14 and OpenSSL:

   ```sh
   python3 scripts/build-native-pages.py policy/native-pages.json pages-site
   ```

   Use a new output path. The builder verifies the exact four x86_64 versions in each index, the Wall dependency pins and optional Lens, the index key and the SHA-256 and RSA signatures of each package. It exposes the completed directory only after all releases pass. The site includes the newest `x86_64-repodata` at the root and retains older XBPS files and their signatures alongside it. Sources, notices, signed manifests and historical indexes remain in each versioned release.
3. Dispatch the [native Pages workflow](https://github.com/SirOtter0/skwd-void-repo/actions/workflows/native-xbps-pages.yml) manually from reviewed `main` after release approval. Keep Pages on the Actions source and `ENABLE_NATIVE_XBPS_PAGES=true`. Keep `github-pages` restricted to `main`, require an authorized reviewer, and keep administrator bypass disabled. Approve the deployment after the assembly job passes. The workflow serializes deployments and holds Pages and OIDC write permissions only in the protected deployment job. [Custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) · [Deployment environment protection](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
4. Before announcing native installation, verify TLS and direct asset requests at the real Pages origin. Compare all nine published files, including the index, against the authenticated release. Run Quick installation, Lens installation and plain `xbps-install -Su` in a fresh Void VM. Check all selected versions and `xbps-pkgdb -a`.

The artifact is a complete deployment. CDN edge caches may still expose different generations briefly. Keeping old package filenames and signatures on the origin allows older indexes to remain usable. During propagation a newer index may still encounter a missing file. Retry after the edge catches up. Keep historical releases for intentional rollback. Prune retained Pages files only after reviewing the cache window and available rollback releases. If the site approaches its size limit before old releases can be pruned, move to a larger mirror.

## Void VM validation procedure

Run the native suite with QEMU, the XBPS tools, OpenSSL, Python and `mkisofs`. Use a disposable overlay based on a Void x86_64 glibc guest with Python and a serial login helper:

```sh
python3 tests/run-channel-vm.py --native \
  --base /path/to/void.qcow2 --console /path/to/guest-console.py
```

The suite uses a private TLS origin and disposable signing keys. It substitutes a separate local HTTPS fixture for the official Void mirrors to check dependency resolution across repositories. The actual production Pages origin, CDN behavior and live Void dependency resolution with Pages are post-deployment checks.

The 2026-11-25 Void VM run passed key confirmation, registration with overwrite protection, Wall with Deck/Paper and a separate dependency repository, optional Lens, stale metadata, signed-package rejection, interrupted downloads, an unavailable origin, missing packages with a newer index, coordinated `-Su`, rollback and migration in both directions. After the deliberately damaged cache sequence, XBPS discarded invalid bytes and the next plain `-Su` completed the update. The authenticated helper continued to verify and reuse its snapshot. All 38 repository tests passed.

The real beta29_2 Pages artifact was assembled using the public release and reproduced byte for byte from the local verified copy. A modified test index was rejected before the output directory was activated. The [first production deployment](https://github.com/SirOtter0/skwd-void-repo/actions/runs/45684831685) passed assembly and reviewer-gated deployment. All nine direct HTTPS responses matched the signed release. A clean Void VM installed Wall, Deck and Paper from Pages, resolved system dependencies from official Void repositories, installed Lens separately and passed plain `xbps-install -Su`, repeated index sync, package integrity, runtime smoke tests and explicit migration in both directions. The newer-version discovery test used disposable keys and packages in the lab.
