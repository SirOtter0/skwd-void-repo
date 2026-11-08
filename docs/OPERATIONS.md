# Release and channel operations

## Before the first public release

The notice/source work and owner-authorized disposable-key rehearsal are complete;
see STATUS.md and REDISTRIBUTION-REVIEW.md. Still required: explicit owner approval
for definitive-key creation and first testing publication, authenticated production
fingerprints/backup ceremony, exact candidate/provenance review and protected HTTPS
publication settings. No signing/publishing secret is configured in CI.

No deployment runs merely because this repository is updated.
Only infrastructure checks run on hosted PR runners. No application code runs on
PR events and no job has a signing secret. No workflow_run/pull_request_target
handoff accepts untrusted build artifacts into a privileged signer.

## Planned authorized procedure

1. Complete notices/attribution/source review, update pinned port/revision if
   necessary, then build a fresh local candidate in a disposable VM. Use the exact
   sources/patches and published scripts. Record tool versions and source hashes.
2. Install/run/remove the new coordinated archives in a separate clean VM; retain
   acceptance receipts. Inspect candidate source delivery for credentials, private
   paths, unknown vendor rights and missing native/asset sources.
3. Approve that EXACT candidate.json digest and licensing evidence in policy. A
   changed candidate requires fresh approval; compilation never clears licensing.
4. After owner authorization, sign offline per KEYS.md. `repository.py verify`
   requires an independently authenticated SHA256 public-key identity.
5. Prepare a new local testing directory using `repository.py promote SIGNED NEW
   --channel testing`. It verifies signed files and performs no network operation.
6. Assemble a complete site bundle with testing and, if already deployed, the
   unchanged stable channel. No symlinks, devices, executable hooks or unrelated
   files are allowed. Preserve immutable historical releases/rollback archives.
7. After explicit publication approval, configure protected publication-review
   and github-pages environments, Pages Actions deployment and the approved public
   key fingerprint. Review/enable the inactive deployment workflow example and
   ENABLE_SIGNED_PUBLICATION. No automatic source-building job gets write access.
8. Run the publication workflow manually with a reviewed public HTTPS bundle URL
   and exact SHA256. `fetch-site.py` limits download/extracted size, rejects unsafe
   members, verifies all channel hashes/package signatures and signed index/source
   metadata, and fails if an existing stable channel would disappear. It never
   executes package content or installs packages.
9. Download the actual public metadata/signatures/key/index/packages, verify all
   signatures/hashes and perform XBPS remote import/install/remove in a disposable
   VM. Check the exact native fingerprint prompt, dependency resolution and that
   services/settings are untouched. Only then write real user installation URLs.
10. After testing acceptance, promote the SAME signed bytes to stable using
    `--channel stable --accept-tested-release`. Record its exact candidate digest
    as stable_approved_candidate_sha256 in policy. Include both channels in the
    next verified site bundle. Promotion must not recompile/re-sign packages.

Production-environment gates and platform settings are not configured by merely
committing a YAML file. Ensure required reviewers, no self-approval where possible,
protected main branch, minimal tokens, and immutable reviewed workflow revisions.

## Updates / rollback

A public package filename/version is immutable. Bump all coordinated revisions for
changed contents, retain previous packages/signatures/source and test both upgrade
and downgrade paths. Publish new signatures/assets before replacing the index and
keep packages referenced by recently cached indices. A Pages deployment is a full
site replacement; downloading/assembling both verified channels is mandatory.

Rollback redeploys the previously archived complete signed site, then verifies its
public endpoint. Explain the deliberate old release to users; stock XBPS cannot
by itself prevent repository replay/freeze. Key compromise requires the separately
authenticated rotation procedure, not just republishing with the same key.
