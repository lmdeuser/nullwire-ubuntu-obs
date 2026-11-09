#!/usr/bin/env python3
"""Prepare or submit the isolated offline NullWire build-test source package."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import tarfile
import xml.etree.ElementTree as ET

import pipeline as obs

ROOT=Path(__file__).resolve().parents[1]
VERSION='7.4.1'
DEB_VERSION=VERSION+'-obs3.test10'
PACKAGE='nullwire-buildtest'
SOURCE='nullwire'
FOLDER=ROOT/'.state/source-buildtest'
UPSTREAM=ROOT/'.state/upstream'


def verify(path,expected):
    if obs.sha256(path)!=expected:raise ValueError('source input SHA256 mismatch: '+path.name)


def prepare():
    FOLDER.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/'packaging/source/dependencies.lock.json').read_text())
    assets=[(UPSTREAM/f'tdesktop-{VERSION}-full.tar.gz',f'{SOURCE}_{VERSION}.orig.tar.gz','b3d98d75961bf81c2752cec60bdd67a586960fbfca29e3ab473165e49de533d4',f'https://github.com/telegramdesktop/tdesktop/releases/download/v{VERSION}/tdesktop-{VERSION}-full.tar.gz')]
    for component,key in [('rustc','rustc'),('ruststd','rust-std'),('cargo','cargo')]:
        data=lock['rust-toolchain'][key]
        assets.append((UPSTREAM/data['xz_url'].rsplit('/',1)[1],f'{SOURCE}_{VERSION}.orig-{component}.tar.xz',data['xz_hash'],data['xz_url']))
    services=ET.Element('services');files=[]
    for src,name,digest,url in assets:
        verify(src,digest);dest=FOLDER/name
        if not dest.exists():os.link(src,dest)
        verify(dest,digest);files.append(dest)
        parsed=__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(url)
        fetch=ET.SubElement(services,'service',name='download_url')
        for key,value in [('protocol','https'),('host',parsed.netloc),('path',parsed.path),('filename',name)]:ET.SubElement(fetch,'param',name=key).text=value
        check=ET.SubElement(services,'service',name='verify_file')
        for key,value in [('file','_service:download_url:'+name),('verifier','sha256'),('checksum',digest)]:ET.SubElement(check,'param',name=key).text=value
    dependencies=FOLDER/f'{SOURCE}_{VERSION}.orig-deps.tar.xz'
    if not dependencies.is_file():raise ValueError('offline source dependency archive is not ready')
    expected=lock.get('dependency_archive_sha256')
    if not isinstance(expected,str) or not re.fullmatch(r'[0-9a-f]{64}',expected):
        raise ValueError('missing or invalid dependency archive SHA256 pin')
    verify(dependencies,expected)
    files.append(dependencies)
    debian=ROOT/'packaging/source/debian'
    rules=(debian/'rules').read_text()
    if '-DTDESKTOP_API_TEST=ON' not in rules or 'nullwire-buildtest' not in rules:raise ValueError('build-test isolation has changed')
    debtar=FOLDER/f'{SOURCE}_{DEB_VERSION}.debian.tar.xz'
    with tarfile.open(debtar,'w:xz') as tar:tar.add(debian,arcname='debian',filter=lambda m:None if '__pycache__' in Path(m.name).parts or m.name.endswith('.pyc') else m)
    files.append(debtar)
    control=(debian/'control').read_text();depends=next(line.split(':',1)[1].strip() for line in control.splitlines() if line.startswith('Build-Depends:'))
    dsc=FOLDER/f'{SOURCE}_{DEB_VERSION}.dsc'
    dsc.write_text(f'''Format: 3.0 (quilt)
Source: {SOURCE}
Binary: {PACKAGE}
Architecture: amd64
Version: {DEB_VERSION}
Maintainer: dwolfF <dwolfF@users.noreply.build.opensuse.org>
Build-Depends: {depends}
Files:
'''+''.join(f' {hashlib.md5(p.read_bytes()).hexdigest()} {p.stat().st_size} {p.name}\n' for p in files)+'Checksums-Sha256:\n'+''.join(f' {obs.sha256(p)} {p.stat().st_size} {p.name}\n' for p in files))
    service=FOLDER/'_service';service.write_text(ET.tostring(services,encoding='unicode')+'\n')
    constraints=FOLDER/'_constraints';constraints.write_text('<constraints><hardware><memory><size unit="G">16</size></memory><disk><size unit="G">16</size></disk></hardware></constraints>\n')
    return [dsc,debtar,dependencies,service,constraints]


def submit(files):
    project=obs.STAGING;path=f'/source/{project}/{PACKAGE}'
    config_path=f'/source/{project}/_config'
    config=obs.api(config_path)
    preference='Prefer: libavcodec62 libavfilter11 libavformat62'
    if preference not in config.splitlines():
        obs.api(config_path,'PUT',config.rstrip()+'\n'+preference+'\n')
    try:obs.api(path+'/_meta')
    except __import__('subprocess').CalledProcessError as e:
        if '404' not in e.stderr:raise
        obs.api(path+'/_meta','PUT',f'<package name="{PACKAGE}" project="{project}"><title>NullWire isolated source build test</title><description>Limited test API identity. Not for login, migration or stable release.</description><publish><disable/></publish></package>')
    current={entry.attrib['name']:entry.attrib['md5'] for entry in ET.fromstring(obs.api(path)) if entry.tag=='entry'}
    listing=ET.Element('directory')
    for file in files:
        digest=hashlib.md5(file.read_bytes()).hexdigest()
        if current.get(file.name)!=digest:
            print('Uploading source file:',file.name,flush=True)
            obs.api(path+'/'+file.name+'?rev=repository','PUT',file=file)
        ET.SubElement(listing,'entry',name=file.name,md5=digest)
    response=ET.fromstring(obs.api(path+'?cmd=commitfilelist&comment=NullWire-offline-source-build-test','POST',ET.tostring(listing,encoding='unicode')))
    record=dict(package=PACKAGE,source_version=DEB_VERSION,srcmd5=response.attrib['srcmd5'],build_mode='source',api_identity='test',release_allowed=False,files={p.name:obs.sha256(p) for p in files})
    obs.save_json(FOLDER/'submission.json',record)
    print('Submitted isolated OBS source build test:',record['srcmd5'],flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--submit',action='store_true');args=parser.parse_args()
    os.umask(0o077)
    files=prepare();print('Prepared source inputs:',', '.join(p.name for p in files),flush=True)
    if args.submit:submit(files)

if __name__=='__main__':main()
