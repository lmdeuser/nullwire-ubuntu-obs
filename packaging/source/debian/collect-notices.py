#!/usr/bin/env python3
"""Retain license notices for statically bundled dependencies and Rust runtime."""
from pathlib import Path
import shutil
import sys

root=Path(sys.argv[1]).resolve(strict=True)
dest=root/'debian/nullwire-buildtest/usr/share/doc/nullwire-buildtest/third-party-notices'
count=0
for base in [root/'deps',root/'ruststd']:
    for path in sorted(base.rglob('*')):
        if '.git' in path.parts or 'target' in path.parts:continue
        name=path.name.upper()
        if not (name.startswith(('LICENSE','LICENCE','COPYING','NOTICE','COPYRIGHT')) or name=='LEGAL'):continue
        if not path.is_file():continue
        if not path.resolve(strict=True).is_relative_to(root):raise ValueError('license path escapes source root')
        if path.stat().st_size>5*1024*1024:raise ValueError('unexpectedly large license notice')
        target=dest/path.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target);count+=1
if not count:raise ValueError('no dependency notices found')
print('Retained dependency license notices:',count)
