#!/bin/bash
# Demo automático del sistema minimal

echo "======================================"
echo "MINIMAL GENERATIVE VISUAL ENGINE DEMO"
echo "======================================"
echo ""
echo "Este demo mostrará la forma generativa"
echo "respondiendo automáticamente."
echo ""
echo "Observa cómo:"
echo "- K (kick) pulsa la forma"
echo "- H (hat) crea glitch"
echo "- T (tom1) cambia geometría"
echo "- Y (tom2) modula rotación"
echo ""
echo "Presiona Ctrl+C para salir"
echo ""
sleep 2

source venv/bin/activate
python3 visuales.py
