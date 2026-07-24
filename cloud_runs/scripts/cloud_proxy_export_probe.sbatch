#!/bin/bash
# Verifies that the account .bashrc exports the proxy on a compute node.
# No model data, Gurobi environment, or optimization is used.
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_384
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --job-name=cispo_proxy_export
#SBATCH --output=cloud_proxy_export_probe-%j.out
#SBATCH --error=cloud_proxy_export_probe-%j.err

set -eo pipefail

unset http_proxy https_proxy ftp_proxy HTTP_PROXY HTTPS_PROXY FTP_PROXY || true
source "$HOME/.bashrc"
set -u

EXPECTED_PROXY="http://172.16.110.3:8888"
test "${http_proxy:-}" = "$EXPECTED_PROXY"
test "${https_proxy:-}" = "$EXPECTED_PROXY"
test "${ftp_proxy:-}" = "$EXPECTED_PROXY"

echo "PROXY_EXPORT_COMPUTE_PASS"
echo "PROBE_HOST $(hostname)"
curl -sS -o /dev/null -w 'PROXY_STATUS %{http_code} REMOTE_IP %{remote_ip}\n' \
  --connect-timeout 10 --max-time 20 https://token.gurobi.com/ || true
