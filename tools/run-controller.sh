#!/bin/bash
set -euo pipefail
umask 077
project=$(cd "$(dirname "$0")/.." && pwd -P)
[[ $project == /home/dennweiss/telegram-obs ]]
export TMPDIR="$project/.state/tmp"
mkdir -p "$TMPDIR" "$project/.state/home"
[[ $(findmnt -n -o FSTYPE -T "$TMPDIR") != tmpfs ]]
obs_config=/home/dennweiss/antigravity-obs/.state/config
[[ -r "$obs_config/osc/oscrc" ]]
docker_gid=$(stat -c %g /var/run/docker.sock)
exec docker run --rm --name telegram-obs-controller \
 --user "$(id -u):$(id -g)" --group-add "$docker_gid" \
 --cpus=0.5 --memory=768m --pids-limit=256 --read-only \
 --volume "$project:$project" --workdir "$project" \
 --volume "$obs_config:$obs_config:ro" \
 --volume /var/run/docker.sock:/var/run/docker.sock \
 --volume /usr/bin/docker:/usr/local/bin/docker:ro \
 --env "HOME=$project/.state/home" --env "XDG_CONFIG_HOME=$obs_config" \
 --env "TMPDIR=$TMPDIR" --env TELEGRAM_CLOUD=1 \
 --env DOCKER_BUILDKIT=0 --env PYTHONUNBUFFERED=1 \
 telegram-obs-controller:1
