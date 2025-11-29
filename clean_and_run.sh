#!/usr/bin/env bash
# Script para limpiar cache y ejecutar la app

echo "🧹 Limpiando cache de Python..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

echo "🚀 Ejecutando JungleLabStudio..."
exec ./run.sh "$@"
