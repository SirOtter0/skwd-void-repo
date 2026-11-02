# Hosting proposal — no package channel deployed

Use GitHub Pages initially for two small flat HTTPS XBPS channels: testing and
stable. They are proposed directory names, not live repository URLs. Do not print
or install a repository configuration until the actual deployment exists and its
signed content has been downloaded/verified from the public endpoint.

The four inspected packages total 81,633,615 bytes. Two copies plus corresponding
source delivery can fit initially under Pages' 1GB published-site ceiling. Keep
binaries OUT of Git: deploy a reviewed Pages artifact. Do not assume unlimited
bandwidth: Pages has a soft 100GB/month limit (roughly 1,200 full-suite downloads
before source traffic/updates). Monitor actual source-bundle size, channel size,
availability and bandwidth. Enforce a conservative 900MB site ceiling.

Use immutable GitHub Releases for archive history, exact corresponding source,
provenance and signature receipts; each release asset must be <2GiB. Keep prior
coordinated releases for rollback. Do not make testing/stable aliases refer to
independently updated companion packages. Promote the exact validated signed
bytes; never rebuild between testing and stable.

Pages is adequate for a small community trial, not a guaranteed high-traffic
package mirror. If size/traffic makes it unsuitable, move the same signed static
tree to HTTPS object storage/CDN (for example an owner-controlled S3-compatible
bucket with versioning). Review cost, access policy and domain/key announcements
before provisioning anything. Neither a bucket nor a billing service is created.

Publication must preserve both channels, publish assets/signatures before making
a new index visible, retain old package files for clients with cached indices,
and keep immutable release snapshots. Never overwrite an existing published
package filename with different bytes: bump all coordinated package revisions.
Pages artifact deployment replaces the site, so ALWAYS assemble/verify the full
site including the unchanged stable channel before deploying a testing update.
A short CDN/cache transition can still occur; signatures make bad mixes fail.

The example Pages workflow is outside .github/workflows and cannot run until the
owner reviews/enables it. No deploy credential, Pages configuration or production
environment is set up automatically.

References:
[Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits),
[Releases limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases),
[Actions security](https://docs.github.com/en/actions/reference/security/secure-use).
