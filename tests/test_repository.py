import importlib.util
import io
import json
from pathlib import Path
import plistlib
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('repository', ROOT / 'scripts/repository.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class RepositoryTests(unittest.TestCase):
    def policy(self):
        return m.load(ROOT / 'policy/release.json')

    def package(self, directory, extra=None, arch='x86_64', deps=None):
        name = 'skwd-lens-local'
        p = Path(directory) / (name + '-1.0.0beta26_3.x86_64.xbps')
        props = {'architecture': arch, 'pkgname': name, 'pkgver': name + '-1.0.0beta26_3', 'run_depends': deps or []}
        with tarfile.open(p, 'w') as t:
            for path, value in [('props.plist', plistlib.dumps(props)), ('usr/bin/skwd-lens', b'not-executed'), *(([extra]) if extra else [])]:
                entry = tarfile.TarInfo(path); entry.size = len(value)
                t.addfile(entry, io.BytesIO(value))
        return p

    def test_valid_package_is_inspected_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.inspect(self.package(d), self.policy())['name'], 'skwd-lens-local')

    def test_install_hook_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.inspect(self.package(d, ('INSTALL', b'bad')), self.policy())

    def test_autostart_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.inspect(self.package(d, ('usr/share/autostart/bad', b'bad')), self.policy())

    def test_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.inspect(self.package(d, ('../bad', b'bad')), self.policy())

    def test_musl_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.inspect(self.package(d, arch='x86_64-musl'), self.policy())

    def test_systemd_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.inspect(self.package(d, deps=['systemd>=1']), self.policy())

    def test_package_set_must_be_coordinated(self):
        with tempfile.TemporaryDirectory() as d:
            self.package(d)
            with self.assertRaises(ValueError):m.check_candidates(d, self.policy())

    def test_distribution_is_blocked_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'candidate.json';p.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'approval'):m.gate(self.policy(), p)

    def test_license_approval_is_bound_to_candidate_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'candidate.json';p.write_text('{}');policy = self.policy()
            policy['distribution_approved'] = True
            policy['license_review'].update(approved=True,reviewer='reviewer',evidence='review',approved_candidate_sha256='0'*64,blockers=[])
            with self.assertRaisesRegex(ValueError, 'exact candidate'):m.gate(policy, p)

    def test_wrong_public_key_rejected_before_signature_check(self):
        from unittest.mock import patch
        with patch.object(m,'public_identity',return_value={'spki_sha256':'a'*64}):
            with self.assertRaisesRegex(ValueError,'trusted identity'):m.verify(Path('/unused'), 'b'*64)


if __name__ == '__main__':unittest.main()
