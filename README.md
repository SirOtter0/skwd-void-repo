# Skwd Void community repository — preparation

Infrastructure for an **unofficial** XBPS binary distribution of Skwd-wall v2 for
**Void Linux x86_64 glibc + runit**. Independent of official Void repositories and
upstream Skwd releases. No upstream PR is opened by this project.

**No signed channel is published. No release key exists. Do not install from a
placeholder URL.** Binary distribution remains blocked by the licensing review;
the current workflows do not publish or upload application binaries.

The pinned public port is
[SirOtter0/skwd-wall](https://github.com/SirOtter0/skwd-wall/tree/feat/void-linux-support).
Four compatible package names are preserved: skwd-wall-v2-local, skwd-deck-local,
skwd-lens-local, skwd-paper-local (current reviewed revision1.0.0beta26_3).

## Prepared

* Public-source, unprivileged offline build orchestration using pinned port recipes.
* Static package/architecture/dependency/payload checks and source/provenance records.
* Candidate-bound licensing approval gate; no automatic clearance from compilation.
* Manual offline RSA/XBPS signing and an additional signed release manifest.
* Testing-first local promotion, immutable signed-byte verification and stable approval.
* Read-only hosted infrastructure CI; optional disabled ephemeral-VM build workflow.
* Pages deployment example kept inactive outside the workflow directory.

## Review before first publication

1. Complete [distribution licensing/notices/source review](docs/LICENSING.md).
2. Review the [builder and clean VM acceptance](docs/BUILD.md).
3. Approve the [key ceremony and signing procedure](docs/KEYS.md).
4. Approve [hosting and deployment](docs/HOSTING.md), configure protected environments.
5. Obtain the owner's explicit authorization to publish the first signed testing channel.
6. Verify the actual public HTTPS endpoint, then complete [installation documentation](docs/USERS.md).

`policy/release.json` is intentionally fail-closed. Never remove blockers merely
to make CI green. The verifier tests can run without keys or XBPS installation:

```
python3 -m unittest discover -s tests -v
bash -n scripts/build-candidate.sh
```

No proprietary models, personal configurations, binaries, signing secrets or
workstation paths belong in Git. Scripts here are MIT; upstream packages, sources,
assets and dependencies retain their respective licenses. See LICENSE.
