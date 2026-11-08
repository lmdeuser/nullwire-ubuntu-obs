#!/usr/bin/env python3
"""OBS primitives and historical repack experiment; production source release is gated."""
import argparse
import dataclasses
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import shlex
import subprocess
import tarfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.state'
STABLE='home:dwolfF:telegram'
STAGING=STABLE+':staging'
REPO='xUbuntu_26.04'
ARCH='x86_64'
REVISION='obs2'
GATE_VERSION=1
NAME='telegram-desktop'
BUILD_DEPS='debhelper-compat (= 13), python3, binutils, libglib2.0-0t64, libx11-6, libxcb1, libfontconfig1, libfreetype6, libegl1, libgl1, libxkbcommon0, libxkbcommon-x11-0, libdbus-1-3, libpangocairo-1.0-0, libpango-1.0-0, libpangoft2-1.0-0, libcairo2'

@dataclasses.dataclass(frozen=True)
class Release:
    name: str
    version: str
    url: str
    digest: str
    source_url: str
    source_digest: str


def discover(data):
    version=data.get('tag_name','').removeprefix('v')
    if data.get('draft') or data.get('prerelease') or not re.fullmatch(r'\d+\.\d+\.\d+',version):
        raise ValueError('not an unambiguous stable release')
    def asset(filename):
        found=[a for a in data['assets'] if a['name']==filename]
        if len(found)!=1:raise ValueError('missing or ambiguous asset')
        a=found[0]
        expected=f'https://github.com/telegramdesktop/tdesktop/releases/download/v{version}/{filename}'
        if a['browser_download_url']!=expected:raise ValueError('unofficial asset URL')
        digest=a.get('digest') or ''
        if not re.fullmatch('sha256:[0-9a-f]{64}',digest):raise ValueError('missing SHA256 metadata')
        return expected,digest[7:]
    url,digest=asset(f'td-setup-linux-x64-{version}.tar.xz')
    source,source_digest=asset(f'tdesktop-{version}-full.tar.gz')
    return Release(NAME,version,url,digest,source,source_digest)


def validate_members(members):
    seen=set()
    for m in members:
        p=PurePosixPath(m.name)
        if p.is_absolute() or '..' in p.parts or not p.parts or m.name in seen:
            raise ValueError('unsafe or duplicate archive path')
        seen.add(m.name)
        if not (m.isdir() or m.isfile()) or m.mode & 0o6000:
            raise ValueError('links, special or privileged members are forbidden')


def project_xml(staging):
    name=STAGING if staging else STABLE
    build='' if staging else '<build><disable/></build>'
    publish='<publish><disable/></publish>' if staging else '<publish><enable/></publish>'
    target=f'<releasetarget project="{STABLE}" repository="{REPO}" trigger="manual"/>' if staging else ''
    return f'<project name="{name}"><title>Telegram Desktop for Ubuntu 26.04</title><description>Telegram Desktop official upstream archives repackaged as native debs. Independent packaging. Corresponding full source archives are provided in OBS. Staging must pass offline installation and GUI tests before release.</description><person userid="dwolfF" role="maintainer"/>{build}{publish}<repository name="{REPO}">{target}<path project="Ubuntu:26.04" repository="update"/><path project="Ubuntu:26.04" repository="universe-update"/><arch>{ARCH}</arch></repository></project>'

def newer(candidate, current):
    return tuple(map(int,candidate.split('.'))) > tuple(map(int,current.split('.')))

def needs_update(version,current):
    if current is None:return True
    if newer(version,current['version']):return True
    if version!=current['version']:return False
    previous=re.search(r'[+-]obs(\d+)$',current.get('deb_version',''))
    if not previous:raise ValueError('unknown existing packaging revision')
    return int(REVISION.removeprefix('obs'))>int(previous[1])

def sha256(path):
    with open(path,'rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def verify_sha256(path, expected):
    if sha256(path) != expected:
        raise ValueError('SHA256 mismatch')

def save_json(path, data):
    tmp = path.with_suffix('.new')
    with tmp.open('w') as f:
        json.dump(data,f,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)

def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, text=True, timeout=3600, **kwargs)

def osc(*args):
    return run(['osc','--setopt',f'cookiejar={STATE}/osc-cookiejar',*args],capture_output=True).stdout

def api(path, method='GET', data=None, file=None):
    args=['api','-X',method]
    if data is not None:args += ['-d',data]
    if file is not None:args += ['-T',str(file)]
    return osc(*args,path)

def download(url, dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    part=dest.with_suffix(dest.suffix+'.part')
    with urllib.request.urlopen(url,timeout=120) as response, part.open('wb') as f:
        if urllib.parse.urlparse(response.url).scheme != 'https':raise ValueError('insecure redirect')
        shutil.copyfileobj(response,f,1024*1024)
    os.replace(part,dest)

def init_obs():
    # Dedicated projects only; never rewrite a pre-existing unrelated project.
    for staging in [False, True]:
        name=STAGING if staging else STABLE
        try:
            current=api(f'/source/{name}/_meta')
        except subprocess.CalledProcessError as e:
            if '404' not in e.stderr:raise
            api(f'/source/{name}/_meta','PUT',project_xml(staging))
        else:
            if 'Telegram Desktop official upstream archives' not in current:
                raise ValueError(f'project {name} not owned by this pipeline')
        api(f'/source/{name}/_config','PUT','PublishFlags: nofailedpackages\n')
    print('OBS projects ready',flush=True)

def submit(release):
    folder, record=prepare(release)
    name=release.name
    try:api(f'/source/{STAGING}/{name}/_meta')
    except subprocess.CalledProcessError as e:
        if '404' not in e.stderr:raise
        api(f'/source/{STAGING}/{name}/_meta','PUT',f'<package name="{name}" project="{STAGING}"><title>{name}</title><description>Managed stable upstream package</description></package>')
    files=[folder/f for f in record['source_files']]
    listing=ET.Element('directory')
    for file in files:
        # Upload to transaction area; publish one source revision with commitfilelist.
        api(f'/source/{STAGING}/{name}/{file.name}?rev=repository','PUT',file=file)
        ET.SubElement(listing,'entry',name=file.name,md5=hashlib.md5(file.read_bytes()).hexdigest())
    response=ET.fromstring(api(f'/source/{STAGING}/{name}?cmd=commitfilelist&comment=automated-stable-update','POST',ET.tostring(listing,encoding='unicode')))
    record['srcmd5']=response.attrib['srcmd5']
    store_record(f'{name}-candidate.json',record)
    print(f'{name}: submitted {record["deb_version"]} srcmd5={record["srcmd5"]}',flush=True)

def build_succeeded(xml,name):
    root=ET.fromstring(xml)
    return any(r.attrib.get('repository')==REPO and r.attrib.get('arch')==ARCH and r.attrib.get('dirty')!='true' and any(s.attrib.get('package')==name and s.attrib.get('code')=='succeeded' for s in r.findall('status')) for r in root.findall('result'))

def require_source_record(record):
    expected=dict(build_mode='source',api_identity='production',hwaccel_default=True,brand='NullWire')
    if any(record.get(key)!=value for key,value in expected.items()):
        raise ValueError('NullWire requires a production source build with hardware decoding enabled')


def require_release(success, revision, tested):
    if not all([success,revision,tested]):raise ValueError('release gates not satisfied')

def require_same_revision(before,after):
    if not before or before != after:raise ValueError('source changed during verification')

def source_md5(name):
    return ET.fromstring(api(f'/source/{STAGING}/{name}')).attrib['srcmd5']

def expanded_md5(name):
    return ET.fromstring(api(f'/source/{STAGING}/{name}?expand=1')).attrib['srcmd5']

def build_revision(xml):
    revision=ET.fromstring(xml).findtext('srcmd5')
    if not revision:raise ValueError('OBS buildinfo is missing source revision')
    return revision

def fetch_binary(name,filename,dest):
    part=dest.with_suffix(dest.suffix+'.part')
    with part.open('wb') as output:
        run(['osc','--setopt',f'cookiejar={STATE}/osc-cookiejar','api',f'/build/{STAGING}/{REPO}/{ARCH}/{name}/{filename}'],stdout=output,stderr=subprocess.PIPE)
    os.replace(part,dest)

def reconcile(name):
    candidate=STATE/f'{name}-candidate.json'
    if not candidate.exists():return
    record=json.loads(candidate.read_text())
    require_source_record(record)
    previous=STATE/f'{name}-stable.json'
    if previous.exists() and json.loads(previous.read_text()).get('srcmd5')==record['srcmd5'] and json.loads(previous.read_text()).get('gate_version',0)>=GATE_VERSION:return
    result=api(f'/build/{STAGING}/_result?package={name}')
    if not build_succeeded(result,name):
        print(f'{name}: staging not ready; stable unchanged',flush=True);return
    require_same_revision(record['srcmd5'],source_md5(name))
    # Bind success to the actual build, not merely current source metadata.
    info=build_revision(api(f'/build/{STAGING}/{REPO}/{ARCH}/{name}/_buildinfo'))
    require_same_revision(expanded_md5(name),info)
    directory=ET.fromstring(api(f'/build/{STAGING}/{REPO}/{ARCH}/{name}'))
    filename=f'{name}_{record["deb_version"]}_amd64.deb'
    if filename not in {b.attrib.get('filename') for b in directory}:raise ValueError('expected binary absent')
    dest=STATE/'binaries'/record['srcmd5']/filename;dest.parent.mkdir(parents=True,exist_ok=True)
    # osc getbinaries streams binary data safely, without decoding it as text.
    fetch_binary(name,filename,dest)
    artifact_sha=sha256(dest)
    extracted=dest.parent/'extracted';extracted.mkdir(exist_ok=True)
    run(['dpkg-deb','-x',dest,extracted])
    verify_sha256(extracted/'usr/lib/telegram-desktop/Telegram',record['executable_sha256'])
    run([ROOT/'tools/verify-deb.sh',dest,name,record['deb_version']])
    verify_sha256(dest,artifact_sha)
    require_same_revision(record['srcmd5'],source_md5(name))
    current_info=build_revision(api(f'/build/{STAGING}/{REPO}/{ARCH}/{name}/_buildinfo'))
    require_same_revision(info,current_info)
    # Re-download the server artifact to ensure a concurrent rebuild did not replace it.
    check=STATE/'recheck';check.mkdir(exist_ok=True)
    fetch_binary(name,filename,check/filename)
    verify_sha256(check/filename,artifact_sha)
    require_release(True,True,True)
    osc('release',STAGING,name,'-r',REPO,'-a',ARCH,'--target-project',STABLE,'--target-repository',REPO,'--no-delay')
    record.update(binary_sha256=artifact_sha,verified_at=int(time.time()),gate_version=GATE_VERSION)
    store_record(previous.name,record)
    print(f'{name}: released verified {record["deb_version"]}',flush=True)

def load_remote_state():
    package='pipeline-state'
    try:api(f'/source/{STAGING}/{package}/_meta')
    except subprocess.CalledProcessError as e:
        if '404' not in e.stderr:raise
        api(f'/source/{STAGING}/{package}/_meta','PUT',f'<package name="{package}" project="{STAGING}"><title>Pipeline provenance</title><description>Non-secret candidate and release records</description><build><disable/></build><publish><disable/></publish></package>')
    listing=ET.fromstring(api(f'/source/{STAGING}/{package}'))
    for entry in listing:
        filename=entry.attrib['name']
        if re.fullmatch(r'telegram-desktop-(candidate|stable)\.json',filename):
            save_json(STATE/filename,json.loads(api(f'/source/{STAGING}/{package}/{filename}')))

def store_record(filename,record):
    if os.environ.get('TELEGRAM_CLOUD')=='1':
        api(f'/source/{STAGING}/pipeline-state/{filename}','PUT',json.dumps(record,indent=2)+'\n')
    save_json(STATE/filename,record)

def wait_for_builds(timeout=2700,interval=30):
    deadline=time.monotonic()+timeout
    while True:
        pending=[]
        for name in ['telegram-desktop']:
            candidate=STATE/f'{name}-candidate.json';stable=STATE/f'{name}-stable.json'
            if not candidate.exists():continue
            record=json.loads(candidate.read_text())
            if stable.exists() and json.loads(stable.read_text()).get('srcmd5')==record['srcmd5'] and json.loads(stable.read_text()).get('gate_version',0)>=GATE_VERSION:continue
            result=api(f'/build/{STAGING}/_result?package={name}')
            statuses=ET.fromstring(result).findall('.//status')
            errors=[s.attrib['code'] for s in statuses if s.attrib.get('package')==name and s.attrib.get('code') in ['failed','broken','unresolvable','disabled','excluded']]
            # Briefly allow OBS scheduler to notice a newly committed revision.
            if errors and time.time()-record['prepared_at']>180:
                raise ValueError(f'{name}: OBS build {errors}; stable unchanged')
            if build_succeeded(result,name):reconcile(name)
            else:pending.append(name)
        if not pending:return
        if time.monotonic()>=deadline:raise TimeoutError(f'OBS build wait timed out: {pending}')
        print('Waiting for OBS: '+', '.join(pending),flush=True)
        time.sleep(interval)


def prepare(release):
    version=release.version+'-'+REVISION
    folder=STATE/'sources'/version
    folder.mkdir(parents=True,exist_ok=True)
    upstream=STATE/'upstream';upstream.mkdir(exist_ok=True)
    assets=[]
    for url,digest,target in [
        (release.url,release.digest,f'{NAME}_{release.version}.orig.tar.xz'),
        (release.source_url,release.source_digest,f'{NAME}_{release.version}.orig-source.tar.gz')]:
        archive=upstream/Path(urllib.parse.urlsplit(url).path).name
        if not archive.exists():download(url,archive)
        verify_sha256(archive,digest)
        dest=folder/target
        if not dest.exists():os.link(archive,dest)
        verify_sha256(dest,digest)
        assets.append(dest)
    with tarfile.open(assets[0]) as tar:
        members=tar.getmembers();validate_members(members)
        executable_sha256=hashlib.file_digest(tar.extractfile('Telegram/Telegram'),'sha256').hexdigest()
        if {m.name for m in members if m.isfile()}!={'Telegram/Telegram','Telegram/Updater'}:
            raise ValueError('unexpected upstream archive layout')
    # Full upstream source is distributed alongside binary and Debian recipe.
    debian=folder/'work/debian';(debian/'source').mkdir(parents=True,exist_ok=True)
    (debian/'source/format').write_text('3.0 (quilt)\n')
    shutil.copy2(ROOT/'packaging/package.py',debian/'package.py')
    (debian/'control').write_text(f'''Source: {NAME}
Section: net
Priority: optional
Maintainer: dwolfF <dwolfF@users.noreply.build.opensuse.org>
Build-Depends: {BUILD_DEPS}
Standards-Version: 4.7.0
Homepage: https://desktop.telegram.org/
Rules-Requires-Root: no

Package: {NAME}
Architecture: amd64
Depends: ${{shlibs:Depends}}, ${{misc:Depends}}, ca-certificates, xdg-utils, libegl1, libgl1, libxkbcommon0, libxkbcommon-x11-0, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-render-util0, libxcb-xinerama0, libxcb-randr0, libxcb-shape0, libxcb-xfixes0, libxcb-sync1, libxcb-render0, libxcb-shm0
Recommends: libgtk-3-0t64, libasound2t64, libpulse0, libsecret-1-0
Description: Telegram Desktop messenger (official upstream binary)
 Independent native Debian packaging of the official Linux amd64 release.
 Application updates use the signed OBS APT repository.
''')
    (debian/'changelog').write_text(f'''{NAME} ({version}) resolute; urgency=medium

  * Package upstream {release.version}; preserve binary, ship full sources.
  * Disable in-app self-update using upstream externalupdater marker.

 -- dwolfF <dwolfF@users.noreply.build.opensuse.org>  Mon, 09 Nov 2026 00:00:00 +0500
''')
    (debian/'copyright').write_text(f'''Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Telegram Desktop
Source: {release.source_url}
Disclaimer: Independent packaging; not affiliated with Telegram.

Files: *
Copyright: 2014-2026 John Preston and Telegram Desktop contributors
License: GPL-3.0 with OpenSSL exception
 Full upstream LICENSE and LEGAL notices are included in this package.
 The full upstream source including bundled dependencies is included in
 the OBS source package as {assets[1].name}.

Files: debian/*
Copyright: 2026 dwolfF
License: GPL-3.0-or-later
 On Debian systems the GPL-3 text is in /usr/share/common-licenses/GPL-3.
''')
    (debian/'rules').write_text(f'''#!/usr/bin/make -f
export TMPDIR := $(CURDIR)/.build-tmp
%:
\tmkdir -p "$(TMPDIR)"
\tdh $@
override_dh_auto_build:
\tpython3 debian/package.py verify
override_dh_auto_test:
\tpython3 debian/package.py verify
override_dh_auto_install:
\tpython3 debian/package.py install
override_dh_shlibdeps:
\tdpkg-shlibdeps -Tdebian/{NAME}.substvars -edebian/{NAME}/usr/lib/{NAME}/Telegram
override_dh_strip:
override_dh_dwz:
''')
    (debian/'rules').chmod(0o755)
    debtar=folder/f'{NAME}_{version}.debian.tar.xz'
    with tarfile.open(debtar,'w:xz') as tar:tar.add(debian,arcname='debian')
    files=assets+[debtar]
    dsc=folder/f'{NAME}_{version}.dsc'
    dsc.write_text(f'''Format: 3.0 (quilt)
Source: {NAME}
Binary: {NAME}
Architecture: amd64
Version: {version}
Maintainer: dwolfF <dwolfF@users.noreply.build.opensuse.org>
Build-Depends: {BUILD_DEPS}
Files:
'''+''.join(f' {hashlib.md5(f.read_bytes()).hexdigest()} {f.stat().st_size} {f.name}\n' for f in files)+'Checksums-Sha256:\n'+''.join(f' {sha256(f)} {f.stat().st_size} {f.name}\n' for f in files))
    services=ET.Element('services')
    for url,digest,asset in [(release.url,release.digest,assets[0]),(release.source_url,release.source_digest,assets[1])]:
        fetch=ET.SubElement(services,'service',name='download_url')
        parsed=urllib.parse.urlsplit(url)
        for key,value in [('protocol','https'),('host',parsed.netloc),('path',parsed.path),('filename',asset.name)]:
            ET.SubElement(fetch,'param',name=key).text=value
        check=ET.SubElement(services,'service',name='verify_file')
        for key,value in [('file','_service:download_url:'+asset.name),('verifier','sha256'),('checksum',digest)]:
            ET.SubElement(check,'param',name=key).text=value
    (folder/'_service').write_text(ET.tostring(services,encoding='unicode')+'\n')
    return folder,dict(name=NAME,version=release.version,deb_version=version,url=release.url,sha256=release.digest,source_url=release.source_url,source_archive_sha256=release.source_digest,executable_sha256=executable_sha256,source_sha256=sha256(debtar),source_files=[dsc.name,debtar.name,'_service'],prepared_at=int(time.time()))


def cycle():
    if os.environ.get('TELEGRAM_CLOUD')=='1':load_remote_state()
    run(['python3','-m','unittest','discover','-s','tests','-v'],cwd=ROOT)
    reconcile(NAME)
    data=json.load(urllib.request.urlopen('https://api.github.com/repos/telegramdesktop/tdesktop/releases/latest',timeout=60))
    release=discover(data)
    path=STATE/f'{NAME}-candidate.json'
    current=json.loads(path.read_text()) if path.exists() else None
    if current and release.version==current['version']:
        if release.url!=current['url'] or release.digest!=current['sha256'] or release.source_digest!=current['source_archive_sha256']:
            raise ValueError('upstream archives changed without version bump')
    if needs_update(release.version,current):submit(release)
    else:print('No newer stable version',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['init-obs','prepare','cycle','cloud-cycle','reconcile'])
    args=parser.parse_args()
    if args.action!='init-obs':
        raise SystemExit('Historical repack pipeline is disabled. NullWire source build is being prepared; no release is allowed.')
    os.umask(0o077);STATE.mkdir(mode=0o700,exist_ok=True)
    with (STATE/'pipeline.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.action=='init-obs':init_obs()
        elif args.action=='prepare':print(prepare(discover(json.loads((STATE/'upstream/release.json').read_text())))[1])
        elif args.action=='reconcile':reconcile(NAME)
        else:
            cycle()
            if args.action=='cloud-cycle':wait_for_builds()

if __name__=='__main__':main()
