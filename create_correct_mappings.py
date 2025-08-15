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
    
    # Definir los mappings exactos según el documento midi_mappings.json
    mappings = {
        # DECK A PRESETS (36-45)
        "deck_a_preset_0": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Simple Test",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note36"
        },
        "deck_a_preset_1": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Wire Terrain",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note37"
        },
        "deck_a_preset_2": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Abstract Lines",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note38"
        },
        "deck_a_preset_3": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Geometric Particles",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note39"
        },
        "deck_a_preset_4": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Evolutive Particles",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note40"
        },
        "deck_a_preset_5": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Abstract Shapes",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note41"
        },
        "deck_a_preset_6": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Mobius Band",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note42"
        },
        "deck_a_preset_7": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Building Madness",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note43"
        },
        "deck_a_preset_8": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Cosmic Flow",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note44"
        },
        "deck_a_preset_9": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": "Fluid Particles",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note45"
        },
        "deck_a_clear": {
            "type": "load_preset",
            "params": {
                "deck_id": "A",
                "preset_name": None,
                "custom_values": ""
            },
            "midi": "note_on_ch0_note46"
        },
        
        # MIX ACTIONS (48-53)
        "mix_action_0": {
            "type": "crossfade_action",
            "params": {
                "preset": "A to B",
                "duration": "10s",
                "target": "Visual Mix"
            },
            "midi": "note_on_ch0_note48"
        },
        "mix_action_1": {
            "type": "crossfade_action",
            "params": {
                "preset": "B to A",
                "duration": "10s",
                "target": "Visual Mix"
            },
            "midi": "note_on_ch0_note49"
        },
        "mix_action_2": {
            "type": "crossfade_action",
            "params": {
                "preset": "A to B",
                "duration": "5s",
                "target": "Visual Mix"
            },
            "midi": "note_on_ch0_note50"
        },
        "mix_action_3": {
            "type": "crossfade_action",
            "params": {
                "preset": "B to A",
                "duration": "5s",
                "target": "Visual Mix"
            },
            "midi": "note_on_ch0_note51"
        },
        "mix_action_4": {
            "type": "crossfade_action",
            "params": {
                "preset": "A to B",
                "duration": "500ms",
                "target": "Visual Mix"
            },
            "midi": "note_on_ch0_note52"
        },
        "mix_action_5": {
            "type": "crossfade_action",
            "params": {
                "preset": "B to A",
                "duration": "500ms",
                "target": "Visual Mix"
            },
            "midi": "note_on_ch0_note53"
        },
        
        # DECK B PRESETS (54-63)
        "deck_b_preset_0": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Simple Test",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note54"
        },
        "deck_b_preset_1": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Wire Terrain",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note55"
        },
        "deck_b_preset_2": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Abstract Lines",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note56"
        },
        "deck_b_preset_3": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Geometric Particles",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note57"
        },
        "deck_b_preset_4": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Evolutive Particles",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note58"
        },
        "deck_b_preset_5": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Abstract Shapes",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note59"
        },
        "deck_b_preset_6": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Mobius Band",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note60"
        },
        "deck_b_preset_7": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Building Madness",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note61"
        },
        "deck_b_preset_8": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Cosmic Flow",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note62"
        },
        "deck_b_preset_9": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": "Fluid Particles",
                "custom_values": ""
            },
            "midi": "note_on_ch0_note63"
        },
        "deck_b_clear": {
            "type": "load_preset",
            "params": {
                "deck_id": "B",
                "preset_name": None,
                "custom_values": ""
            },
            "midi": "note_on_ch0_note64"
        }
    }
    
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
                if mapping_data.get('midi') == midi_key:
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
        print(f"\n📋 RESUMEN POR DECK:")
        
        deck_a_count = len([m for m in mappings.values() if m.get('params', {}).get('deck_id') == 'A'])
        deck_b_count = len([m for m in mappings.values() if m.get('params', {}).get('deck_id') == 'B'])
        mix_count = len([m for m in mappings.values() if m.get('type') == 'crossfade_action'])
        
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