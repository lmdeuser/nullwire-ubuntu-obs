"""Source preparation must reject changed or unpinned dependency bundles."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('source_prepare',ROOT/'tools/prepare-source-test.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class DependencyInputTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.upstream=self.root/'upstream';self.upstream.mkdir()
        self.folder=self.root/'output';self.folder.mkdir()
        debian=self.root/'packaging/source/debian';debian.mkdir(parents=True)
        (debian/'control').write_text('Build-Depends: python3\n')
        (debian/'rules').write_text('-DTDESKTOP_API_TEST=ON nullwire-buildtest\n')
        (self.upstream/'tdesktop-7.4.1-full.tar.gz').write_bytes(b'upstream boundary fixture')
        toolchain={}
        for name in ['rustc','rust-std','cargo']:
            (self.upstream/(name+'.tar.xz')).write_bytes(b'toolchain boundary fixture')
            toolchain[name]={'xz_url':'https://example.invalid/'+name+'.tar.xz','xz_hash':'a'*64}
        self.archive=self.folder/'nullwire_7.4.1.orig-deps.tar.xz'
        self.archive.write_bytes(b'reviewed dependency bundle')
        self.lock={'rust-toolchain':toolchain,'dependency_archive_sha256':hashlib.sha256(self.archive.read_bytes()).hexdigest()}
        self.lockfile=self.root/'packaging/source/dependencies.lock.json'
        self.write_lock()
        for name,value in [('ROOT',self.root),('UPSTREAM',self.upstream),('FOLDER',self.folder)]:
            changer=patch.object(p,name,value);changer.start();self.addCleanup(changer.stop)
        real_verify=p.verify
        def verify_boundary(path,expected):
            # Other upstream assets have their own verification tests; exercise
            # the actual dependency-digest check with real fixture bytes here.
            if path==self.archive:return real_verify(path,expected)
        changer=patch.object(p,'verify',side_effect=verify_boundary);changer.start();self.addCleanup(changer.stop)

    def write_lock(self):self.lockfile.write_text(json.dumps(self.lock))

    def test_changed_dependency_bundle_is_rejected(self):
        self.archive.write_bytes(b'unreviewed changed bundle')
        with self.assertRaisesRegex(ValueError,'SHA256'):p.prepare()

    def test_missing_dependency_pin_is_rejected(self):
        self.lock.pop('dependency_archive_sha256');self.write_lock()
        with self.assertRaisesRegex(ValueError,'dependency.*SHA256'):p.prepare()

    def test_reviewed_dependency_bundle_is_accepted(self):
        self.assertIn(self.archive,p.prepare())


class BuildDependencyTests(unittest.TestCase):
    def test_tdutils_generator_has_gperf(self):
        control=(ROOT/'packaging/source/debian/control').read_text()
        depends=next(line.split(':',1)[1] for line in control.splitlines() if line.startswith('Build-Depends:'))
        dependencies={item.strip() for item in depends.split(',')}
        self.assertIn('gperf',dependencies)

    def test_qsb_path_matches_ubuntu_qt6_package(self):
        rules=(ROOT/'packaging/source/debian/rules').read_text()
        flag='-DQSB_EXECUTABLE='
        self.assertIn(flag,rules)
        configured=next(token.split('=',1)[1] for token in rules.split() if token.startswith(flag))
        with tempfile.TemporaryDirectory() as folder:
            packaged=Path(folder)/'usr/lib/qt6/bin/qsb'
            packaged.parent.mkdir(parents=True)
            packaged.write_text('fixture')
            selected=Path(folder)/configured.lstrip('/')
            self.assertEqual(selected,packaged)
            self.assertTrue(selected.is_file())

    def test_lto_is_disabled_for_memory_bounded_link(self):
        rules=(ROOT/'packaging/source/debian/rules').read_text()
        options=next(line.split('=',1)[1].strip() for line in rules.splitlines() if line.startswith('export DEB_BUILD_MAINT_OPTIONS'))
        env=os.environ.copy()
        env['DEB_BUILD_MAINT_OPTIONS']=options
        result=subprocess.run(['dpkg-buildflags','--get','CXXFLAGS'],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        flags=result.stdout.split()
        self.assertFalse(any(flag.startswith('-flto') for flag in flags),result.stdout)

    def test_release_link_omits_oversized_debug_sections(self):
        rules=(ROOT/'packaging/source/debian/rules').read_text()
        append=next((line.split('=',1)[1].strip() for line in rules.splitlines() if line.startswith('export DEB_CXXFLAGS_MAINT_APPEND')),'')
        env=os.environ.copy()
        env['DEB_CXXFLAGS_MAINT_APPEND']=append
        result=subprocess.run(['dpkg-buildflags','--get','CXXFLAGS'],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        flags=result.stdout.split()
        debug=[flag for flag in flags if flag in {'-g','-g0','-g1','-g2','-g3'}]
        self.assertEqual(debug[-1],'-g0',result.stdout)
