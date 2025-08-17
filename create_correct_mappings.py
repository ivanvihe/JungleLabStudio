#!/usr/bin/env python3
"""
Script para crear un archivo config/midi_mappings.json correcto desde cero
Ejecuta este script para generar los mappings MIDI correctos
"""

import json
import os

def create_correct_midi_mappings():
    """Crear mapeos MIDI correctos basados en los documentos proporcionados"""

    print("🔧 CREANDO MAPPINGS MIDI CORRECTOS...")

    # Cargar los mappings desde el archivo raíz
    with open('midi_mappings.json', 'r', encoding='utf-8') as f:
        mappings = json.load(f)

    # Crear directorio config si no existe
    config_dir = 'config'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"✅ Directorio '{config_dir}/' creado")

    # Guardar archivo
    output_file = 'config/midi_mappings.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)

        print(f"✅ Archivo creado: {output_file}")
        print(f"📊 Total mappings: {len(mappings)}")

        # Verificar algunos mappings críticos
        print(f"\n🔍 VERIFICANDO MAPPINGS CRÍTICOS:")
        critical_tests = [
            ("note_on_ch0_note37", "Wire Terrain", "A"),
            ("note_on_ch0_note60", "Mobius Band", "B"),
            ("note_on_ch0_note55", "Wire Terrain", "B"),
            ("note_on_ch0_note38", "Abstract Lines", "A"),
            ("note_on_ch0_note50", "A to B", "Mix")
        ]

        for midi_key, expected_preset, expected_deck in critical_tests:
            found = False
            for action_id, mapping_data in mappings.items():
                if isinstance(mapping_data, dict) and mapping_data.get('midi') == midi_key:
                    action_type = mapping_data.get('type')
                    params = mapping_data.get('params', {})

                    if action_type == 'load_preset':
                        deck_id = params.get('deck_id')
                        preset_name = params.get('preset_name')
                        if deck_id == expected_deck and preset_name == expected_preset:
                            print(f"   ✅ {midi_key}: Deck {deck_id} -> {preset_name}")
                        else:
                            print(f"   ❌ {midi_key}: Expected Deck {expected_deck} -> {expected_preset}, got Deck {deck_id} -> {preset_name}")
                    elif action_type == 'crossfade_action':
                        preset = params.get('preset')
                        if preset == expected_preset:
                            print(f"   ✅ {midi_key}: Mix -> {preset}")
                        else:
                            print(f"   ❌ {midi_key}: Expected Mix -> {expected_preset}, got Mix -> {preset}")
                    found = True
                    break

            if not found:
                print(f"   ❌ {midi_key}: NOT FOUND")

        # Mostrar resumen por deck
        print(f"\n📋 RESUMEN POR DECK:\n")

        deck_a_count = len([m for m in mappings.values() if isinstance(m, dict) and m.get('params', {}).get('deck_id') == 'A'])
        deck_b_count = len([m for m in mappings.values() if isinstance(m, dict) and m.get('params', {}).get('deck_id') == 'B'])
        mix_count = len([m for m in mappings.values() if isinstance(m, dict) and m.get('type') == 'crossfade_action'])

        print(f"   🔴 Deck A: {deck_a_count} mappings")
        print(f"   🟢 Deck B: {deck_b_count} mappings")
        print(f"   🟡 Mix: {mix_count} mappings")

        print(f"\n💡 SIGUIENTE PASO:")
        print("   1. Ejecuta debug_midi_mappings.py para verificar que todo está correcto")
        print("   2. Reinicia la aplicación")
        print("   3. Los mappings deberían funcionar correctamente ahora")

        return True

    except Exception as e:
        print(f"❌ Error creando archivo: {e}")
        return False

if __name__ == "__main__":
    success = create_correct_midi_mappings()
    if success:
        print(f"\n🎉 ¡MAPPINGS MIDI CREADOS EXITOSAMENTE!")
    else:
        print(f"\n💥 ERROR CREANDO MAPPINGS MIDI")
