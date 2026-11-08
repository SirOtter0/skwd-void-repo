# Skwd-wall v2 for Void Linux

**Unofficial community packaging infrastructure** for [Skwd-wall](https://github.com/liixini/skwd-wall) v2 on **Void Linux x86_64 (glibc + runit)**.

> [!WARNING]
> **Not ready for installation.** No signed repository channel has been published, no release signing key exists, and no public application binaries are distributed by this repository. Do not install packages from placeholder URLs or treat passing CI as release approval.

This repository prepares a separately maintained XBPS distribution workflow. It is **not** an official Void Linux repository or an upstream Skwd release. The port sources are maintained in [SirOtter0/skwd-wall (`feat/void-linux-support`)](https://github.com/SirOtter0/skwd-wall/tree/feat/void-linux-support). No upstream pull request has been opened by this project.

The four prepared revision4 packages preserve the 15 validated executable/library hashes.
A disposable-key private HTTP rehearsal passed installation, upgrade, tamper rejection
and removal. Definitive keys and public binary distribution remain unauthorized.

## Project status

| Area | Status |
| --- | --- |
| Pinned public-source build orchestration | Prepared |
| Package, architecture, dependency and payload checks | Prepared |
| Source and provenance records | Prepared |
| Licensing approval gate | Implemented; revision4 review completed; production candidate review required |
| Offline signing and signed manifest workflow | Prepared; no release key created |
| Testing-to-stable promotion and signed-byte verification | Prepared; no public channel |
| Infrastructure CI | Available; checks passing in the latest reported run (25 local tests) |
| Public binary releases | **Blocked** |
| End-user installation | **Not supported yet** |

The passing test count describes infrastructure checks, **not** complete runtime, graphical, security or distribution acceptance.

## Target platform and packages

- **Distribution:** Void Linux, x86_64 glibc, using runit (not systemd).
- **Desktop target:** Wayland, including Niri; graphical compatibility still requires final validation.
- **Components:** Wall, Deck, Lens and Paper.
- **Local package names:** `skwd-wall-v2-local`, `skwd-deck-local`, `skwd-lens-local`, `skwd-paper-local`.
- **Current reviewed package revision:** `1.0.0beta26_4`.

These are **targets and preparation details**, not a declaration of tested end-user compatibility.

## What is prepared

- Unprivileged offline build orchestration using pinned public port recipes.
- Static package, architecture, dependency and payload inspection.
- Candidate-bound licensing approval gate; compilation never grants distribution clearance.
- Manual offline RSA/XBPS signing and an additional signed release manifest.
- Testing-first promotion with immutable signed-byte verification and explicit stable approval.
- Read-only hosted infrastructure CI; optional ephemeral-VM build workflow disabled by default.
- Pages deployment example, not activated for publication.

## Before the first public release

1. Review the completed [redistribution evidence](docs/REDISTRIBUTION-REVIEW.md) and its documented scope.
2. Review [builder and clean-VM acceptance](docs/BUILD.md), including relevant runtime and graphical checks.
3. Approve the [key ceremony and signing procedure](docs/KEYS.md).
4. Approve [hosting and deployment](docs/HOSTING.md) and configure protected environments.
5. Obtain the repository owner's explicit authorization for the first signed testing publication.
6. Verify the actual public HTTPS repository endpoint and finalize [end-user installation instructions](docs/USERS.md).

`policy/release.json` is intentionally **fail-closed**. Do not remove blockers merely to make CI pass.

## Run infrastructure checks

The following checks do not require release signing keys or installation of XBPS packages:

```sh
python3 -m unittest discover -s tests -v
bash -n scripts/build-candidate.sh
```

They do not replace clean-VM acceptance, licensing clearance or testing on the target desktop.

## Upstream, credits and licensing

Skwd-wall is developed by [liixini](https://github.com/liixini/skwd-wall). This repository is an independent community packaging effort, not an official upstream distribution channel.

Scripts in this repository are MIT-licensed. Upstream code, packages, assets and dependencies retain their respective licenses; see [LICENSE](LICENSE) and [distribution review](docs/LICENSING.md).

Do not commit proprietary models, personal configurations, built application binaries, signing secrets or workstation-specific paths.
