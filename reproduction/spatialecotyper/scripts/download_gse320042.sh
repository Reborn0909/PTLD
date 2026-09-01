#!/usr/bin/env bash
set -euo pipefail

root=/mnt/f/spatialecotyper_reproduction
raw_dir="$root/raw/gse320042"
manifest_dir="$root/archive/manifests"
log_dir="$root/results/logs"
base_url=https://ftp.ncbi.nlm.nih.gov/geo/series/GSE320nnn/GSE320042/suppl
tar_name=GSE320042_RAW.tar
filelist_name=filelist.txt
tar_url="$base_url/$tar_name"
filelist_url="$base_url/$filelist_name"
tar_path="$raw_dir/$tar_name"
filelist_path="$raw_dir/$filelist_name"
sha_path="$manifest_dir/$tar_name.sha256"
members_path="$manifest_dir/$tar_name.members.txt"
metadata_path="$manifest_dir/GSE320042.download-metadata.tsv"
log_path="$log_dir/download_gse320042.log"

mkdir -p "$raw_dir" "$manifest_dir" "$log_dir"
touch "$log_path"

log() {
  printf '%s\t%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*" | tee -a "$log_path"
}

if [[ -e "$sha_path" || -e "$members_path" || -e "$metadata_path" ]]; then
  test -s "$tar_path"
  test -s "$filelist_path"
  test -s "$sha_path"
  test -s "$members_path"
  test -s "$metadata_path"

  expected_size=$(awk -F '\t' -v target="$tar_name" \
    '$1 == "Archive" && $2 == target { print $4; exit }' "$filelist_path")
  test "$expected_size" = "$(stat -c %s "$tar_path")"
  (
    cd "$raw_dir"
    sha256sum --check "$sha_path"
  )

  expected_filelist_sha=$(awk -F '\t' -v target="$filelist_name" \
    'NR > 1 && $1 == target { print $4; exit }' "$metadata_path")
  test -n "$expected_filelist_sha"
  test "$expected_filelist_sha" = "$(sha256sum "$filelist_path" | awk '{ print $1 }')"

  locked_members=$(mktemp)
  trap 'rm -f -- "$locked_members"' EXIT
  tar -tf "$tar_path" > "$locked_members"
  cmp -s "$locked_members" "$members_path"
  log "GSE320042 archive baseline: PASS (locked)"
  exit 0
fi

download_atomic() {
  local url=$1
  local destination=$2
  local part="${destination}.part"
  local headers="${destination}.headers"

  if [[ -s "$destination" ]]; then
    log "reuse existing $(basename "$destination") ($(stat -c %s "$destination") bytes)"
  else
    local attempt=1
    local max_attempts=20
    while (( attempt <= max_attempts )); do
      local offset=0
      if [[ -f "$part" ]]; then
        offset=$(stat -c %s "$part")
      fi
      log "download $(basename "$destination") attempt=$attempt resume_offset=$offset from $url"
      if curl \
        --fail \
        --location \
        --continue-at - \
        --speed-limit 1024 \
        --speed-time 60 \
        --output "$part" \
        "$url" 2>&1 | tee -a "$log_path"; then
        break
      fi
      log "transfer interrupted at $(stat -c %s "$part") bytes"
      attempt=$((attempt + 1))
      if (( attempt > max_attempts )); then
        echo "download failed after $max_attempts attempts: $url" >&2
        exit 1
      fi
      sleep 5
    done
    test -s "$part"
    mv -- "$part" "$destination"
  fi

  curl --fail --location --silent --show-error --head "$url" > "${headers}.part"
  mv -- "${headers}.part" "$headers"
}

download_atomic "$filelist_url" "$filelist_path"

expected_size=$(awk -F '\t' -v target="$tar_name" '$1 == "Archive" && $2 == target { print $4; exit }' "$filelist_path")
if [[ ! "$expected_size" =~ ^[0-9]+$ ]] || (( expected_size <= 4500000000 )); then
  echo "invalid archive size in official filelist: $expected_size" >&2
  exit 1
fi

download_atomic "$tar_url" "$tar_path"
observed_size=$(stat -c %s "$tar_path")
if [[ "$observed_size" != "$expected_size" ]]; then
  echo "archive size mismatch: expected $expected_size, observed $observed_size" >&2
  exit 1
fi

log "compute SHA-256 for $tar_name"
(
  cd "$raw_dir"
  sha256sum "$tar_name" > "${sha_path}.part"
)
mv -- "${sha_path}.part" "$sha_path"

log "validate tar and record member list"
tar -tf "$tar_path" > "${members_path}.part"
test -s "${members_path}.part"
if awk 'BEGIN { bad = 0 }
  /^\// { bad = 1 }
  /(^|\/)\.\.($|\/)/ { bad = 1 }
  END { exit bad ? 0 : 1 }' "${members_path}.part"; then
  echo "unsafe tar member path detected" >&2
  exit 1
fi
mv -- "${members_path}.part" "$members_path"

header_value() {
  local path=$1
  local field=$2
  awk -v field="$field" 'BEGIN { IGNORECASE = 1 }
    index($0, field ":") == 1 {
      sub("^[^:]+:[[:space:]]*", "")
      sub("\r$", "")
      value = $0
    }
    END { print value }' "$path"
}

tar_sha=$(awk '{ print $1 }' "$sha_path")
filelist_sha=$(sha256sum "$filelist_path" | awk '{ print $1 }')
downloaded_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
{
  printf 'file\turl\tbytes\tsha256\trecorded_utc\tetag\tlast_modified\n'
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$tar_name" "$tar_url" "$observed_size" "$tar_sha" "$downloaded_utc" \
    "$(header_value "${tar_path}.headers" ETag)" \
    "$(header_value "${tar_path}.headers" Last-Modified)"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$filelist_name" "$filelist_url" "$(stat -c %s "$filelist_path")" \
    "$filelist_sha" "$downloaded_utc" \
    "$(header_value "${filelist_path}.headers" ETag)" \
    "$(header_value "${filelist_path}.headers" Last-Modified)"
} > "${metadata_path}.part"
mv -- "${metadata_path}.part" "$metadata_path"

log "GSE320042 archive ready: $observed_size bytes, sha256=$tar_sha"
