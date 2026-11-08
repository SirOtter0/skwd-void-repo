import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('fingerprint',ROOT/'scripts/repository.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class FingerprintEncoding(unittest.TestCase):
    def test_rfc4251_positive_mpint_padding(self):
        # Public toy integers, not a usable RSA key. RFC4251 requires sign padding.
        der=bytes.fromhex('300a02030080ff0203010001')
        expected=b'\x00\x00\x00\x07ssh-rsa\x00\x00\x00\x03\x01\x00\x01\x00\x00\x00\x03\x00\x80\xff'
        self.assertEqual(m.rsa_ssh_blob(der),expected)
    def test_negative_or_truncated_or_extra_der_rejected(self):
        for value in ['3009020280ff0203010001','300a02030080ff02030100','300a02030080ff020301000100']:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):m.rsa_ssh_blob(bytes.fromhex(value))

if __name__=='__main__':unittest.main()
