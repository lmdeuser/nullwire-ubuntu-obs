"""Source preparation must reject changed or unpinned dependency bundles."""
import hashlib
import importlib.util
import json
from pathlib import Path
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
