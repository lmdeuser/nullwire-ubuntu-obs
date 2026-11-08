import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('package',Path(__file__).resolve().parents[1]/'packaging/package.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.previous=Path.cwd();os.chdir(self.tmp.name)
        root=Path('source/tdesktop');(root/'Telegram/Resources/art').mkdir(parents=True)
        (root/'Telegram/Resources/art/icon256.png').write_bytes(b'PNG')
        (root/'LICENSE').write_text('upstream GPL')
        (root/'LEGAL').write_text('third party notices')
        header=bytearray(20);header[:6]=b'\x7fELF\x02\x01';header[18:20]=b'\x3e\0'
        Path('Telegram').write_bytes(header)
    def tearDown(self):
        os.chdir(self.previous);self.tmp.cleanup()
    def test_preserve_binary_and_disable_updater(self):
        p.install();dest=Path('debian/telegram-desktop')
        self.assertEqual(Path('Telegram').read_bytes(),(dest/'usr/lib/telegram-desktop/Telegram').read_bytes())
        self.assertEqual((dest/'usr/lib/telegram-desktop/externalupdater.d/apt').read_text(),'/usr/lib/telegram-desktop/Telegram\n')
        self.assertFalse((dest/'usr/lib/telegram-desktop/Updater').exists())
        self.assertEqual((dest/'usr/share/doc/telegram-desktop/LEGAL').read_text(),'third party notices')
    def test_reject_wrong_architecture(self):
        Path('Telegram').write_bytes(b'wrong binary')
        with self.assertRaises(ValueError):p.verify()
    def test_reject_missing_corresponding_source(self):
        Path('source/tdesktop/LICENSE').unlink()
        with self.assertRaises(ValueError):p.verify()
