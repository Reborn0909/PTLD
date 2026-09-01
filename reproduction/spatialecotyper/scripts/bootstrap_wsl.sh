#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd -- "$script_dir/../../.." && pwd -P)
data_root=/mnt/f/spatialecotyper_reproduction
official_repo=/mnt/c/Users/Microsoft/Documents/EBV开题/external/spatialecotyper-official
env_name=spatialecotyper-1.0.2
micromamba_bin="$HOME/.local/bin/micromamba"
export MAMBA_ROOT_PREFIX="$HOME/.local/share/micromamba-spatialecotyper"
env_prefix="$MAMBA_ROOT_PREFIX/envs/$env_name"
official_commit=48c2c846781d3a312771021c1a2ef5fc383700c5
source_bundle="$data_root/archive/source/spatialecotyper-official-$official_commit.bundle"

mkdir -p \
  "$data_root/raw/tutorial" "$data_root/raw/gse320042" \
  "$data_root/archive/source" "$data_root/archive/manifests" \
  "$data_root/work/tutorials" "$data_root/work/gse320042" \
  "$data_root/cache/micromamba" "$data_root/cache/renv" \
  "$data_root/cache/downloads" \
  "$data_root/results/tutorials" "$data_root/results/reproducibility" \
  "$data_root/results/ptld_adapter" "$data_root/results/environment" \
  "$data_root/results/logs"

if [[ ! -f "$source_bundle" ]]; then
  git -C "$official_repo" bundle create "$source_bundle.part" --all
  mv -- "$source_bundle.part" "$source_bundle"
fi
git -C "$official_repo" bundle verify "$source_bundle"

if [[ ! -x "$micromamba_bin" ]]; then
  archive="$data_root/cache/downloads/micromamba-linux-64.tar.bz2"
  mkdir -p "$(dirname -- "$micromamba_bin")"
  curl --fail --location --retry 5 --retry-all-errors \
    --continue-at - \
    --output "$archive.part" \
    https://micro.mamba.pm/api/micromamba/linux-64/latest
  mv -- "$archive.part" "$archive"
  tar -xjf "$archive" -C "$(dirname -- "$micromamba_bin")" \
    --strip-components=1 bin/micromamba
  chmod 0755 "$micromamba_bin"
  sha256sum "$archive" > \
    "$data_root/archive/manifests/micromamba-linux-64.tar.bz2.sha256"
fi

"$micromamba_bin" --version | tee \
  "$data_root/results/environment/micromamba-version.txt"

if ! "$micromamba_bin" --no-rc --root-prefix "$MAMBA_ROOT_PREFIX" \
  run --prefix "$env_prefix" Rscript -e \
  'quit(status = if (getRversion() == "4.4.1") 0L else 1L)' \
  >/dev/null 2>&1; then
  "$micromamba_bin" --no-rc --root-prefix "$MAMBA_ROOT_PREFIX" \
    create --yes --prefix "$env_prefix" \
    --override-channels --channel conda-forge \
    --file "$repo_root/reproduction/spatialecotyper/config/environment.yml" \
    2>&1 | tee "$data_root/results/logs/environment-solve.log"
fi

"$micromamba_bin" --no-rc --root-prefix "$MAMBA_ROOT_PREFIX" \
  run --prefix "$env_prefix" Rscript \
  "$repo_root/reproduction/spatialecotyper/scripts/record_environment.R" \
  "$official_repo" "$data_root"

sha256sum "$source_bundle" > \
  "$data_root/archive/manifests/source-archives.sha256"
presto_archive="$data_root/cache/downloads/presto-7636b3d0465c468c35853f82f1717d3a64b3c8f6.tar.gz"
if [[ -f "$presto_archive" ]]; then
  sha256sum "$presto_archive" >> \
    "$data_root/archive/manifests/source-archives.sha256"
fi

"$micromamba_bin" --no-rc --root-prefix "$MAMBA_ROOT_PREFIX" \
  list --prefix "$env_prefix" --explicit > \
  "$data_root/archive/manifests/explicit-conda-spec.txt"
"$micromamba_bin" --no-rc --root-prefix "$MAMBA_ROOT_PREFIX" \
  env export --prefix "$env_prefix" > \
  "$data_root/archive/manifests/environment-resolved.yml"

printf 'MAMBA_ROOT_PREFIX=%s\n' "$MAMBA_ROOT_PREFIX" > \
  "$data_root/results/environment/activation.env"
printf 'MICROMAMBA_EXE=%s\n' "$micromamba_bin" >> \
  "$data_root/results/environment/activation.env"
printf 'ENV_NAME=%s\n' "$env_name" >> \
  "$data_root/results/environment/activation.env"
printf 'ENV_PREFIX=%s\n' "$env_prefix" >> \
  "$data_root/results/environment/activation.env"

printf 'WSL environment bootstrap: PASS\n'
