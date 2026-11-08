import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
s=importlib.util.spec_from_file_location('public_source',ROOT/'scripts/prepare-public-source.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class SDKExclusions(unittest.TestCase):
    def closure(self,used=None):return {'components':{'deck':{'runtime_registry_packages':used or [],'build_only_or_proc_macro_packages':[]}}}
    def test_source_module_named_target_is_retained(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);module=root/'skwd-paper/crates/paper-vk/src/wayland/target';module.mkdir(parents=True)
            self.assertFalse(m.is_build_state(module,root))
            cargo=root/'skwd-paper/target';cargo.mkdir();(cargo.parent/'Cargo.toml').write_text('[workspace]')
            self.assertTrue(m.is_build_state(cargo,root))
    def test_empty_sdk_not_claimed_as_shipped(self):
        with tempfile.TemporaryDirectory() as d:
            suite=Path(d);(suite/'vendor/steamworks-sys-1/lib').mkdir(parents=True)
            result=m.sdk_plan(suite,self.closure());self.assertEqual(result['excluded_files'],[]);self.assertEqual(result['observations'][0]['sdk_lib_file_count'],0)
    def test_unused_sdk_recorded_for_exclusion(self):
        with tempfile.TemporaryDirectory() as d:
            suite=Path(d);folder=suite/'vendor/steamworks-sys-1/lib';folder.mkdir(parents=True);(folder/'libsteam_api.so').write_bytes(b'synthetic-test-only')
            self.assertEqual(m.sdk_plan(suite,self.closure())['excluded_files'][0]['path'],'vendor/steamworks-sys-1/lib/libsteam_api.so')
    def test_used_sdk_refuses_automatic_exclusion(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.sdk_plan(Path(d),self.closure(['steamworks-sys-1']))

if __name__=='__main__':unittest.main()
