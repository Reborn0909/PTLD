#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd -- "$script_dir/../../.." && pwd -P)
data_root=/mnt/f/spatialecotyper_reproduction
official_repo=/mnt/c/Users/Microsoft/Documents/EBV开题/external/spatialecotyper-official
official_commit=48c2c846781d3a312771021c1a2ef5fc383700c5
activation_file="$data_root/results/environment/activation.env"
audit_dir="$data_root/results/reproducibility"
audit_path="$audit_dir/final-audit.txt"

mkdir -p "$audit_dir"
audit_temp=$(mktemp "$audit_dir/final-audit.txt.part.XXXXXX")
trap 'rm -f -- "$audit_temp"' EXIT

audit_body() {
  cd "$repo_root"

  pass() {
    printf 'PASS\t%s\n' "$1"
  }

  printf 'SpatialEcoTyper final audit\n'
  printf 'audit_utc\t%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  printf 'official_commit\t%s\n' "$official_commit"

  test -d "$official_repo/.git"
  test "$(git -C "$official_repo" rev-parse HEAD)" = "$official_commit"
  test -z "$(git -c core.autocrlf=true -C "$official_repo" status --porcelain)"
  pass "official source commit and clean worktree"

  source_bundle="$data_root/archive/source/spatialecotyper-official-$official_commit.bundle"
  test -s "$source_bundle"
  git -C "$official_repo" bundle verify "$source_bundle"
  sha256sum --check "$data_root/archive/manifests/source-archives.sha256"
  pass "official source bundle and archived source hashes"

  bash reproduction/spatialecotyper/tests/test_layout.sh
  bash reproduction/spatialecotyper/tests/test_tutorial_archive.sh
  bash reproduction/spatialecotyper/tests/test_gse320042_archive.sh
  bash reproduction/spatialecotyper/tests/test_paper_download_archive.sh
  python3 reproduction/spatialecotyper/tests/test_paper_source_lock.py
  python3 reproduction/spatialecotyper/tests/test_paper_data_manifest.py
  python3 reproduction/spatialecotyper/tests/test_paper_download_resolution.py
  python3 reproduction/spatialecotyper/tests/test_paper_file_validation.py
  python3 reproduction/spatialecotyper/tests/test_paper_sample_validation.py

  test -s "$activation_file"
  mamba_root=$(awk -F= '$1 == "MAMBA_ROOT_PREFIX" { print $2; exit }' "$activation_file")
  micromamba_bin=$(awk -F= '$1 == "MICROMAMBA_EXE" { print $2; exit }' "$activation_file")
  env_prefix=$(awk -F= '$1 == "ENV_PREFIX" { print $2; exit }' "$activation_file")
  test -n "$mamba_root"
  test -x "$micromamba_bin"
  test -d "$env_prefix"
  pass "fixed WSL environment paths"

  run_r_test() {
    "$micromamba_bin" --no-rc --root-prefix "$mamba_root" \
      run --prefix "$env_prefix" Rscript "$1"
  }

  run_r_test reproduction/spatialecotyper/tests/test_source_lock.R
  run_r_test reproduction/spatialecotyper/tests/test_environment.R
  run_r_test reproduction/spatialecotyper/tests/test_tutorial_runs.R
  run_r_test reproduction/spatialecotyper/tests/test_reproducibility_matrix.R
  run_r_test reproduction/spatialecotyper/tests/test_ptld_adapter.R
  run_r_test reproduction/spatialecotyper/tests/test_paper_inputs.R
  run_r_test reproduction/spatialecotyper/tests/test_gse_object_audit.R
  run_r_test reproduction/spatialecotyper/tests/test_paper_reproduction.R
  run_r_test reproduction/spatialecotyper/tests/test_compare_paper_outputs.R

  file_validation="$data_root/results/reproducibility/paper-file-validation.tsv"
  sample_comparison="$data_root/results/paper_reproduction/generated_visium_deconvolution/supplementary-table-s17-comparison.tsv"
  test -s "$file_validation"
  test -s "$sample_comparison"
  awk -F '\t' 'NR == 1 { for (i=1; i<=NF; i++) if ($i == "validation_status") c=i; next }
    $c != "PASS" { failed += 1 } END { if (!c || failed) exit 1 }' "$file_validation"
  awk -F '\t' 'NR == 1 { for (i=1; i<=NF; i++) if ($i == "comparison_status") c=i; next }
    $c != "PASS" { failed += 1 } END { if (!c || NR != 18 || failed) exit 1 }' "$sample_comparison"
  pass "paper file integrity and Supplementary Table 17 sample counts"

  matrix_path="$data_root/results/reproducibility/paper-computation-matrix.tsv"
  test -s "$matrix_path"
  printf 'Reproducibility boundaries\n'
  awk -F '\t' '
    NR > 1 && $3 == "BLOCKED_NOT_PUBLIC" {
      printf "BLOCKED_NOT_PUBLIC\t%s\t%s\n", $1, $6
      blocked += 1
    }
    END {
      if (blocked != 3) exit 1
    }
  ' "$matrix_path"
  pass "three unpublished computation boundaries are explicit"

  printf 'Disk usage by F-drive layer\n'
  printf 'layer\tbytes\n'
  for layer in raw archive work cache results; do
    test -d "$data_root/$layer"
    bytes=$(du -sb "$data_root/$layer" | awk '{ print $1 }')
    test "$bytes" -ge 0
    printf '%s\t%s\n' "$layer" "$bytes"
  done
  pass "F-drive layer byte inventory"

  test -z "$(find "$data_root/raw" "$data_root/archive" -type f \( -name '*.part' -o -name '*.aria2' \) -print -quit)"
  pass "no partial or aria2 control files in raw or archive"

  printf 'FINAL_AUDIT\tPASS\n'
}

set +e
(
  set -euo pipefail
  audit_body
) > "$audit_temp" 2>&1
audit_status=$?
set -e

if ! cat "$audit_temp"; then
  printf 'Final audit report could not be read: %s\n' "$audit_temp" >&2
  trap - EXIT
  exit 1
fi

if [[ "$audit_status" -ne 0 ]]; then
  printf 'Final audit failed; partial report retained at %s\n' "$audit_temp" >&2
  trap - EXIT
  exit "$audit_status"
fi

mv -- "$audit_temp" "$audit_path"
trap - EXIT
printf 'Final audit report: %s\n' "$audit_path"
