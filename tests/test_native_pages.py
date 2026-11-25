import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


build = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/build-native-pages.py"))["build"]


class NativePagesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.site = self.root / "site"
        self.policy = self.root / "policy.json"

    def put_policy(self, *versions):
        self.policy.write_text(json.dumps({
            "schema": 1, "releases": [{"version": version} for version in versions]
        }))

    def stage(self, work, release, _source):
        version = release["version"]
        (work / "x86_64-repodata").write_text(version)
        for suffix in ("xbps", "xbps.sig2"):
            asset = work / f"skwd-example-{version}.{suffix}"
            asset.write_text(version)
            yield asset

    def test_retains_previous_assets_only_current_index(self):
        self.put_policy("1.0.0beta29_2", "1.0.0beta29_3")
        with patch.dict(build.__globals__, stage_release=self.stage):
            build(self.policy, self.site, None)
        self.assertEqual((self.site / "x86_64-repodata").read_text(), "1.0.0beta29_3")
        self.assertEqual(len(list(self.site.glob("*.xbps"))), 2)
        self.assertEqual(len(list(self.site.glob("*.sig2"))), 2)

    def test_incomplete_release_never_creates_site(self):
        self.put_policy("1.0.0beta29_2", "1.0.0beta29_3")

        def fail_second(work, release, source):
            if release["version"].endswith("_3"):
                raise ValueError("Fixture with missing signed asset")
            yield from self.stage(work, release, source)

        with patch.dict(build.__globals__, stage_release=fail_second):
            with self.assertRaisesRegex(ValueError, "missing signed asset"):
                build(self.policy, self.site, None)
        self.assertFalse(self.site.exists())

    def test_rejects_unordered_or_duplicate_policy(self):
        for versions in (("1.0.0beta29_3", "1.0.0beta29_2"), ("1.0.0beta29_2",) * 2):
            with self.subTest(versions=versions):
                self.put_policy(*versions)
                with self.assertRaisesRegex(ValueError, "increasing order"):
                    build(self.policy, self.site, None)


if __name__ == "__main__":
    unittest.main()
