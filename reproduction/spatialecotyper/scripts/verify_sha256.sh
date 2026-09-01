#!/usr/bin/env bash
set -euo pipefail

data_root=${SPATIALECOTYPER_DATA_ROOT:-/mnt/f/spatialecotyper_reproduction}
checksums=${1:-$data_root/archive/manifests/tutorial-files.sha256}

[[ -s "$checksums" ]]
sha256sum --check "$checksums"
