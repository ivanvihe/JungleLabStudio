#!/bin/bash
# Script para ejecutar JungleLabStudio con el editor visual

# Activar entorno virtual
source .venv/bin/activate

# Ejecutar aplicación
python src/main.py

# Instrucciones:
# - Presiona 'E' para activar/desactivar el editor visual
# - Presiona 'F1' para monitor MIDI
# - Usa 1-9,0 para cambiar entre presets
# - En el editor:
#   - Rueda del mouse: Zoom
#   - Botón central + drag: Pan
#   - Click izquierdo: Seleccionar/Mover nodos
#   - Shift + Click: Selección múltiple
#   - Delete/Backspace: Eliminar nodos seleccionados
#   - Menu Add > Node: Crear nuevos nodos
#   - Arrastra desde puerto a puerto: Crear conexiones
