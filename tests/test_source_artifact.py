"""Verify artifact identity across the verifier's build-context copy boundary."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class SourceArtifactTests(unittest.TestCase):
    def run_fixture(self,tamper):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'tools').mkdir();fakebin=root/'bin';fakebin.mkdir()
            shutil.copy2(ROOT/'tools/verify-source-deb.sh',root/'tools/verify-source-deb.sh')
            (root/'tools/source-container-check.sh').write_text('#!/bin/sh\nexit 0\n')
            package_root=root/'pkg';(package_root/'DEBIAN').mkdir(parents=True)
            (package_root/'DEBIAN/control').write_text('Package: nullwire-buildtest\nVersion: 1.0\nArchitecture: amd64\nMaintainer: Test <test@example.invalid>\nDescription: Synthetic artifact fixture\n')
            package=root/'fixture.deb'
            subprocess.run(['dpkg-deb','--build',str(package_root),str(package)],check=True,capture_output=True)
            cp=fakebin/'cp'
            cp.write_text('''#!/usr/bin/python3
import os,subprocess,sys
subprocess.run([os.environ['REAL_CP'],*sys.argv[1:]],check=True)
if os.environ.get('TAMPER_COPY')=='1' and os.environ['FIXTURE_PACKAGE'] in sys.argv:
 with open(os.environ['FIXTURE_PACKAGE'],'ab') as stream:stream.write(b'changed after context copy')
''');cp.chmod(0o755)
            docker=fakebin/'docker'
            docker.write_text('#!/bin/sh\nprintf "%s\\n" "$1" >> "$DOCKER_LOG"\nexit 0\n');docker.chmod(0o755)
            log=root/'docker.log';env=os.environ.copy()
            env.update(PATH=str(fakebin)+os.pathsep+env['PATH'],REAL_CP=shutil.which('cp'),FIXTURE_PACKAGE=str(package),TAMPER_COPY='1' if tamper else '0',DOCKER_LOG=str(log))
            result=subprocess.run(['bash','tools/verify-source-deb.sh',str(package)],cwd=root,env=env,text=True,capture_output=True)
            return result,log.read_text().splitlines() if log.exists() else []

    def test_changed_input_after_copy_blocks_verification(self):
        result,calls=self.run_fixture(tamper=True)
        self.assertNotEqual(result.returncode,0,'verifier accepted a build-context copy with different bytes from its claimed input hash')
        self.assertEqual(calls,[],'mismatched input must be rejected before the container runs')

    def test_unchanged_input_reaches_container_checks(self):
        result,calls=self.run_fixture(tamper=False)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(calls,['build','run'])
