#!/bin/bash
# Compute-node connectivity probe only: no model data, no optimization, no license content.
# Submit with: sbatch cloud_wls_network_probe.sbatch
# The historical proxy is intentionally tested as a reachability diagnostic;
# it is not assumed to be valid.
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_384
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --job-name=cispo_wls_netprobe
#SBATCH --output=cloud_wls_network_probe-%j.out
#SBATCH --error=cloud_wls_network_probe-%j.err

set -euo pipefail

TARGET="https://token.gurobi.com/"
HISTORICAL_PROXY="http://172.16.110.3:8888"

echo "PROBE_HOST $(hostname)"
echo "PROBE_START_UTC $(date -u +%FT%TZ)"
echo "DNS"
getent hosts token.gurobi.com || true

echo "DIRECT_HTTP"
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  curl -sS -o /dev/null -w 'DIRECT_STATUS %{http_code} REMOTE_IP %{remote_ip}\n' \
  --connect-timeout 10 --max-time 20 "$TARGET" || true

echo "HISTORICAL_PROXY_HTTP"
HTTPS_PROXY="$HISTORICAL_PROXY" https_proxy="$HISTORICAL_PROXY" \
  curl -sS -o /dev/null -w 'PROXY_STATUS %{http_code} REMOTE_IP %{remote_ip}\n' \
  --connect-timeout 10 --max-time 20 "$TARGET" || true

echo "PROBE_END_UTC $(date -u +%FT%TZ)"
