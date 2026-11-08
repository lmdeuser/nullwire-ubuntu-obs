"""Exercise build command routing without compiling Telegram locally."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('cargo'), 'Cargo metadata probe is required')
class BindingsDirectoryTests(unittest.TestCase):
    def test_bindgen_runs_from_rust_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'debian').mkdir()
            shutil.copy2(ROOT/'packaging/source/debian/build-deps.sh',root/'debian/build-deps.sh')
            workspace=root/'deps/tdesktop_rust'
            (workspace/'src').mkdir(parents=True)
            (workspace/'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\nedition="2021"\n')
            (workspace/'src/lib.rs').write_text('')
            (root/'deps/cargo-config.template').write_text('')
            (root/'deps/tlottie/include').mkdir(parents=True)
            (root/'deps/tlottie/include/tlottie.h').write_text('fixture header')
            fixture_bin=root/'fixture-bin';fixture_bin.mkdir()
            rustc=fixture_bin/'rustc'
            rustc.write_text('#!/bin/sh\necho "rustc 1.96.1 (fixture)"\n');rustc.chmod(0o755)
            cargo=fixture_bin/'cargo'
            cargo.write_text('''#!/usr/bin/python3
import os, pathlib, subprocess, sys
root=pathlib.Path(os.environ['BINDINGS_FIXTURE'])
if sys.argv[1]=='rustc':
 output=root/'deps/tdesktop_rust/target/release';output.mkdir(parents=True)
 for name in ['libtdesktop_rust.a','libtdesktop_rust.so']:(output/name).touch()
 sys.exit(0)
if sys.argv[1]=='run':
 # UniFFI's Cargo metadata lookup uses its process working directory.
 env=os.environ.copy();env['RUSTC']=env['ACTUAL_RUSTC'];env['RUSTUP_TOOLCHAIN']='stable'
 result=subprocess.run([env['ACTUAL_CARGO'],'metadata','--offline','--no-deps','--format-version','1'],env=env,capture_output=True)
 if result.returncode:sys.stderr.write(result.stderr.decode());sys.exit(result.returncode)
 (root/'observed-bindings-cwd').write_text(os.getcwd())
 sys.exit(37) # Stop before the unrelated C++ compilation stages.
sys.exit(99)
''');cargo.chmod(0o755)
            for name in ['rustc','ruststd','cargo']:
                component=root/name;component.mkdir()
                (component/'install.sh').write_text('''#!/bin/bash
set -eu
for arg; do case "$arg" in --prefix=*) prefix=${arg#--prefix=};; esac; done
mkdir -p "$prefix/bin"
cp "$BINDINGS_FIXTURE/fixture-bin/"* "$prefix/bin/"
''')
            env=os.environ.copy()
            env.update(BINDINGS_FIXTURE=str(root),ACTUAL_CARGO=shutil.which('cargo'),ACTUAL_RUSTC=shutil.which('rustc'))
            result=subprocess.run(['bash','debian/build-deps.sh'],cwd=root,env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,37,result.stdout+result.stderr)
            self.assertEqual((root/'observed-bindings-cwd').read_text(),str(workspace))
