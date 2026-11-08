import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('migration',Path(__file__).resolve().parents[1]/'tools/migrate-profile.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class MigrationTests(unittest.TestCase):
    def test_detect_snap_and_upstream_executables(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for pid,target in [('101','/snap/telegram-desktop/7183/usr/bin/telegram-desktop'),('102','/usr/lib/telegram-desktop/Telegram'),('103','/usr/bin/python3')]:
                d=root/pid;d.mkdir();(d/'exe').symlink_to(target)
            self.assertEqual(set(p.telegram_processes(root)),{101,102})
    def test_detect_deleted_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'104').mkdir();(root/'104/exe').symlink_to('/usr/lib/telegram-desktop/Telegram (deleted)')
            self.assertEqual(p.telegram_processes(root),[104])

if __name__=='__main__':unittest.main()
