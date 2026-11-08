import importlib.util
import sys
import tarfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import pipeline as p


def metadata(version='7.4.1'):
    def asset(name):
        return dict(name=name, browser_download_url=f'https://github.com/telegramdesktop/tdesktop/releases/download/v{version}/{name}', digest='sha256:'+'a'*64)
    return dict(tag_name='v'+version, prerelease=False, draft=False, assets=[asset(f'td-setup-linux-x64-{version}.tar.xz'),asset(f'tdesktop-{version}-full.tar.gz')])

class PipelineTests(unittest.TestCase):
    def test_official_stable(self):
        r=p.discover(metadata()); self.assertEqual(r.version,'7.4.1'); self.assertTrue(r.source_url.endswith('full.tar.gz'))
    def test_reject_prerelease(self):
        data=metadata();data['prerelease']=True
        with self.assertRaises(ValueError): p.discover(data)
    def test_reject_ambiguous(self):
        data=metadata();data['assets'].append(data['assets'][0])
        with self.assertRaises(ValueError): p.discover(data)
    def test_reject_missing_digest(self):
        data=metadata();data['assets'][0]['digest']=None
        with self.assertRaises(ValueError): p.discover(data)
    def test_reject_unofficial_url(self):
        data=metadata();data['assets'][0]['browser_download_url']='https://evil.test/payload'
        with self.assertRaises(ValueError): p.discover(data)
    def test_no_downgrade(self):
        self.assertFalse(p.needs_update('7.4.0',{'version':'7.4.1','deb_version':'7.4.1-obs1'}))
    def test_same_revision_no_update(self):
        self.assertFalse(p.needs_update('7.4.1',{'version':'7.4.1','deb_version':'7.4.1-'+p.REVISION}))
    def test_graphics_build_dependencies(self):
        for library in ['libpangocairo-1.0-0','libpango-1.0-0','libpangoft2-1.0-0','libcairo2']:
            self.assertIn(library,p.BUILD_DEPS)
    def test_repack_cannot_release(self):
        with self.assertRaises(ValueError):p.require_source_record({'version':'7.4.1'})
    def test_test_credentials_cannot_release(self):
        record=dict(build_mode='source',api_identity='test',hwaccel_default=True,brand='NullWire')
        with self.assertRaises(ValueError):p.require_source_record(record)
    def test_default_disabled_cannot_release(self):
        record=dict(build_mode='source',api_identity='production',hwaccel_default=False,brand='NullWire')
        with self.assertRaises(ValueError):p.require_source_record(record)
    def test_archive_paths_and_links(self):
        for name,kind in [('../Telegram',tarfile.REGTYPE),('/Telegram',tarfile.REGTYPE),('Telegram/link',tarfile.SYMTYPE),('Telegram/device',tarfile.CHRTYPE)]:
            item=tarfile.TarInfo(name);item.type=kind
            with self.assertRaises(ValueError):p.validate_members([item])
    def test_archive_reject_privileged(self):
        item=tarfile.TarInfo('Telegram/Telegram');item.mode=0o4755
        with self.assertRaises(ValueError):p.validate_members([item])
    def test_release_needs_all_gates(self):
        for args in [(False,True,True),(True,False,True),(True,True,False)]:
            with self.assertRaises(ValueError):p.require_release(*args)
    def test_revision_change_rejected(self):
        with self.assertRaises(ValueError):p.require_same_revision('a','b')
    def test_stale_build_rejected(self):
        self.assertFalse(p.build_succeeded('<resultlist><result repository="xUbuntu_26.04" arch="x86_64" dirty="true"><status package="telegram-desktop" code="succeeded"/></result></resultlist>','telegram-desktop'))

if __name__=='__main__':unittest.main()
