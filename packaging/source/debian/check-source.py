#!/usr/bin/env python3
"""Check the actual patched Linux default and preserved backend selection."""
from pathlib import Path
import os
import re
import subprocess
import sys


def check(root):
    root=Path(root)
    settings=(root/'Telegram/SourceFiles/core/core_settings.h').read_text()
    matches=re.findall(r'(#if[^\n]*Q_OS_MAC[^\n]*\n\s*bool _hardwareAcceleratedVideo[^#]+#else[^#]+#endif[^\n]*)',settings)
    if len(matches)!=1:raise ValueError('unknown hardware-video default layout')
    output=subprocess.run(['cpp','-P','-DQ_OS_LINUX','-'],input=matches[0],text=True,capture_output=True,check=True).stdout
    if not re.search(r'bool\s+_hardwareAcceleratedVideo\s*=\s*true\s*;',output):
        raise ValueError('Linux hardware video decoding does not default to enabled')
    version=(root/'Telegram/SourceFiles/core/version.h').read_text()
    if 'constexpr auto AppName = "NullWire"_cs;' not in version:raise ValueError('unofficial client name is missing')
    ffmpeg=(root/'Telegram/SourceFiles/ffmpeg/ffmpeg_utility.cpp').read_text()
    for backend in ['AV_HWDEVICE_TYPE_VAAPI','AV_HWDEVICE_TYPE_VDPAU','AV_HWDEVICE_TYPE_CUDA']:
        if backend not in ffmpeg:raise ValueError('upstream hardware backend is missing')
    if not re.search(r'for \(const enum AVPixelFormat \*p = formats;.*?result = \*p;',ffmpeg,re.S):
        raise ValueError('upstream software pixel-format fallback is missing')
    print('PASS: source Linux GPU default, NullWire name and upstream backend/fallback code')

if __name__=='__main__':check(sys.argv[1])
