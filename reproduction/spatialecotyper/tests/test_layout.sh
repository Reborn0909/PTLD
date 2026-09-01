#!/usr/bin/env bash
set -euo pipefail

root=/mnt/f/spatialecotyper_reproduction
required=(
  raw archive work cache results
  raw/tutorial raw/gse320042
  archive/source archive/manifests
  work/tutorials work/gse320042
  cache/micromamba cache/renv cache/downloads
  results/tutorials results/reproducibility results/ptld_adapter
  results/environment results/logs
)

for relative in "${required[@]}"; do
  test -d "$root/$relative" || {
    printf 'missing directory: %s\n' "$root/$relative" >&2
    exit 1
  }
done

printf 'F-drive layout: PASS (%d directories)\n' "${#required[@]}"
