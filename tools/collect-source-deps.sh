#!/bin/bash
set -euo pipefail
project=$(cd "$(dirname "$0")/.." && pwd -P)
mkdir -p "$project/.state"
export TMPDIR=/srv/temp/telegram
base=/srv/temp/telegram/deps
fetch() {
 local name=$1 url=$2 revision=$3
 [[ ! -e "$base/$name" ]]
 git init -q "$base/$name"
 git -C "$base/$name" remote add origin "$url"
 git -C "$base/$name" fetch -q --depth=1 origin "$revision"
 git -C "$base/$name" checkout -q --detach FETCH_HEAD
 [[ $(git -C "$base/$name" rev-parse HEAD) == "$revision" ]]
 printf 'Fetched %s at pinned revision\n' "$name"
}
fetch patches https://github.com/desktop-app/patches.git a59fc82462fb2987e9f0ee1498e2db694410ae81
fetch tg_owt https://github.com/desktop-app/tg_owt.git 020feec5c040fdae2cf752c2c2be62ddde7c236d
git -C "$base/tg_owt" submodule update --init --recursive --depth=1 > "$project/.state/dependency-fetch.log" 2>&1
fetch tde2e https://github.com/tdlib/td.git 51743dfd01dff6179e2d8f7095729caa4e2222e9
fetch tlottie https://github.com/dkaraush/tlottie.git 92df98dc209bc39b1e567ec74a8c86a0af5239de
fetch wallet-engine https://github.com/i582/wallet-engine.git e59e0d89d7ee90c388bf36e3334c5b276f396697
fetch rnnoise https://github.com/xiph/rnnoise.git 904a876dce1f9ab8860c0a5000ed151f9f6eef58
printf 'Pinned source checkout complete; vendor Cargo and RNNoise model before creating the offline archive\n'
