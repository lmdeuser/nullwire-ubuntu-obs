#!/bin/bash
set -euo pipefail
export TMPDIR="${TMPDIR:-/srv/temp/telegram}"
mkdir -p "$TMPDIR"
[[ $(findmnt -n -o FSTYPE -T "$TMPDIR") != tmpfs ]]
package=$(realpath "$1")
[[ $2 == telegram-desktop ]]
[[ $(dpkg-deb -f "$package" Package) == "$2" ]]
[[ $(dpkg-deb -f "$package" Version) == "$3" ]]
[[ $(dpkg-deb -f "$package" Architecture) == amd64 ]]
limits=()
if [[ ${DOCKER_BUILDKIT:-1} == 0 ]]; then limits=(--memory=768m --cpu-period=100000 --cpu-quota=50000); fi
docker build "${limits[@]}" -t telegram-obs-verifier:26.04 -f "$(dirname "$0")/../packaging/verifier.Dockerfile" "$(dirname "$0")/.."
docker run --rm --network none --cpus=0.5 --memory=768m --pids-limit=256 --shm-size=256m \
 --mount "type=bind,src=$package,dst=/input/package.deb,readonly" \
 --env "PACKAGE_VERSION=$3" telegram-obs-verifier:26.04
