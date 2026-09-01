#!/usr/bin/env bash
set -euo pipefail

root=/mnt/f/spatialecotyper_reproduction
phase=all-actionable
jobs=3
manifest=""
capacity=""

while (( $# > 0 )); do
  case "$1" in
    --root) root=$2; shift 2 ;;
    --phase) phase=$2; shift 2 ;;
    --jobs) jobs=$2; shift 2 ;;
    --manifest) manifest=$2; shift 2 ;;
    --capacity) capacity=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

manifest=${manifest:-$root/archive/manifests/paper-downloads.tsv}
capacity=${capacity:-$root/results/reproducibility/paper-download-capacity.tsv}
output_manifest="$root/archive/manifests/paper-file-sha256.tsv"
skipped_manifest="$root/archive/manifests/paper-download-skipped.tsv"
log_dir="$root/results/logs/paper-downloads"
cache_dir="$root/cache"

[[ -s "$manifest" && -s "$capacity" ]]
[[ "$jobs" =~ ^[1-9][0-9]*$ ]]
case "$phase" in
  generated|spatial|scrna|bulk|all-actionable) ;;
  *) echo "invalid phase: $phase" >&2; exit 2 ;;
esac

mkdir -p "$root/raw/public_spatial" "$root/raw/public_scrna" "$root/raw/public_bulk" \
  "$root/archive/manifests" "$log_dir" "$cache_dir"
rows_dir=$(mktemp -d "$cache_dir/paper-download.XXXXXX")
cleanup() {
  case "$rows_dir" in
    "$cache_dir"/paper-download.*) rm -rf -- "$rows_dir" ;;
    *) echo "refusing unsafe cleanup: $rows_dir" >&2 ;;
  esac
}
trap cleanup EXIT

declare -A paused=()
while IFS= read -r source; do
  [[ -n "$source" ]] && paused["$source"]=1
done < <(awk -F '\t' 'NR > 1 && $7 != "PASS" { print $1 }' "$capacity")

phase_matches() {
  local source=$1
  case "$phase" in
    all-actionable) return 0 ;;
    generated) [[ "$source" == GENERATED-* ]] ;;
    spatial) [[ "$source" == TableS1-* ]] ;;
    scrna) [[ "$source" == TableS2-* ]] ;;
    bulk) [[ "$source" == TableS15-* ]] ;;
  esac
}

target_path() {
  local source=$1 accession=$2 repository=$3 filename=$4
  [[ "$filename" != */* && "$filename" != *\\* && "$filename" != *..* ]]
  case "$repository" in
    TENX)
      [[ "$filename" == *__* ]]
      local sample=${filename%%__*}
      local suffix=${filename#*__}
      printf '%s/raw/public_spatial/tenx/%s/%s' "$root" "$sample" "$suffix"
      ;;
    NCBI_GEO)
      if [[ "$source" == GENERATED-* ]]; then
        printf '%s/raw/gse320042/%s' "$root" "$filename"
      elif [[ "$source" == TableS1-* ]]; then
        printf '%s/raw/public_spatial/geo/%s/%s' "$root" "$accession" "$filename"
      elif [[ "$source" == TableS2-* ]]; then
        printf '%s/raw/public_scrna/geo/%s/%s' "$root" "$accession" "$filename"
      else
        printf '%s/raw/public_bulk/geo/%s/%s' "$root" "$accession" "$filename"
      fi
      ;;
    ZENODO) printf '%s/raw/public_spatial/zenodo/%s' "$root" "$filename" ;;
    SPATIALRESEARCH) printf '%s/raw/public_spatial/spatialresearch/%s/%s' "$root" "$source" "$filename" ;;
    GITHUB) printf '%s/raw/public_spatial/github/%s/%s' "$root" "$source" "$filename" ;;
    ENA) printf '%s/raw/public_bulk/ena/%s/%s' "$root" "$accession" "$filename" ;;
    *) printf '%s/raw/paper_generated/%s/%s' "$root" "$source" "$filename" ;;
  esac
}

printf 'source_record_id\taccession\treason\tfile_name\tdownload_url\n' > "$skipped_manifest.part"
queue="$rows_dir/queue.tsv"
: > "$queue"
declare -A seen_url=()
index=0

while IFS=$'\034' read -r source accession repository filename url size checksum_type checksum license access_status note; do
  phase_matches "$source" || continue
  if [[ -n "${paused[$source]:-}" ]]; then
    printf '%s\t%s\tPAUSED_SOURCE_GATE\t%s\t%s\n' "$source" "$accession" "$filename" "$url" >> "$skipped_manifest.part"
    continue
  fi
  if [[ ! "$size" =~ ^[0-9]+$ ]] || (( size == 0 )); then
    printf '%s\t%s\tUNKNOWN_SIZE\t%s\t%s\n' "$source" "$accession" "$filename" "$url" >> "$skipped_manifest.part"
    continue
  fi
  if [[ -n "${seen_url[$url]:-}" ]]; then
    continue
  fi
  seen_url["$url"]=1
  destination=$(target_path "$source" "$accession" "$repository" "$filename")
  index=$((index + 1))
  printf '%06d\034%s\034%s\034%s\034%s\034%s\034%s\034%s\034%s\034%s\n' \
    "$index" "$source" "$accession" "$repository" "$filename" "$url" "$size" "$checksum_type" "$checksum" "$destination" >> "$queue"
done < <(awk -F '\t' 'NR > 1 {
  for (i = 1; i <= 11; i++) {
    gsub(/\034/, " ", $i)
    printf "%s%s", $i, (i == 11 ? "\n" : "\034")
  }
}' "$manifest")
mv -- "$skipped_manifest.part" "$skipped_manifest"

download_one() {
  local item_index=$1 source=$2 accession=$3 repository=$4 filename=$5
  local url=$6 expected_size=$7 checksum_type=$8 expected_checksum=$9 destination=${10}
  local part="${destination}.part"
  local result="$rows_dir/${item_index}.tsv"
  local log="$log_dir/${item_index}-${repository}.log"
  mkdir -p "$(dirname "$destination")"
  local status=VERIFIED_EXISTING

  if [[ -e "$destination" ]]; then
    [[ -f "$destination" ]]
    local existing_size
    existing_size=$(stat -c %s "$destination")
    if [[ "$existing_size" != "$expected_size" ]]; then
      echo "existing size mismatch: $destination expected=$expected_size actual=$existing_size" >&2
      return 1
    fi
  else
    status=DOWNLOADED_VERIFIED
    local attempt=1
    while (( attempt <= 20 )); do
      local offset=0
      [[ -f "$part" ]] && offset=$(stat -c %s "$part")
      printf '%s attempt=%s offset=%s url=%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$attempt" "$offset" "$url" >> "$log"
      if [[ "$url" =~ ^https?:// ]] && command -v aria2c >/dev/null 2>&1; then
        if aria2c --continue=true --auto-file-renaming=false --allow-overwrite=true \
            --max-connection-per-server=8 --split=8 --min-split-size=1M \
            --file-allocation=none --max-tries=4 --retry-wait=5 --timeout=60 \
            --summary-interval=30 --console-log-level=notice \
            --dir="$(dirname "$part")" --out="$(basename "$part")" "$url" >> "$log" 2>&1; then
          break
        fi
      elif curl --fail --location --retry 3 --retry-all-errors --continue-at - \
          --speed-limit 1024 --speed-time 60 --output "$part" "$url" >> "$log" 2>&1; then
        break
      fi
      attempt=$((attempt + 1))
      if (( attempt > 20 )); then
        echo "download failed after 20 attempts: $url" >&2
        return 1
      fi
      sleep 5
    done
    [[ -f "$part" ]]
    local observed_part
    observed_part=$(stat -c %s "$part")
    if [[ "$observed_part" != "$expected_size" ]]; then
      echo "downloaded size mismatch: $part expected=$expected_size actual=$observed_part" >&2
      return 1
    fi
    mv -- "$part" "$destination"
  fi

  local actual_size actual_sha downloaded_utc
  actual_size=$(stat -c %s "$destination")
  actual_sha=$(sha256sum "$destination" | awk '{ print $1 }')
  if [[ "$checksum_type" == md5 && -n "$expected_checksum" ]]; then
    local actual_md5
    actual_md5=$(md5sum "$destination" | awk '{ print $1 }')
    [[ "$actual_md5" == "$expected_checksum" ]]
  fi
  downloaded_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$source" "$accession" "$repository" "$filename" "$url" "$expected_size" "$actual_size" \
    "$expected_checksum" "$actual_sha" "$destination" "$status" "$downloaded_utc" > "$result"
}

active=0
failed=0
while IFS=$'\034' read -r item_index source accession repository filename url size checksum_type checksum destination; do
  download_one "$item_index" "$source" "$accession" "$repository" "$filename" "$url" "$size" \
    "$checksum_type" "$checksum" "$destination" &
  active=$((active + 1))
  if (( active >= jobs )); then
    if ! wait -n; then failed=1; fi
    active=$((active - 1))
  fi
done < "$queue"
while (( active > 0 )); do
  if ! wait -n; then failed=1; fi
  active=$((active - 1))
done
(( failed == 0 )) || { echo "one or more downloads failed" >&2; exit 1; }

printf 'source_record_id\taccession\trepository\tfile_name\tdownload_url\texpected_bytes\tactual_bytes\texpected_checksum\tsha256\tlocal_path\tstatus\tdownloaded_utc\n' \
  > "$output_manifest.part"
for result in "$rows_dir"/[0-9][0-9][0-9][0-9][0-9][0-9].tsv; do
  [[ -e "$result" ]] && cat "$result" >> "$output_manifest.part"
done
mv -- "$output_manifest.part" "$output_manifest"

printf 'paper data download: PASS files=%s skipped=%s phase=%s\n' \
  "$(( $(wc -l < "$output_manifest") - 1 ))" "$(( $(wc -l < "$skipped_manifest") - 1 ))" "$phase"
