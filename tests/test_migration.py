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


# Characterization of existing migration behavior before any further changes.
class MigrationBoundaryTests(unittest.TestCase):
    def setUp(self):
        import os
        from unittest.mock import patch
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.home=self.root/'home'
        self.source=self.home/'snap/telegram-desktop/1/.local/share/TelegramDesktop'
        (self.source/'tdata').mkdir(parents=True)
        (self.home/'snap/telegram-desktop/current').symlink_to('1')
        (self.home/'.local/share').mkdir(parents=True)
        self.dest=self.home/'.local/share/TelegramDesktop'
        self.profile=self.source/'tdata/session.dat'
        self.profile.write_bytes(b'fixture profile, not a real session')
        for name,value in [('HOME',self.home),('ROOT',self.root)]:
            changer=patch.object(p,name,value);changer.start();self.addCleanup(changer.stop)
        changer=patch.object(p.os,'getuid',return_value=1000);changer.start();self.addCleanup(changer.stop)
        changer=patch.object(p,'telegram_processes',return_value=[]);changer.start();self.addCleanup(changer.stop)
        original=os.umask(0o077);self.addCleanup(os.umask,original)

    def test_existing_native_profile_is_not_overwritten(self):
        self.dest.mkdir();sentinel=self.dest/'existing';sentinel.write_bytes(b'keep')
        with self.assertRaisesRegex(SystemExit,'already exists'):p.main()
        self.assertEqual(sentinel.read_bytes(),b'keep')
        self.assertFalse((self.root/'.state/migration').exists())

    def test_source_symlink_is_rejected_before_backup(self):
        outside=self.root/'outside';outside.write_bytes(b'outside fixture')
        (self.source/'tdata/link').symlink_to(outside)
        with self.assertRaisesRegex(SystemExit,'symlinks'):p.main()
        self.assertFalse(self.dest.exists())
        self.assertFalse((self.root/'.state/migration').exists())

    def test_destination_parent_symlink_is_rejected(self):
        target=self.root/'other';target.mkdir()
        parent=self.home/'.local/share';parent.rmdir();parent.symlink_to(target)
        with self.assertRaisesRegex(SystemExit,'parent is a symlink'):p.main()
        self.assertEqual(list(target.iterdir()),[])

    def test_running_client_blocks_migration(self):
        from unittest.mock import patch
        with patch.object(p,'telegram_processes',return_value=[123]):
            with self.assertRaisesRegex(SystemExit,'Close Telegram'):p.main()
        self.assertFalse(self.dest.exists())

    def test_changed_backup_never_installs_profile(self):
        from unittest.mock import patch
        real_digest=p.digest
        def change_after_read(path):
            result=real_digest(path)
            if path==self.profile:self.profile.write_bytes(b'concurrently changed fixture')
            return result
        with patch.object(p,'digest',side_effect=change_after_read):
            with self.assertRaisesRegex(SystemExit,'Backup verification failed'):p.main()
        self.assertFalse(self.dest.exists())
        self.assertFalse(list((self.root/'.state/migration').rglob('manifest.json')))

    def test_small_migration_verifies_backup_and_copy(self):
        import contextlib,io,json
        with contextlib.redirect_stdout(io.StringIO()):p.main()
        self.assertEqual((self.dest/'tdata/session.dat').read_bytes(),self.profile.read_bytes())
        manifest=next((self.root/'.state/migration').rglob('manifest.json'))
        record=json.loads(manifest.read_text())
        self.assertEqual(record['file_count'],1)
        self.assertEqual(record['archive_sha256'],p.digest(manifest.with_name('snap-profile.tar')))
        self.assertTrue(self.profile.exists())
        self.assertEqual(self.dest.stat().st_mode & 0o777,0o700)

if __name__=='__main__':unittest.main()
