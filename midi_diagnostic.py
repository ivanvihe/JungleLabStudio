# Script de diagnóstico para ejecutar en la consola de Python de tu aplicación
# Ejecuta esto mientras la aplicación está corriendo para verificar el estado

import logging

# Verificar conexión MIDI
def diagnose_midi():
    print("\n" + "="*60)
    print("DIAGNÓSTICO MIDI")
    print("="*60)
    
    # Verificar MIDI engine
    if app.midi_engine:
        print("✅ MIDI Engine existe")
        print(f"   Puerto abierto: {app.midi_engine.is_port_open()}")
        print(f"   Puerto actual: {app.midi_engine.input_port}")
        
        # Verificar referencias
        print(f"   Mixer window ref: {'✅' if app.midi_engine.mixer_window else '❌'}")
        print(f"   Control panel ref: {'✅' if app.midi_engine.control_panel else '❌'}")
        
        # Verificar mappings
        mappings = app.midi_engine.get_midi_mappings()
        print(f"\n📋 Total mappings: {len(mappings)}")
        
        # Mostrar algunos mappings de ejemplo
        test_notes = [36, 37, 48, 54, 55]
        for note in test_notes:
            key = f"note_on_ch0_note{note}"
            found = False
            for action_id, mapping_data in mappings.items():
                if isinstance(mapping_data, dict) and mapping_data.get('midi') == key:
                    action_type = mapping_data.get('type', 'unknown')
                    params = mapping_data.get('params', {})
                    preset = params.get('preset_name', params.get('preset', 'N/A'))
                    print(f"   Note {note}: {action_type} -> {preset}")
                    found = True
                    break
            if not found:
                print(f"   Note {note}: Sin mapping")
    else:
        print("❌ MIDI Engine no disponible")
    
    print("\n" + "="*60)

# Simular una nota MIDI para probar
def test_note(note_number, velocity=127):
    print(f"\n🧪 Probando nota {note_number} con velocity {velocity}")
    
    if app.midi_engine:
        import mido
        # Crear mensaje MIDI de prueba
        msg = mido.Message('note_on', channel=0, note=note_number, velocity=velocity)
        
        # Llamar directamente al handler
        print(f"   Enviando mensaje: {msg}")
        app.midi_engine.handle_midi_message(msg)
        print("   ✅ Mensaje procesado")
    else:
        print("   ❌ MIDI Engine no disponible")

# Verificar si los visualizadores están disponibles
def check_visualizers():
    print("\n🎨 VISUALIZADORES DISPONIBLES:")
    if app.visualizer_manager:
        names = app.visualizer_manager.get_visualizer_names()
        for i, name in enumerate(names):
            print(f"   {i+1}. {name}")
    else:
        print("   ❌ Visualizer manager no disponible")

# Ejecutar diagnóstico completo
diagnose_midi()
check_visualizers()

# Prueba directa - descomenta para probar
# test_note(37)  # Wire Terrain en Deck A