#!/usr/bin/env python3
"""Install unmodified upstream Telegram binary and official source notices."""
from pathlib import Path
import shutil
import struct
import sys

NAME='telegram-desktop'

def source_root():
    roots=[p.parent for p in Path('source').rglob('LICENSE') if (p.parent/'Telegram/Resources/art/icon256.png').is_file()]
    if len(roots)!=1:raise ValueError('missing/ambiguous full source tree')
    return roots[0]

def verify():
    binary=Path('Telegram')
    if not binary.is_file():raise ValueError('missing Telegram executable')
    with binary.open('rb') as f:header=f.read(20)
    if header[:6]!=b'\x7fELF\x02\x01' or struct.unpack('<H',header[18:20])[0]!=62:
        raise ValueError('expected ELF amd64')
    root=source_root()
    if not (root/'LICENSE').is_file():raise ValueError('missing upstream license')
    return root

def install():
    root=verify()
    dest=Path('debian')/NAME
    def write(path,text,mode=0o644):
        p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);p.chmod(mode)
    lib=dest/'usr/lib'/NAME;lib.mkdir(parents=True,exist_ok=True)
    shutil.copy2('Telegram',lib/'Telegram')
    (lib/'Telegram').chmod(0o755)
    # Upstream's supported distribution marker; no binary patching.
    write(f'usr/lib/{NAME}/externalupdater.d/apt',f'/usr/lib/{NAME}/Telegram\n')
    write('usr/bin/telegram-desktop',f'#!/bin/sh\nexec /usr/lib/{NAME}/Telegram -noupdate "$@"\n',0o755)
    write('usr/share/applications/org.telegram.desktop.desktop','''[Desktop Entry]
Type=Application
Name=Telegram Desktop
Comment=Telegram messenger
Exec=/usr/bin/telegram-desktop -- %u
TryExec=/usr/bin/telegram-desktop
Icon=telegram
Terminal=false
Categories=Network;InstantMessaging;Qt;
MimeType=x-scheme-handler/tg;x-scheme-handler/tonsite;
StartupWMClass=TelegramDesktop
StartupNotify=true
SingleMainWindow=true
Actions=quit;

[Desktop Action quit]
Name=Quit Telegram
Exec=/usr/bin/telegram-desktop -quit
''')
    icons=dest/'usr/share/icons/hicolor/256x256/apps';icons.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/'Telegram/Resources/art/icon256.png',icons/'telegram.png')
    doc=dest/'usr/share/doc'/NAME;doc.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/'LICENSE',doc/'LICENSE.upstream')
    legal=root/'LEGAL'
    if legal.is_dir():shutil.copytree(legal,doc/'LEGAL',dirs_exist_ok=True)
    elif legal.is_file():shutil.copy2(legal,doc/'LEGAL')
    write(f'usr/share/doc/{NAME}/UPDATES','Application self-updates are disabled by the upstream externalupdater.d mechanism.\nUse apt update and apt upgrade. Full corresponding sources are in the OBS source package.\n')

if __name__=='__main__':{'verify':verify,'install':install}[sys.argv[1]]()
