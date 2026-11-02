# User guide — installation is not available yet

There is no live signed package channel or approved public signing key yet.
Do not add an invented repository URL or disable XBPS signature verification.
Only Void x86_64 glibc is in scope; no musl/other-architecture compatibility claim.
This is a community port, not an official Void or Skwd binary distribution.

After licensing, signing, deployment and public-endpoint verification, this file
will be completed with the REAL testing/stable URL, public key and independently
authenticated fingerprints. The following is the reviewed procedure, not runnable
installation instructions for a currently available repository.

1. Obtain the published public key and compare its SHA256 SPKI identity through a
   separate trusted channel. Check the native XBPS fingerprint as well.
2. Verify the release manifest signature and its index/package/source hashes.
   Run the release verifier with the independently trusted SHA256 key value.
3. Add ONE reviewed testing or stable repository line to a dedicated
   `/etc/xbps.d/20-skwd-community.conf`, leaving official Void repositories enabled.
4. Synchronize XBPS interactively; compare the key-import prompt, reject mismatches.
   Never automatically answer yes to a new/unexpected key or disable signatures.
5. Simulate installation of skwd-wall-v2-local, skwd-deck-local, skwd-lens-local and
   skwd-paper-local. Review dependencies, then install. Wall already pulls its
   exact Deck/Paper revision; Lens remains a separate package.
6. Follow the port's Wayland/driver setup. Start Deck and clients manually under
   your own account. Packages must not activate services/autostart or edit personal
   desktop settings. Back up settings before enabling wallpaper/theme hooks.
7. To update, first check the signed release notes/key identity and retain the
   previous four packages. Simulate the coordinated update, then apply it. Review
   rolling Void library/toolchain requirements and do not mix companion revisions.
8. To uninstall, stop only your Skwd components, simulate removal of all four named
   packages, then remove them. Personal settings/catalogue/cache deliberately remain.
9. Remove only the repository configuration file you added. Do not delete keys used
   by other repositories or remove unrelated packages/services automatically.

## Recovery from an update failure

Keep an offline copy of the last known-good coordinated packages, their source,
manifest and signatures. Close Skwd processes normally; do not kill the compositor.
Use a verified local repository holding the previous complete package set to
simulate an explicit-version reinstall/downgrade. Resolve all four exact versions
together, inspect the transaction and only then perform it. Do not use force/remove
options to bypass missing dependencies/signature failures. Restore personal settings
from your own pre-update backup only where changed; package downgrade alone does
not revert arbitrary configured hooks. A TTY is sufficient for package recovery.

If previous dependencies are no longer available, stop and use a prior VM/system
snapshot rather than replacing system libraries. Keep the community repository
disabled until the problem is fixed and the new release independently verified.
