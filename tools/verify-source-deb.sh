#!/bin/bash
set -euo pipefail
export TMPDIR="${TMPDIR:-/srv/temp/telegram}"
mkdir -p "$TMPDIR"
[[ -w $TMPDIR && $(findmnt -n -o FSTYPE -T "$TMPDIR") != tmpfs ]]
project=$(cd "$(dirname "$0")/.." && pwd -P)
package=$(realpath "$1")
artifact_sha256=$(sha256sum "$package" | cut -d' ' -f1)
[[ $(dpkg-deb -f "$package" Package) == nullwire-buildtest ]]
[[ $(dpkg-deb -f "$package" Architecture) == amd64 ]]
context="$project/.state/source-verifier"
mkdir -p "$context"
cp -- "$package" "$context/package.deb"
if [[ $(sha256sum "$context/package.deb" | cut -d' ' -f1) != "$artifact_sha256" || $(sha256sum "$package" | cut -d' ' -f1) != "$artifact_sha256" ]]; then
    echo "Artifact changed while preparing verification" >&2
    exit 1
fi
cp "$project/tools/source-container-check.sh" "$context/container-check"
cat > "$context/Dockerfile" <<'EOF'
FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive TMPDIR=/var/tmp/nullwire-check
RUN mkdir -p "$TMPDIR" && chmod 1777 "$TMPDIR" && apt-get update && apt-get install -y --no-install-recommends ca-certificates xvfb xauth x11-utils dbus-x11 desktop-file-utils python3 procps && useradd --create-home tester
COPY package.deb /input/package.deb
RUN apt-get install -y --no-install-recommends /input/package.deb && dpkg -r nullwire-buildtest && rm -rf /var/lib/apt/lists/*
COPY container-check /usr/local/bin/container-check
ENTRYPOINT ["/usr/local/bin/container-check"]
EOF
docker build -t nullwire-source-verifier:26.04 "$context"
docker run --rm --network none --cpus=0.75 --memory=1g --pids-limit=256 --shm-size=256m nullwire-source-verifier:26.04
[[ $(sha256sum "$package" | cut -d' ' -f1) == "$artifact_sha256" ]]
[[ $(sha256sum "$context/package.deb" | cut -d' ' -f1) == "$artifact_sha256" ]]
printf 'Verified exact source-built artifact SHA256: %s\n' "$artifact_sha256"
