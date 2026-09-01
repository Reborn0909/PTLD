#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
data_root=${1:-/mnt/f/spatialecotyper_reproduction}
status_dir="$data_root/results/reproducibility"
log_dir="$data_root/results/logs"
pid_path="$status_dir/paper-completion.pid"
status_path="$status_dir/paper-completion-status.tsv"
log_path="$log_dir/paper-completion.log"
mkdir -p "$status_dir" "$log_dir"

if [[ -s "$pid_path" ]]; then
  existing_pid=$(<"$pid_path")
  if [[ "$existing_pid" =~ ^[0-9]+$ ]] && kill -0 "$existing_pid" 2>/dev/null; then
    printf 'paper reproduction completion already running: pid=%s\n' "$existing_pid"
    exit 0
  fi
fi

started_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
temp="${status_path}.part"
printf 'status\tlast_step\texit_code\tstarted_utc\tcompleted_utc\n' > "$temp"
printf 'RUNNING\tdetached_runner\t\t%s\t\n' "$started_utc" >> "$temp"
mv -- "$temp" "$status_path"

nohup bash "$script_dir/complete_paper_reproduction.sh" "$data_root" \
  >> "$log_path" 2>&1 < /dev/null &
runner_pid=$!
printf '%s\n' "$runner_pid" > "$pid_path"
printf 'paper reproduction completion launched: pid=%s log=%s\n' \
  "$runner_pid" "$log_path"
