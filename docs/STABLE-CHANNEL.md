# Authenticated XBPS stable channel

The stable channel is [stable/channel.json](https://raw.githubusercontent.com/SirOtter0/skwd-void-repo/main/stable/channel.json) on the distribution repository's default branch. Sequence 1 points to the [versioned beta29_2 release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2) and expires on 2027-01-24 at 17:34:30 UTC. Renew before expiry with a higher sequence. Reuse the same manifest when the packages stay the same.

## Hosting

| Option | XBPS and maintenance | Decision |
| --- | --- | --- |
| GitHub Releases + signed channel + local synchronization | Keep versioned assets on Releases. Publish one small signed file in Git. Each client registers an atomic local snapshot with XBPS. | Recommended. No added hosting cost or service. |
| GitHub Pages | Can serve a normal HTTPS XBPS repository. The stable site needs coordinated promotion of packages and index and would still need client-side manifest verification. | A mirror if needed. GitHub Free supports public Pages sites with a 1 GB published-site limit and a soft limit of 100 GB per month. |
| GitHub Releases directly | XBPS can read the versioned asset prefix. The `latest/download` prefix resolves each asset separately and does not pin them to the same release during an update. XBPS does not check the detached manifest. | Keep versioned Releases as storage. |
| Vercel or another static host | Same native XBPS and manifest constraints as Pages, plus deployment and quota management. Vercel's Hobby CLI source limit is 100 MB, below the current source asset size. | No deployment required. |

The four beta29_2 XBPS are about 87 MiB together. Its source archive is about 177 MiB. GitHub Releases allows files below 2 GiB. Clients on the quick path download the authenticated index, four packages and their signatures. Sources and the full manifest remain on the versioned release. [GitHub Releases limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) · [Asset links](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases) · [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) · [Vercel limits](https://vercel.com/docs/limits)

## Trust and recovery

- TLS uses normal certificate and hostname verification. The helper pins the historical SPKI SHA-256 `3860084bca30b2022dd851490ba2f920524feb1dd38b578f69252e0a76e9d987` and expects XBPS fingerprint `cb:49:33:d0:b1:e9:be:a6:3d:85:96:11:04:c4:50:e8`. Verify both against an independent reference.
- The channel envelope contains the exact JSON payload and detached signature as base64. The signed payload binds the release tag and package version to a SHA-256 manifest, sequence and expiry. The helper verifies the detached release manifest, hashes of every installed asset, all four XBPS package signatures and the four exact index entries. Local XBPS repositories do not require signature verification. The helper checks the native package signatures before handing the repository to XBPS. The bootstrap asks the user to check and import that same key through XBPS against the already authenticated local snapshot. The native HTTPS probe is a separate interoperability check. [Void repository signing](https://docs.voidlinux.org/xbps/repositories/signing.html)
- XBPS 0.60.7 previously accepted altered index contents when the archive retained its trust metadata. Repository key metadata identifies a signer. The signed SHA-256 binds the exact index bytes. Native XBPS sync does not call the helper or verify this detached manifest.
- The helper validates the root-owned directory chain, locks concurrent synchronization, and switches the `current` pointer atomically only after the complete snapshot passes verification. On a network or signature error the former snapshot remains selected. Avoid running XBPS concurrently with a refresh. The normal update recipe chains the two commands with `&&`.
- A lower channel sequence or package version is refused. A repeated sequence must have exactly the same signed payload. Reusing a package version with a different manifest is refused. A new installation can accept a previously signed release within its validity window. This also applies if an administrator restores older local state. Expiry depends on an accurate UTC system clock and is checked again at activation. If metadata is not yet valid, check the system clock before retrying. After an outage, retry against the same endpoint. If the outage lasts past expiry, wait for a signed renewal. A network attacker can withhold updates. The sync step refuses expired metadata. Plain XBPS keeps access to the local snapshot and does not check channel freshness.
- Keep at least one older verified snapshot for a deliberate rollback. Run the four exact versions with `xbps-install -i -R /path/to/snapshot -n -f ...`, review the transaction, and rerun without `-n`. The active channel stays at its high-water mark. The next normal update can reapply the newer release. Back up user data separately for changes in application data formats. [User guide](USERS.md#rollback) · [Void downgrade documentation](https://docs.voidlinux.org/xbps/advanced-usage.html)
- Key rotation requires a separately authorized bootstrap with an independently announced new SPKI/hash and XBPS fingerprint. Publish the transition through the trusted channel when the old key is available. If it is compromised, use an independent trusted announcement, stop synchronization, and distribute the reviewed replacement helper. The existing helper never accepts a different key at a prompt.

## Coordinating packages

The beta29_2 Wall index requires the exact matching versions of Deck and Paper. Lens is optional for runtime and has no version pin to Wall. The stable channel requires one snapshot with all four names and one version. It rejects missing exact Deck/Paper pins in Wall and required Lens dependencies in the three core packages. A standard upgrade considers all four installed packages, including Lens. Holding or explicitly selecting a subset can keep an independent Lens behind, and Wall's exact dependencies prevent mixing the Deck/Paper versions that Wall requires. Existing beta29_2 packages need no changes. For a future release that requires all four to move together, an optional `skwd-wall` metapackage with exact dependencies can make the supported complete installation explicit. Wall-only installation can keep Lens optional. Test holds, transitions and dependency resolution before adding the metapackage.

## Maintainer procedure

1. Build and test the next version in isolated Void with both fresh installation and upgrading from the previous version. Build, test and promotion should have separate approval points. GitHub Actions can build and verify public inputs and produce an unsigned artifact. It does not need production signing credentials or release-write permission.
2. With explicit owner approval, sign the XBPS and manifest on the offline signing machine. Verify the signed set and publish the versioned release first. Confirm unauthenticated HTTPS downloads before notifying channel clients.
3. Create the payload in a fresh staging directory using the final release manifest and a sequence greater than all previously issued values. The first beta29_2 promotion can use `1` if no channel has ever been published. The helper emits metadata valid for 60 days. Renew before expiry with a new sequence and the same manifest when no packages have changed.

```sh
python3 scripts/channel-envelope.py prepare 1.0.0beta29_2 1 /path/to/verified/SHA256SUMS /path/to/stage/channel.payload
```

4. Only on the approved offline signer, in an interactive terminal, review the payload and its manifest hash, then sign it with the existing key. OpenSSL prompts for the encrypted key's passphrase. Retain the private key on the signing machine.

```sh
openssl dgst -sha256 -sign /offline/path/to/existing-xbps-key.pem \
    -out channel.sig channel.payload
```

5. Back in the staging directory, wrap the signature and verified payload. Review the exact response and helper hash independently. After approval, land the reviewed scripts, documentation and `stable/channel.json` together on `main`, where the client fetches them. Remove the pending-activation notice in the same change. Include only approved documentation, scripts and the signed envelope. Keep the staging directory and private files off the remote. From a clean Void VM, fetch the public helper and channel, run Authenticated installation and the documented authenticated update command, then check the four package versions and `xbps-pkgdb -a` before announcing the channel.

```sh
python3 scripts/channel-envelope.py pack /path/to/stage/channel.payload \
    /path/to/stage/channel.sig /path/to/verified/xbps-public.pem /path/to/stage/channel.json
```

For future releases, update the stable file only after all the signed release assets are reachable. A failed download or stale mixed CDN response is rejected, allowing the user to retry. Preserve versioned releases used for recovery.

## Isolated integration test

Use a clean x86_64 glibc Void guest with Python, OpenSSL and XBPS, and a serial helper for that guest. The host test runner needs Python, OpenSSL, XBPS tools, QEMU and `mkisofs`. It creates a new qcow2 overlay and leaves the existing base and snapshots intact. The test TLS server binds to loopback and the guest uses a private lab trust anchor. The test packages carry only marker files and reproduce the relevant package names and version pins.

```sh
python3 tests/run-channel-vm.py \
    --base "$void_guest_base" --console "$guest_serial_helper" --output "$lab_output"
```

A fresh run prints its artifact directory. Read `guest.log` and `guest.exit` for the staged update, rejection, rollback and native signature checks. The current release was audited separately using its production public key and the existing signature files. Production signing and the public stable endpoint are outside the lab.

The Void/QEMU run on 2026-11-25 exited 0. It passed TLS verification, repeat setup, key-prompt refusal and explicit import, four-package installation, coordinated `-Su` after synchronization, negative tests for truncated downloads, modified indexes, bad signatures, wrong keys, expired or replayed metadata and origin unavailability, and an explicit rollback. A separate native HTTPS download verified the Lens test package's RSA signature. The offline guest masked the distribution's repository defaults in its test configuration. The run did not exercise official Void mirrors or a production stable endpoint.
