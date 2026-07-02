#!/usr/bin/env bash
set -euo pipefail

BASE=/data/zz2/National_model
MINIFORGE="$HOME/.local/miniforge3"
ENV_PREFIX="$HOME/.local/envs/cispo-2030"
INSTALLER=/tmp/Miniforge3-Linux-x86_64.sh
TRANSFERRED_INSTALLER="$BASE/incoming/Miniforge3-Linux-x86_64.sh"
URL=https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh

mkdir -p "$HOME/.local" "$HOME/.local/envs" "$BASE/manifests"
if [[ ! -x "$MINIFORGE/bin/conda" ]]; then
  if [[ -s "$TRANSFERRED_INSTALLER" ]]; then
    cp "$TRANSFERRED_INSTALLER" "$INSTALLER"
  else
    curl --fail --location --retry 3 --connect-timeout 15 --max-time 180 \
      --output "$INSTALLER" "$URL"
  fi
  sha256sum "$INSTALLER" > "$BASE/manifests/miniforge_installer.sha256"
  bash "$INSTALLER" -b -p "$MINIFORGE"
fi

if [[ -x "$ENV_PREFIX/bin/python" ]]; then
  "$MINIFORGE/bin/conda" env update \
    --prefix "$ENV_PREFIX" \
    --file "$BASE/repo/env/cispo-server.yml" \
    --prune
else
  "$MINIFORGE/bin/conda" env create \
    --prefix "$ENV_PREFIX" \
    --file "$BASE/repo/env/cispo-server.yml"
fi

"$ENV_PREFIX/bin/python" -m pip check
"$ENV_PREFIX/bin/python" - <<'PY'
import json
import platform
from importlib.metadata import version

packages = ["numpy", "pandas", "scipy", "netCDF4", "zarr", "numcodecs", "psutil"]
print(json.dumps({
    "python": platform.python_version(),
    "packages": {name: version(name) for name in packages},
}, indent=2))
PY

printf 'ENV_READY prefix=%s\n' "$ENV_PREFIX"
