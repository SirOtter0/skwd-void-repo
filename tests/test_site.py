import importlib.util
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('fetch_site',ROOT/'scripts/fetch-site.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SiteTests(unittest.TestCase):
    def bundle(self,directory,name='testing/file',link=False):
        p=Path(directory)/'site.tar.gz'
        with tarfile.open(p,'w:gz') as t:
            e=tarfile.TarInfo(name)
            if link:
                e.type=tarfile.SYMTYPE;e.linkname='/private';t.addfile(e)
            else:
                e.size=2;t.addfile(e,io.BytesIO(b'ok'))
        return p

    def test_regular_static_file(self):
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'out';m.unpack(self.bundle(d),output)
            self.assertEqual((output/'testing/file').read_bytes(),b'ok')

    def test_parent_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.unpack(self.bundle(d,'testing/../bad'),Path(d)/'out')

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.unpack(self.bundle(d,link=True),Path(d)/'out')

    def test_size_limit_checked(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'LIMIT',1):
            with self.assertRaises(ValueError):m.unpack(self.bundle(d),Path(d)/'out')

    def test_publication_disabled_by_default(self):
        with self.assertRaisesRegex(ValueError,'not approved'):m.verify_site(Path('/unused'),m.repository.load(ROOT/'policy/release.json'))

    def test_existing_stable_cannot_disappear(self):
        policy=m.repository.load(ROOT/'policy/release.json');policy['distribution_approved']=True;policy['hosting']['stable_url']='https://example.invalid/stable'
        with tempfile.TemporaryDirectory() as d,patch.object(m.repository,'verify'),patch.object(m.repository,'gate'):
            with self.assertRaisesRegex(ValueError,'existing stable'):m.verify_site(Path(d),policy)

if __name__=='__main__':unittest.main()
