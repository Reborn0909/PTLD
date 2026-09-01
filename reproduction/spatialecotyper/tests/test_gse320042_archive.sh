#!/usr/bin/env bash
set -euo pipefail

root=/mnt/f/spatialecotyper_reproduction
raw_dir="$root/raw/gse320042"
manifest_dir="$root/archive/manifests"
tar_path="$raw_dir/GSE320042_RAW.tar"
filelist_path="$raw_dir/filelist.txt"
sha_path="$manifest_dir/GSE320042_RAW.tar.sha256"
members_path="$manifest_dir/GSE320042_RAW.tar.members.txt"
metadata_path="$manifest_dir/GSE320042.download-metadata.tsv"

test -f "$tar_path"
test -s "$filelist_path"
test -s "$sha_path"
test -s "$members_path"
test -s "$metadata_path"

expected_size=$(awk -F '\t' '$1 == "Archive" && $2 == "GSE320042_RAW.tar" { print $4; exit }' "$filelist_path")
test "$expected_size" = "4936970240"
test "$(stat -c %s "$tar_path")" = "$expected_size"
test -z "$(find "$raw_dir" "$manifest_dir" -maxdepth 1 -name '*.part' -print -quit)"

(
  cd "$raw_dir"
  sha256sum --check "$sha_path"
)

member_check=$(mktemp)
trap 'rm -f "$member_check"' EXIT
tar -tf "$tar_path" > "$member_check"
cmp -s "$member_check" "$members_path"
test -s "$member_check"

if awk 'BEGIN { bad = 0 }
  /^\// { bad = 1 }
  /(^|\/)\.\.($|\/)/ { bad = 1 }
  END { exit bad ? 0 : 1 }' "$member_check"; then
  echo "unsafe tar member path detected" >&2
  exit 1
fi

grep -Fq $'GSE320042_RAW.tar\thttps://ftp.ncbi.nlm.nih.gov/geo/series/GSE320nnn/GSE320042/suppl/GSE320042_RAW.tar' "$metadata_path"
grep -Fq $'filelist.txt\thttps://ftp.ncbi.nlm.nih.gov/geo/series/GSE320nnn/GSE320042/suppl/filelist.txt' "$metadata_path"

echo "GSE320042 archive: PASS"
