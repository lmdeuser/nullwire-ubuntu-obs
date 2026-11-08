#!/bin/bash
set -euo pipefail
export TMPDIR=/var/tmp/nullwire-check
name=nullwire-buildtest
dpkg -i /input/package.deb
apt-get check
[[ $(dpkg-query -W -f='${Status}' "$name") == 'install ok installed' ]]
[[ -x /usr/lib/nullwire-buildtest/NullWire ]]
[[ -x /usr/bin/nullwire-buildtest ]]
desktop-file-validate /usr/share/applications/nullwire-buildtest.desktop
! ldd /usr/lib/nullwire-buildtest/NullWire | grep 'not found'
runuser -u tester -- xvfb-run -a dbus-run-session -- bash -c '
set -euo pipefail
export HOME=/home/tester QT_QPA_PLATFORM=xcb
mkdir -p "$HOME/profile"
/usr/bin/nullwire-buildtest -workdir "$HOME/profile" >"$HOME/app.log" 2>&1 &
app=$!
trap "kill $app 2>/dev/null || true" EXIT
for i in $(seq 1 60); do
 kill -0 "$app" || { cat "$HOME/app.log"; exit 1; }
 window=$(xwininfo -root -tree | python3 -c '\''import re,sys
for line in sys.stdin:
 m=re.search(r"^\s*(0x[0-9a-fA-F]+).*?(?:NullWire|Telegram).*?\s(\d+)x(\d+)[+-]",line)
 if m and int(m[2])>=320 and int(m[3])>=200:print(m[1]);break'\'')
 if [[ -n $window ]] && xwininfo -id "$window" | grep -q "Map State: IsViewable"; then
  sleep 3
  kill -0 "$app"
  xwininfo -id "$window" | grep -E "Width:|Height:|Map State:"
  exit 0
 fi
 sleep 1
done
cat "$HOME/app.log"
exit 1
'
dpkg -r "$name"
[[ ! -e /usr/bin/nullwire-buildtest ]]
dpkg -i /input/package.deb
apt-get check
echo 'PASS: source-built package installs, opens an offline visible window and reinstalls without GPU access'
