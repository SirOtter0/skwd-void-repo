# beta.27 release hold

The owner confirmed successful generation and recovery of the definitive key.
Its public-only identity is in keys/skwd-void-xbps-public.pem and
review/production-key.json. This is not the disposable rehearsal identity.

The port is being integrated independently on integration/void-beta27-20261108.
Do not modify that worktree, finalize a beta.26 production candidate, sign
packages, enable Pages, or deploy while this integration is pending.

The policy package revision and pinned beta.26 source commit currently describe
historical validated evidence, NOT a planned beta.26 public release. Keep that
record until beta.27 has a reviewed replacement. No release gate is enabled.

After the integrating agent reports completion, obtain its public commit, four
coordinated package hashes, corresponding source delivery, dependency provenance,
security-patch disposition, installation/removal and basic functional evidence.
Bind the EXACT new candidate hash and identity only after review; do not carry
beta.26 licensing approval to beta.27 implicitly. Recheck licensing for changed
inputs. Reuse existing tests only where relevant inputs did not change.

The same production key is intended for the reviewed beta.27 release. Encrypted
key loading by native XBPS remains to be confirmed during an owner-authorized
signing operation. Public-key/backup verification alone does not establish it.

## Hosting protection preparation (not applied)

The GitHub connector used here supports Git content operations but does not expose
Pages/environment/ruleset administration. No authenticated administrative settings
change is claimed. An inactive YAML example is not a protected GitHub environment.

Before separately authorizing deployment, the repository owner must configure:

* Protect main against force pushes/deletion and require the infrastructure check.
* Create publication-review and github-pages environments, restricted to main;
  require owner approval where supported by the repository account/plan.
* Keep ENABLE_SIGNED_PUBLICATION unset/false and the deployment example OUTSIDE
  .github/workflows. No automatic publication or production signing credentials.
* Independently announce both public fingerprints and compare the key import
  prompt. Do not distribute private keys or passphrases to GitHub/Actions.
* Only after explicit deployment authorization, enable Pages Actions source and
  review the full signed testing+stable artifact. The proposed endpoint is
  https://sirotter0.github.io/skwd-void-repo/testing/ ; it is not a live install URL.

Deployment/publishing and the upstream PR remain unauthorized.
