import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class NoticeIntegrity(unittest.TestCase):
    def test_upstream_and_supplemental_bytes_preserved(self):
        for manifest in ['review/upstream-notices/manifest.json','review/asset-supplemental-notices/manifest.json']:
            for item in json.loads((ROOT/manifest).read_text()):
                with self.subTest(file=item['file']):self.assertEqual(hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest(),item['sha256'])
    def test_workspace_notice_bytes_preserved(self):
        data=json.loads((ROOT/'review/crate-upstream-notices/manifest.json').read_text())
        for crate,record in data.items():
            self.assertTrue(record['notices'],crate)
            for item in record['notices']:
                with self.subTest(crate=crate,file=item['file']):self.assertEqual(hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest(),item['sha256'])
    def test_cc0_notice_matches_recorded_origin(self):
        item=json.loads((ROOT/'review/common-licenses.json').read_text())[0]
        self.assertEqual(hashlib.sha256((ROOT/'legal/CC0-1.0.txt').read_bytes()).hexdigest(),item['sha256'])

if __name__=='__main__':unittest.main()
