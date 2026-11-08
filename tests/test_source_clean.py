import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('dh_clean'), 'debhelper is required')
class SourceCleanTests(unittest.TestCase):
    def test_actual_clean_target_preserves_vendor_checksums(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            shutil.copytree(ROOT/'packaging/source/debian',root/'debian',ignore=shutil.ignore_patterns('__pycache__'))
            upstream=root/'deps/vendor/aes/Cargo.toml.orig'
            upstream.parent.mkdir(parents=True)
            original=b'[package]\nname = "fixture"\n'
            upstream.write_bytes(original)
            (root/'leftover.orig').write_bytes(b'removable build detritus')
            result=subprocess.run(['make','-f','debian/rules','clean'],cwd=root,env=os.environ.copy(),text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue(upstream.exists(),'Debian clean deleted a Cargo checksummed source input')
            self.assertEqual(hashlib.sha256(upstream.read_bytes()).digest(),hashlib.sha256(original).digest())
            self.assertFalse((root/'leftover.orig').exists(),'normal clean must remain active')
