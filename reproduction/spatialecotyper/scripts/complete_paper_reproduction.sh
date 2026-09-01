#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd -- "$script_dir/../../.." && pwd -P)
data_root=${1:-/mnt/f/spatialecotyper_reproduction}
status_dir="$data_root/results/reproducibility"
status_path="$status_dir/paper-completion-status.tsv"
mkdir -p "$status_dir"

started_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
finish_status=FAIL
finish_step=initialization
on_exit() {
  code=$?
  completed_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
  temp="${status_path}.part"
  printf 'status\tlast_step\texit_code\tstarted_utc\tcompleted_utc\n' > "$temp"
  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$finish_status" "$finish_step" "$code" "$started_utc" "$completed_utc" >> "$temp"
  mv -- "$temp" "$status_path"
}
trap on_exit EXIT

cd "$repo_root"

finish_step=download_public_materials
bash reproduction/spatialecotyper/scripts/download_paper_data.sh \
  --root "$data_root" --phase all-actionable --jobs 3 --connections 16

finish_step=validate_file_integrity
python3 reproduction/spatialecotyper/scripts/validate_paper_files.py --root "$data_root"

finish_step=validate_sample_coverage
python3 reproduction/spatialecotyper/scripts/validate_paper_samples.py --root "$data_root"

activation_file="$data_root/results/environment/activation.env"
test -s "$activation_file"
mamba_root=$(awk -F= '$1 == "MAMBA_ROOT_PREFIX" { print $2; exit }' "$activation_file")
micromamba_bin=$(awk -F= '$1 == "MICROMAMBA_EXE" { print $2; exit }' "$activation_file")
env_prefix=$(awk -F= '$1 == "ENV_PREFIX" { print $2; exit }' "$activation_file")
test -n "$mamba_root"
test -x "$micromamba_bin"
test -d "$env_prefix"

run_r() {
  "$micromamba_bin" --no-rc --root-prefix "$mamba_root" \
    run --prefix "$env_prefix" Rscript "$1"
}

finish_step=prepare_generated_inputs
run_r reproduction/spatialecotyper/scripts/prepare_paper_inputs.R

finish_step=audit_generated_objects
run_r reproduction/spatialecotyper/scripts/audit_gse320042_objects.R

finish_step=run_generated_spatial_deconvolution
run_r reproduction/spatialecotyper/scripts/run_paper_reproduction.R

finish_step=compare_supplementary_table_s17
run_r reproduction/spatialecotyper/scripts/compare_paper_outputs.R

finish_step=regenerate_reproducibility_boundary
run_r reproduction/spatialecotyper/scripts/audit_reproducibility.R
python3 reproduction/spatialecotyper/scripts/write_paper_data_inventory.py \
  --root "$data_root" \
  --output docs/reproduction/spatialecotyper-paper-data-inventory.md

finish_step=final_audit
bash reproduction/spatialecotyper/scripts/final_audit.sh

finish_step=complete
finish_status=PASS
printf 'paper reproduction completion: PASS\n'
