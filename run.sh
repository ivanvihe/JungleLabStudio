#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Missing virtualenv at $VENV. Create it with: python -m venv .venv && .venv/bin/python -m pip install -r requirements.txt" >&2
  exit 1
fi

export GDK_BACKEND="${GDK_BACKEND:-x11}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
export DISPLAY="${DISPLAY:-:0}"
# Force XWayland path to avoid libdecor warnings on some Wayland setups
unset WAYLAND_DISPLAY
export LIBDECOR_DISABLE=1

# If you want native Wayland GLFW instead, comment the above block and set:
# export GLFW_USE_WAYLAND=1
# export QT_QPA_PLATFORM=wayland

exec "$VENV/bin/python" -m src.main "$@"
