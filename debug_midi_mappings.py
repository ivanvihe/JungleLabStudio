#!/usr/bin/env python3
"""
Script de depuración para verificar que los mappings MIDI basados en canales
se cargan correctamente.
"""

import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def debug_midi_mappings():
    print("INICIANDO DEBUG DE MAPPINGS MIDI")
    print("=" * 60)

    config_file = 'config/midi_mappings.json'
    print(f"\n1.  VERIFICANDO ARCHIVO PRINCIPAL: {config_file}")

    if os.path.exists(config_file):
        print(f"    Archivo existe: {config_file}")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)

            print("    JSON válido")
            print(f"    Total mappings: {len(mappings)}")

            print("\n    MAPPINGS ENCONTRADOS:")
            for i, (visual, note) in enumerate(mappings.items()):
                if i >= 10:
                    print(f"      ... y {len(mappings) - 10} más")
                    break
                print(f"      {visual}: note {note}")

            sample_visual = next(iter(mappings.keys()), None)
            if sample_visual:
                note = mappings[sample_visual]
                print(f"\n    MAPPING POR CANAL PARA '{sample_visual}':")
                for deck, channel in zip(['A', 'B', 'C', 'D'], range(12, 16)):
                    midi_key = f"note_on_ch{channel}_note{note}"
                    print(f"      Deck {deck} -> {midi_key}")
        except Exception as e:
            print(f"    Error leyendo archivo: {e}")
    else:
        print(f"    Archivo NO existe: {config_file}")

    print("\n" + "=" * 60)
    print("DEBUG COMPLETADO")


if __name__ == '__main__':
    debug_midi_mappings()
