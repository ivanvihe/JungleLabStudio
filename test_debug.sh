#!/usr/bin/env bash
# Script para ejecutar la app con debug completo

# Limpiar cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# Ejecutar app con timeout y capturar todo
export PYTHONDONTWRITEBYTECODE=1
export DISPLAY="${DISPLAY:-:0}"
export GDK_BACKEND="${GDK_BACKEND:-x11}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
unset WAYLAND_DISPLAY
export LIBDECOR_DISABLE=1

echo "=== Starting JungleLabStudio with full debug logging ==="
echo "DISPLAY=$DISPLAY"
echo ""

timeout 10 .venv/bin/python -u -m src.main 2>&1 | tee debug_output.log

echo ""
echo "=== Execution completed ==="
echo "Full log saved to debug_output.log"
