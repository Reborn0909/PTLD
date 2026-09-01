#!/usr/bin/env bash
set -euo pipefail

data_root=/mnt/f/spatialecotyper_reproduction
manifest="$data_root/archive/manifests/tutorial-files.tsv"
downloaded="$data_root/archive/manifests/tutorial-files.downloaded.tsv"
checksums="$data_root/archive/manifests/tutorial-files.sha256"
raw_dir="$data_root/raw/tutorial"

[[ -s "$manifest" ]]
[[ $(( $(wc -l < "$manifest") - 1 )) -eq 21 ]]
[[ -s "$downloaded" ]]
[[ $(( $(wc -l < "$downloaded") - 1 )) -eq 21 ]]
[[ -s "$checksums" ]]
[[ $(wc -l < "$checksums") -eq 21 ]]

awk -F '\t' '
  NR == 1 {
    if ($1 != "file" || $6 != "bytes" || $7 != "sha256") exit 1
    next
  }
  length($7) != 64 || $7 !~ /^[0-9a-f]+$/ || $6 !~ /^[0-9]+$/ || $6 == 0 {
    exit 1
  }
' "$downloaded"

while IFS=$'\t' read -r filename _; do
  [[ "$filename" == "file" ]] && continue
  [[ -s "$raw_dir/$filename" ]]
done < "$manifest"

if find "$raw_dir" -maxdepth 1 -type f -name '*.part' -print -quit | grep -q .; then
  echo "partial tutorial downloads remain" >&2
  exit 1
fi

sha256sum --check "$checksums"
printf 'tutorial archive: PASS (21 files)\n'
