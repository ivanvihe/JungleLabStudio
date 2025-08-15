#!/usr/bin/env python3
"""
Script de depuración para verificar que los mappings MIDI se cargan correctamente
Ejecuta este script para diagnosticar problemas con los mappings MIDI
"""

import json
import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def debug_midi_mappings():
    """Debug completo del sistema de mapeo MIDI"""
    print("🔍 INICIANDO DEBUG DE MAPPINGS MIDI")
    print("=" * 60)
    
    # 1. Verificar archivo config/midi_mappings.json
    config_file = 'config/midi_mappings.json'
    print(f"\n1. 📁 VERIFICANDO ARCHIVO PRINCIPAL: {config_file}")
    
    if os.path.exists(config_file):
        print(f"   ✅ Archivo existe: {config_file}")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_mappings = json.load(f)
            
            print(f"   ✅ JSON válido")
            print(f"   📊 Total mappings: {len(config_mappings)}")
            
            # Mostrar algunos mappings de ejemplo
            print(f"\n   📋 MAPPINGS ENCONTRADOS:")
            for i, (action_id, mapping_data) in enumerate(config_mappings.items()):
                if i >= 10:  # Mostrar solo los primeros 10
                    print(f"      ... y {len(config_mappings) - 10} más")
                    break
                
                midi_key = mapping_data.get('midi', 'no_midi')
                action_type = mapping_data.get('type', 'unknown')
                params = mapping_data.get('params', {})
                
                # Extraer información específica según el tipo
                if action_type == 'load_preset':
                    deck_id = params.get('deck_id', 'N/A')
                    preset_name = params.get('preset_name', 'N/A')
                    print(f"      {action_id}: {midi_key} -> Deck {deck_id}: {preset_name}")
                elif action_type == 'crossfade_action':
                    preset = params.get('preset', 'N/A')
                    duration = params.get('duration', 'N/A')
                    print(f"      {action_id}: {midi_key} -> Mix: {preset} ({duration})")
                else:
                    print(f"      {action_id}: {midi_key} -> {action_type}")
            
            # Verificar mappings específicos críticos
            print(f"\n   🔍 VERIFICANDO MAPPINGS CRÍTICOS:")
            critical_tests = [
                ("note_on_ch0_note37", "Should be Wire Terrain on Deck A"),
                ("note_on_ch0_note60", "Should be Mobius Band on Deck B"),
                ("note_on_ch0_note55", "Should be Wire Terrain on Deck B"),
                ("note_on_ch0_note38", "Should be Abstract Lines on Deck A"),
                ("note_on_ch0_note50", "Should be Mix A to B 5s")
            ]
            
            for midi_key, expected in critical_tests:
                found = False
                for action_id, mapping_data in config_mappings.items():
                    if mapping_data.get('midi') == midi_key:
                        action_type = mapping_data.get('type', 'unknown')
                        params = mapping_data.get('params', {})
                        
                        if action_type == 'load_preset':
                            deck_id = params.get('deck_id', 'N/A')
                            preset_name = params.get('preset_name', 'N/A')
                            actual = f"Deck {deck_id}: {preset_name}"
                        elif action_type == 'crossfade_action':
                            preset = params.get('preset', 'N/A')
                            duration = params.get('duration', 'N/A')
                            actual = f"Mix: {preset} ({duration})"
                        else:
                            actual = f"{action_type}"
                        
                        print(f"      ✅ {midi_key}: {actual}")
                        found = True
                        break
                
                if not found:
                    print(f"      ❌ {midi_key}: NOT FOUND (expected: {expected})")
                    
        except json.JSONDecodeError as e:
            print(f"   ❌ Error JSON: {e}")
        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")
    else:
        print(f"   ❌ Archivo NO existe: {config_file}")
    
    # 2. Verificar archivo config/settings.json
    settings_file = 'config/settings.json'
    print(f"\n2. 📁 VERIFICANDO ARCHIVO SETTINGS: {settings_file}")
    
    if os.path.exists(settings_file):
        print(f"   ✅ Archivo existe: {settings_file}")
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            midi_mappings = settings.get('midi_mappings', {})
            print(f"   📊 MIDI mappings en settings: {len(midi_mappings)}")
            
            if len(midi_mappings) > 0:
                print(f"   ⚠️  HAY MAPPINGS EN SETTINGS - esto puede causar conflictos")
                # Mostrar algunos
                for i, (action_id, mapping_data) in enumerate(midi_mappings.items()):
                    if i >= 5:
                        print(f"      ... y {len(midi_mappings) - 5} más")
                        break
                    midi_key = mapping_data.get('midi', 'no_midi')
                    print(f"      {action_id}: {midi_key}")
            else:
                print(f"   ✅ No hay mappings conflictivos en settings")
                
        except Exception as e:
            print(f"   ❌ Error leyendo settings: {e}")
    else:
        print(f"   ❌ Archivo settings NO existe: {settings_file}")
    
    # 3. Verificar estructura de directorios
    print(f"\n3. 📂 VERIFICANDO ESTRUCTURA DE DIRECTORIOS:")
    
    config_dir = 'config'
    if os.path.exists(config_dir):
        print(f"   ✅ Directorio config/ existe")
        files = os.listdir(config_dir)
        print(f"   📋 Archivos en config/: {files}")
    else:
        print(f"   ❌ Directorio config/ NO existe")
    
    # 4. Verificar permisos
    print(f"\n4. 🔐 VERIFICANDO PERMISOS:")
    
    if os.path.exists(config_file):
        if os.access(config_file, os.R_OK):
            print(f"   ✅ Permiso de lectura en {config_file}")
        else:
            print(f"   ❌ SIN permiso de lectura en {config_file}")
            
        if os.access(config_file, os.W_OK):
            print(f"   ✅ Permiso de escritura en {config_file}")
        else:
            print(f"   ❌ SIN permiso de escritura en {config_file}")
    
    # 5. Simular carga con settings_manager
    print(f"\n5. 🧪 SIMULANDO CARGA CON SETTINGS_MANAGER:")
    
    try:
        # Agregar el directorio padre al path para importar
        sys.path.append('.')
        from utils.settings_manager import SettingsManager
        
        settings_manager = SettingsManager()
        mappings = settings_manager.load_midi_mappings()
        
        print(f"   📊 Mappings cargados por SettingsManager: {len(mappings)}")
        
        if len(mappings) > 0:
            print(f"   ✅ SettingsManager carga mappings correctamente")
            
            # Verificar un mapping específico
            test_key = "note_on_ch0_note37"  # Wire Terrain Deck A
            found_mapping = None
            for action_id, mapping_data in mappings.items():
                if mapping_data.get('midi') == test_key:
                    found_mapping = (action_id, mapping_data)
                    break
            
            if found_mapping:
                action_id, mapping_data = found_mapping
                params = mapping_data.get('params', {})
                deck_id = params.get('deck_id', 'N/A')
                preset_name = params.get('preset_name', 'N/A')
                print(f"   ✅ Test mapping {test_key}: Deck {deck_id} -> {preset_name}")
            else:
                print(f"   ❌ Test mapping {test_key} NO encontrado")
        else:
            print(f"   ❌ SettingsManager NO carga mappings")
            
    except ImportError as e:
        print(f"   ❌ Error importando SettingsManager: {e}")
    except Exception as e:
        print(f"   ❌ Error simulando carga: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG COMPLETADO")
    
    # 6. Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    print("   1. Asegúrate de que config/midi_mappings.json existe y tiene contenido válido")
    print("   2. Elimina la sección 'midi_mappings' de config/settings.json si existe")
    print("   3. Verifica que el directorio config/ tiene permisos de lectura/escritura")
    print("   4. Reinicia la aplicación después de hacer cambios")

if __name__ == "__main__":
    debug_midi_mappings()