# Signing design — no release key created

No definitive key has been generated, imported into CI or used by this repository.
Owner approval is required before doing so. Proposed first implementation: manual
offline signing on a separate normal-user Void machine/VM, encrypted PEM RSA-4096
key, two encrypted offline backup copies, private directory0700/key0600, excluded
from Git and candidate/source/artifact trees. Keep the signer network disabled;
transfer only reviewed candidate files, never execute builder-supplied programs.

After approval, generate a new dedicated key interactively using the official
Void-documented PEM RSA method (for example ssh-keygen RSA4096 with -m PEM and a
strong passphrase). Do not reuse an SSH login key. This document deliberately does
not run key-generation commands. Never log passphrases, enable shell tracing, put
keys on command lines, or store them as Actions artifacts. Prefer interactive
passphrase prompts over environment variables. No XBPS_PASSPHRASE is configured.

Export only the public PEM. `repository.py identity PUBLIC.pem` prints:

* SHA256 of the public key's DER SubjectPublicKeyInfo, the modern identity pinned
  in policy and independently checked by the manifest verifier.
* The OpenSSH/MD5 fingerprint that XBPS displays for key import. This is a lookup
  fingerprint, not a claim that package signatures use MD5: XBPS uses RSA/SHA256.

The derivation was checked against an already trusted PUBLIC Void key on the
workstation; no private key was accessed or generated. Publish both values on the
repository and at least one separately controlled channel. A hash beside an
untrusted download is not independent authentication. Users must compare the
XBPS import prompt and the SHA256 identity with those authenticated values.

## Explicit signing flow

1. Resolve LICENSE blockers and review the exact candidate/source archive.
2. Set the candidate.json SHA256 approval, reviewer/evidence, signing identity,
   SPKI SHA256 and native XBPS fingerprint in policy. Policy changes require review.
3. Verify package contents/dependencies and clean install/runtime/removal receipts
   before attaching the offline key. Signer must contain trusted XBPS/OpenSSL tools.
4. On an interactive offline signer:

   `python3 scripts/repository.py sign CANDIDATE /outside/git/private.pem --approve-signing`

The script checks the exact approved candidate hash, key ownership/permissions,
external location and approved public identity. It never copies the private key.
It creates native package .sig2 signatures, initializes XBPS key metadata, writes a
signed release.json covering the index/package/source hashes, and verifies package
signatures and repository consistency. It does not upload anything. Signing code
has not yet been exercised with a release or test private key; that ceremony and
end-to-end XBPS remote acceptance remain prerequisites after owner approval.

Important XBPS distinction: `xbps-rindex --sign` initializes repository key metadata;
it must not be presented as a detached cryptographic signature over every byte of
the index. Native package signatures plus the additionally signed release manifest
cover the required distribution integrity. The additional manifest is verified by
our tooling; stock XBPS does not automatically enforce that extra manifest or a
monotonic release number. A compromised host can cause denial of service or replay
old valid content; retain pinned release hashes/history and monitor channel age.

## Rotation and incident response

Stop promotions, publish a separately authenticated revocation/incident notice,
generate a new dedicated key only with owner approval, and independently publish
the old/new identities and transition date. If the old key is trustworthy it may
sign the transition notice, but do not rely on it alone after a compromise.
Re-sign verified packages and rebuild repository metadata with the new key;
verify the client prompt in a disposable VM. Do not silently auto-import keys or
remove another repository's trusted key. Keep archival sources/signatures for
old releases and explain rollback implications.

References:
[Void signing handbook](https://docs.voidlinux.org/xbps/repositories/signing.html),
[XBPS fingerprint implementation](https://github.com/void-linux/xbps/blob/26133746094d64bbae6b87f355200f9da8dc7711/lib/pubkey2fp.c),
[XBPS signing implementation](https://github.com/void-linux/xbps/blob/26133746094d64bbae6b87f355200f9da8dc7711/bin/xbps-rindex/sign.c).
