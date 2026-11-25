# Release status

## Current public release

[beta29_2](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2) is public and production-signed for Void Linux x86_64 glibc/runit. Anonymous HTTPS downloads, the signed manifest and all four package signatures were verified. A clean Void VM installed all four packages from an authenticated local snapshot and passed `xbps-pkgdb -a`. Wall rendered under Niri/Wayland with NVIDIA RTX 4060 Ti. See the [installation guide](../README.md#advanced-verified-installation) and the [scope of the build verification](https://github.com/SirOtter0/skwd-wall/blob/release/beta29_2-candidate/docs/void/BETA29-2-REBUILD.md).

## Historical preparation result — 2026-11-08

| Area | State |
|---|---|
| Four packages | Legal revision1.0.0beta26_4 prepared locally;15 ELF hashes unchanged |
| License/NOTICE/asset attribution | Completed for reviewed runtime configuration; evidence in REDISTRIBUTION-REVIEW.md |
| Sources | Complete local source/recipe delivery;45,595 vendor files verified; four offline/frozen metadata checks pass |
| Optional Steam SDK | No native SDK files present; unused wrappers retained; zero exclusions recorded |
| FFmpeg | IJG/native notices, exact source/configuration/build/change/relink information supplied |
| Independent compilation/graphics | Previous successful results reused; no unchanged build or graphical test repeated |
| Disposable RSA/XBPS signing | PASS: native signatures and additional signed index/source manifest |
| Remote clean-client acceptance | PASS: key fingerprint, install, update simulation/application, hash/signature checks |
| Tamper rejection | PASS: altered archive and invalid signature each rejected; installed bytes unchanged |
| Removal | PASS: four packages, test repo config and key trust removed; services unchanged; package DB clean |
| Definitive key / public binaries / Pages | CREATED; encrypted backups recovered / NOT PUBLISHED / NOT ACTIVATED |
| Upstream PR | NOT OPENED |

Both private test VMs are shut down. Experimental private key was only in tmpfs
and is absent. No personal credentials, host configuration or system packages were
changed. Private raw evidence/artifacts remain outside Git; review/rehearsal-results.json
contains the public, explicitly TEST-ONLY summary and hashes.

Definitive key ceremony completed; public identity is recorded in review/production-key.json.
Exact production-candidate review, authorization to sign/publish, protected hosting
and public HTTPS verification remain required.

### beta.27 handoff

Release preparation is paused for the independent beta.27 integration. The pinned
beta.26 evidence remains historical; no beta.26 final candidate or new signing is
approved. See BETA27-HANDOFF.md for the next review and protection requirements.
