#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
script="$repo/reproduction/spatialecotyper/scripts/download_paper_data.sh"
test -x "$script"

tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp/archive/manifests" "$tmp/results/reproducibility" "$tmp/source"
printf 'abc' > "$tmp/source/a.bin"
printf 'pause' > "$tmp/source/paused.bin"
size_a=$(stat -c %s "$tmp/source/a.bin")
size_paused=$(stat -c %s "$tmp/source/paused.bin")

{
  printf 'source_record_id\taccession\trepository\tfile_name\tdownload_url\tsize_bytes\tchecksum_type\tchecksum\tlicense\taccess_status\tresolver_note\n'
  printf 'A\t\tTENX\tSample__a.bin\tfile://%s\t%s\t\t\t\tPUBLIC_API\ttest\n' "$tmp/source/a.bin" "$size_a"
  printf 'B\t\tTENX\tDuplicate__a.bin\tfile://%s\t%s\t\t\t\tPUBLIC_API\ttest duplicate\n' "$tmp/source/a.bin" "$size_a"
  printf 'C\tPRJEB1\tENA\tpaused.bin\tfile://%s\t%s\t\t\t\tPUBLIC_API\tpaused\n' "$tmp/source/paused.bin" "$size_paused"
  printf 'D\t\tGITHUB\tunknown.zip\tfile://%s\t0\t\t\t\tPUBLIC_API\tunknown\n' "$tmp/source/a.bin"
} > "$tmp/archive/manifests/paper-downloads.tsv"

{
  printf 'source_record_id\taccession\taccess_status\tresolved_file_count\tknown_bytes\tunknown_size_files\tsource_gate\tfree_bytes\tknown_total_bytes\tactionable_total_bytes\tglobal_gate\treason\n'
  printf 'A\t\tPUBLIC_API\t1\t3\t0\tPASS\t1000\t100\t3\tPASS\ttest\n'
  printf 'B\t\tPUBLIC_API\t1\t3\t0\tPASS\t1000\t100\t3\tPASS\ttest\n'
  printf 'C\tPRJEB1\tPUBLIC_API\t1\t5\t0\tPAUSE_OVER_100GB\t1000\t100\t3\tPASS\tpaused\n'
  printf 'D\t\tPUBLIC_API\t1\t0\t1\tPASS\t1000\t100\t3\tPASS\tunknown\n'
} > "$tmp/results/reproducibility/paper-download-capacity.tsv"

"$script" --root "$tmp" --phase all-actionable --jobs 2

manifest="$tmp/archive/manifests/paper-file-sha256.tsv"
skipped="$tmp/archive/manifests/paper-download-skipped.tsv"
test -s "$manifest"
test -s "$skipped"
grep -Fq $'expected_checksum\tchecksum_type\tsha256' "$manifest"
test "$(( $(wc -l < "$manifest") - 1 ))" -eq 1
test "$(( $(wc -l < "$skipped") - 1 ))" -eq 2
path=$(awk -F '\t' 'NR == 2 { print $11 }' "$manifest")
test -s "$path"
test "$(stat -c %s "$path")" -eq 3
expected=$(sha256sum "$tmp/source/a.bin" | awk '{ print $1 }')
test "$(awk -F '\t' 'NR == 2 { print $10 }' "$manifest")" = "$expected"
grep -Fq $'C\tPRJEB1\tPAUSED_SOURCE_GATE' "$skipped"
grep -Fq $'D\t\tUNKNOWN_SIZE' "$skipped"

echo "paper download archive test: PASS"
