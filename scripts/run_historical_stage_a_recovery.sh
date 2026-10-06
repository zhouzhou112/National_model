#!/usr/bin/env bash
# One detached offline recovery; no solver stage or automatic successor.
set -euo pipefail
umask 027
: "${RECOVERY_ROOT:?Set the isolated recovery root}"
: "${CISPO_SERVER_ENV:?Set the existing server environment file}"
source "$CISPO_SERVER_ENV"
unset CISPO_RAW_GRFR_ROOT
export CISPO_DATA_ROOT="$RECOVERY_ROOT/historical_model_data"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
CONTROL="$RECOVERY_ROOT/control"
OUTPUT="$RECOVERY_ROOT/recovered_8760"
test ! -e "$CONTROL"
test ! -e "$OUTPUT"
test -f "$RECOVERY_ROOT/validation_1h/validation_report.json"
"$CISPO_PYTHON" - "$RECOVERY_ROOT/validation_1h/validation_report.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))['status'] == 'PASS'
PY
mkdir "$CONTROL"
cd "$RECOVERY_ROOT/repo"
if pgrep -u "$(id -u)" -af '[r]un_cispo_2030_full_year.py|[r]un_cispo_planning_sequence.py|[r]ecover_historical_stage_a.py' > "$CONTROL/preexisting_model_processes.txt"; then
  exit 95
fi
date -Is > "$CONTROL/started_at.txt"
sha256sum scripts/recover_historical_stage_a.py "$RECOVERY_ROOT/path_mapping.json" > "$CONTROL/launch_checksums.sha256"
setsid /usr/bin/time -v -o "$CONTROL/time.txt" \
  "$CISPO_PYTHON" scripts/recover_historical_stage_a.py \
    --source-backup "$RECOVERY_ROOT/source_backup" \
    --path-map "$RECOVERY_ROOT/path_mapping.json" \
    --output-dir "$OUTPUT" > "$CONTROL/stdout.log" 2> "$CONTROL/stderr.log" &
run_pid=$!
printf '%s\n' "$run_pid" > "$CONTROL/run.pid"
printf 'timestamp\tmem_total_kib\tmem_available_kib\tswap_used_kib\tgroup_rss_kib\n' > "$CONTROL/resource_monitor.tsv"
guard=0
while kill -0 "$run_pid" 2>/dev/null; do
  read -r mt ma st sf < <(awk '/MemTotal:/ {mt=$2} /MemAvailable:/ {ma=$2} /SwapTotal:/ {st=$2} /SwapFree:/ {sf=$2} END {print mt,ma,st,sf}' /proc/meminfo)
  rss=$(ps -eo pgid=,rss= | awk -v pg="$run_pid" '$1==pg {s+=$2} END {print s+0}')
  printf '%s\t%s\t%s\t%s\t%s\n' "$(date -Is)" "$mt" "$ma" "$((st-sf))" "$rss" >> "$CONTROL/resource_monitor.tsv"
  if (( ma * 100 <= mt * 5 )); then
    guard=1
    printf '%s host95 memory guard triggered\n' "$(date -Is)" >> "$CONTROL/events.log"
    kill -TERM -- "-$run_pid" 2>/dev/null || true
    break
  fi
  sleep 2
done
set +e
wait "$run_pid"
rc=$?
set -e
printf '%s\n' "$rc" > "$CONTROL/return_code.txt"
printf '%s rc=%s host95_guard=%s\n' "$(date -Is)" "$rc" "$guard" >> "$CONTROL/events.log"
exit "$rc"
