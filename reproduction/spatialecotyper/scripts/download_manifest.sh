#!/usr/bin/env bash
set -euo pipefail

data_root=${SPATIALECOTYPER_DATA_ROOT:-/mnt/f/spatialecotyper_reproduction}
manifest="$data_root/archive/manifests/tutorial-files.tsv"
raw_dir="$data_root/raw/tutorial"
header_dir="$data_root/archive/manifests/tutorial-headers"
downloaded="$data_root/archive/manifests/tutorial-files.downloaded.tsv"
checksums="$data_root/archive/manifests/tutorial-files.sha256"
metadata_tmp="$downloaded.part"
checksums_tmp="$checksums.part"

[[ -s "$manifest" ]]
mkdir -p "$raw_dir" "$header_dir"
printf 'file\turl\tused_by\tsource_commit\tetag\tbytes\tsha256\tlast_modified\tdownloaded_utc\n' \
  > "$metadata_tmp"
: > "$checksums_tmp"

header_value() {
  local header_file=$1
  local key=$2
  local value
  value=$(grep -i "^${key}:" "$header_file" 2>/dev/null | tail -n 1 | cut -d: -f2- || true)
  value=${value//$'\r'/}
  value=${value//$'\t'/ }
  printf '%s' "${value# }"
}

while IFS=$'\t' read -r filename url used_by source_commit; do
  [[ "$filename" == "file" ]] && continue
  [[ -n "$filename" && -n "$url" ]]
  dest="$raw_dir/$filename"
  partial="$dest.part"
  headers="$header_dir/$filename.headers"
  header_partial="$headers.part"

  if [[ ! -s "$dest" ]]; then
    printf 'Downloading %s\n' "$filename"
    curl --fail --location --retry 5 --retry-all-errors \
      --continue-at - \
      --dump-header "$header_partial" \
      --output "$partial" \
      "$url"
    [[ -s "$partial" ]]
    mv -- "$partial" "$dest"
    mv -- "$header_partial" "$headers"
  else
    printf 'Using archived %s\n' "$filename"
  fi

  [[ -s "$dest" ]]
  bytes=$(stat --printf='%s' "$dest")
  sha256=$(sha256sum "$dest" | awk '{print $1}')
  etag=""
  last_modified=""
  if [[ -s "$headers" ]]; then
    etag=$(header_value "$headers" ETag)
    last_modified=$(header_value "$headers" Last-Modified)
  fi
  downloaded_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$filename" "$url" "$used_by" "$source_commit" "$etag" "$bytes" \
    "$sha256" "$last_modified" "$downloaded_utc" >> "$metadata_tmp"
  printf '%s  %s\n' "$sha256" "$dest" >> "$checksums_tmp"
done < "$manifest"

[[ $(( $(wc -l < "$metadata_tmp") - 1 )) -eq 21 ]]
[[ $(wc -l < "$checksums_tmp") -eq 21 ]]
mv -- "$metadata_tmp" "$downloaded"
mv -- "$checksums_tmp" "$checksums"

printf 'official tutorial download: PASS (21 files)\n'
