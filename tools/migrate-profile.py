#!/usr/bin/env python3
"""Back up and copy a stopped Snap profile; never delete the source profile."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
HOME=Path('/home/dennweiss')

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def telegram_processes(proc_root=Path('/proc')):
    active=[]
    for process in proc_root.iterdir():
        if not process.name.isdigit():continue
        try:executable=Path(os.readlink(process/'exe')).name.removesuffix(' (deleted)').lower()
        except OSError:continue
        if executable in {'telegram','telegram-desktop'}:active.append(int(process.name))
    return active


def main():
    if os.getuid()!=1000:raise SystemExit('Run as dennweiss, not root')
    if telegram_processes():
        raise SystemExit('Close Telegram before migrating its profile')
    source=(HOME/'snap/telegram-desktop/current/.local/share/TelegramDesktop').resolve(strict=True)
    if not source.is_relative_to(HOME/'snap/telegram-desktop') or not (source/'tdata').is_dir():
        raise SystemExit('Unexpected source profile')
    dest=HOME/'.local/share/TelegramDesktop'
    if dest.exists() or dest.is_symlink():raise SystemExit('Native profile already exists; refusing overwrite')
    if (HOME/'.local/share').resolve()!=HOME/'.local/share':raise SystemExit('Destination parent is a symlink')
    files=list(source.rglob('*'))
    if any(p.is_symlink() for p in files):raise SystemExit('Source profile contains symlinks; review before copying')
    os.umask(0o077)
    backup=ROOT/'.state/migration'/time.strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True,mode=0o700)
    expected={str(p.relative_to(source)):digest(p) for p in files if p.is_file()}
    archive=backup/'snap-profile.tar'
    with tarfile.open(archive,'w') as tar:tar.add(source,arcname='TelegramDesktop',recursive=True)
    with tarfile.open(archive) as tar:
        actual={str(Path(m.name).relative_to('TelegramDesktop')):hashlib.file_digest(tar.extractfile(m),'sha256').hexdigest() for m in tar.getmembers() if m.isfile()}
    if actual!=expected:raise SystemExit('Backup verification failed')
    # Detect any concurrent profile modification before installing its copy.
    if expected!={str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file()}:
        raise SystemExit('Source profile changed during backup')
    if telegram_processes():raise SystemExit('Telegram started during backup; source profile preserved')
    shutil.copytree(source,dest,symlinks=False)
    dest.chmod(0o700)
    copied={str(p.relative_to(dest)):digest(p) for p in dest.rglob('*') if p.is_file()}
    if copied!=expected:raise SystemExit('Destination verification failed; source and backup preserved')
    (backup/'manifest.json').write_text(json.dumps(dict(source=str(source),destination=str(dest),archive_sha256=digest(archive),file_count=len(expected),profile_files=expected),indent=2)+'\n')
    print(f'Verified profile backup and migration: {len(expected)} files; backup {backup}')

if __name__=='__main__':main()
