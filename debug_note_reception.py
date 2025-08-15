#!/usr/bin/env python3
"""
Script específico para diagnosticar el problema de recepción de notas MIDI incorrectas
y ejecución de mappings no deseados.

Problema reportado:
- Usuario envía A2 (nota 57) desde Ableton
- Sistema recibe/interpreta como nota 60
- Se ejecuta "Mobius Band" en Deck B sin mapping correspondiente
"""

import logging
import time
import mido

# Configurar logging detallado
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('midi_debug.log', mode='w')
    ]
)

def test_raw_midi_reception():
    """Test directo de recepción MIDI sin procesamiento"""
    print("🔍 INICIANDO DIAGNÓSTICO DE RECEPCIÓN MIDI")
    print("=" * 60)
    
    try:
        # Listar puertos disponibles
        available_ports = mido.get_input_names()
        print(f"📋 Puertos MIDI disponibles: {available_ports}")
        
        # Buscar el puerto virtual 4
        target_port = "virtual 4"
        if target_port not in available_ports:
            print(f"❌ Puerto '{target_port}' no encontrado")
            print("   Puertos disponibles:")
            for i, port in enumerate(available_ports):
                print(f"   {i}: {port}")
            return
        
        print(f"✅ Conectando a puerto: {target_port}")
        
        # Abrir puerto con callback de debug
        def debug_callback(msg):
            timestamp = time.strftime("%H:%M:%S.%f")[:-3]
            print(f"\n🎼 [{timestamp}] RAW MIDI RECIBIDO:")
            print(f"   Mensaje completo: {msg}")
            print(f"   Tipo: {msg.type}")
            print(f"   Canal: {getattr(msg, 'channel', 'N/A')}")
            print(f"   Nota: {getattr(msg, 'note', 'N/A')}")
            print(f"   Velocidad: {getattr(msg, 'velocity', 'N/A')}")
            print(f"   Tiempo: {getattr(msg, 'time', 'N/A')}")
            
            # Verificar si es note_on con velocidad > 0
            if msg.type == 'note_on' and getattr(msg, 'velocity', 0) > 0:
                note = getattr(msg, 'note', 0)
                print(f"   🎵 NOTA ACTIVA: {note}")
                
                # Convertir nota a nombre
                note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                octave = note // 12 - 1
                note_name = note_names[note % 12]
                print(f"   🎼 Nombre de nota: {note_name}{octave}")
                
                # Verificar si es la nota esperada
                if note == 57:  # A2
                    print(f"   ✅ CORRECTO: Recibida nota A2 (57)")
                elif note == 60:  # C4 - Mobius Band Deck B
                    print(f"   ❌ PROBLEMA: Recibida nota C4 (60) - esto triggerea Mobius Band")
                else:
                    print(f"   ⚠️  Nota diferente: {note}")
                
                # Mostrar qué mapping debería ejecutarse
                expected_mappings = {
                    57: "Deck B - Geometric Particles (deck_b_preset_3)",
                    60: "Deck B - Mobius Band (deck_b_preset_6)",
                    55: "Deck B - Wire Terrain (deck_b_preset_1)",
                    37: "Deck A - Wire Terrain (deck_a_preset_1)"
                }
                
                expected = expected_mappings.get(note, "Ningún mapping esperado")
                print(f"   📝 Mapping esperado: {expected}")
                
            elif msg.type == 'note_off':
                note = getattr(msg, 'note', 0)
                print(f"   🔇 NOTA OFF: {note}")
                
            print(f"   ─" * 50)
        
        # Abrir puerto
        with mido.open_input(target_port, callback=debug_callback) as port:
            print(f"\n🎵 PUERTO ABIERTO - Esperando mensajes MIDI...")
            print("   Envía notas desde Ableton para ver el diagnóstico")
            print("   Presiona Ctrl+C para salir")
            print("   Nota esperada: A2 (nota 57)")
            print()
            
            try:
                # Mantener el script corriendo
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n\n🛑 Deteniendo diagnóstico...")
                
    except Exception as e:
        print(f"❌ Error en el diagnóstico: {e}")
        import traceback
        traceback.print_exc()

def analyze_note_mapping_table():
    """Analizar la tabla de mappings para verificar note 57 y 60"""
    print("\n🔍 ANALIZANDO TABLA DE MAPPINGS")
    print("=" * 60)
    
    # Mappings esperados según el documento
    expected_mappings = {
        # Deck A (36-45)
        36: ("A", "Simple Test"),
        37: ("A", "Wire Terrain"),
        38: ("A", "Abstract Lines"),
        39: ("A", "Geometric Particles"),
        40: ("A", "Evolutive Particles"),
        41: ("A", "Abstract Shapes"),
        42: ("A", "Mobius Band"),
        43: ("A", "Building Madness"),
        44: ("A", "Cosmic Flow"),
        45: ("A", "Fluid Particles"),
        46: ("A", "Clear"),
        
        # Mix (48-53)
        48: ("Mix", "A to B 10s"),
        49: ("Mix", "B to A 10s"),
        50: ("Mix", "A to B 5s"),
        51: ("Mix", "B to A 5s"),
        52: ("Mix", "A to B 500ms"),
        53: ("Mix", "B to A 500ms"),
        
        # Deck B (54-63)
        54: ("B", "Simple Test"),
        55: ("B", "Wire Terrain"),
        56: ("B", "Abstract Lines"),
        57: ("B", "Geometric Particles"),  # ← ESTA ES LA NOTA QUE ENVÍAS
        58: ("B", "Evolutive Particles"),
        59: ("B", "Abstract Shapes"),
        60: ("B", "Mobius Band"),  # ← ESTA ES LA QUE SE EJECUTA INCORRECTAMENTE
        61: ("B", "Building Madness"),
        62: ("B", "Cosmic Flow"),
        63: ("B", "Fluid Particles"),
        64: ("B", "Clear")
    }
    
    print("📋 TABLA DE MAPPINGS ESPERADA:")
    print()
    
    # Mostrar mappings relevantes
    relevant_notes = [55, 57, 60, 37]  # Las notas mencionadas en el problema
    
    for note in relevant_notes:
        if note in expected_mappings:
            deck, preset = expected_mappings[note]
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = note // 12 - 1
            note_name = note_names[note % 12]
            
            if note == 57:
                marker = "← NOTA ENVIADA"
            elif note == 60:
                marker = "← ACCIÓN EJECUTADA (INCORRECTO)"
            else:
                marker = ""
                
            print(f"   Nota {note:2d} ({note_name}{octave}): Deck {deck} - {preset} {marker}")
    
    print(f"\n🔍 ANÁLISIS DEL PROBLEMA:")
    print(f"   • Nota enviada: 57 (A2) → Debería ejecutar: Deck B - Geometric Particles")
    print(f"   • Nota recibida: 60 (C4) → Ejecuta: Deck B - Mobius Band")
    print(f"   • Diferencia: +3 semitonos")
    print(f"   • Posibles causas:")
    print(f"     1. Error en el dispositivo MIDI virtual")
    print(f"     2. Transposición en Ableton")
    print(f"     3. Error en la librería mido")
    print(f"     4. Configuración incorrecta del Drum Rack")

def check_ableton_configuration():
    """Verificar configuración de Ableton Live"""
    print(f"\n🎛️ VERIFICACIONES RECOMENDADAS EN ABLETON:")
    print("=" * 60)
    print("1. 📋 Drum Rack:")
    print("   • Verificar que cada pad esté asignado a la nota correcta")
    print("   • A2 debería estar en el pad correspondiente a nota 57")
    print("   • No debe haber transposición activa")
    print()
    print("2. 🎹 Track MIDI:")
    print("   • Verificar que no hay transpose activo (+/- semitones)")
    print("   • Verificar que el canal MIDI es correcto")
    print("   • Verificar que no hay clips con transpose")
    print()
    print("3. 🔧 Configuración MIDI:")
    print("   • Verificar que 'virtual 4' está configurado como Output")
    print("   • Verificar que no hay otros dispositivos interfiriendo")
    print("   • Probar con otros dispositivos MIDI virtuales")
    print()
    print("4. 🧪 Test manual:")
    print("   • Ejecutar este script")
    print("   • Tocar A2 en Ableton")
    print("   • Verificar que el log muestra nota 57, no 60")

def main():
    """Función principal del diagnóstico"""
    print("🏥 DIAGNÓSTICO MIDI - PROBLEMA ESPECÍFICO")
    print("Problema: A2 (57) → se ejecuta Mobius Band (nota 60)")
    print()
    
    # Análisis teórico
    analyze_note_mapping_table()
    
    # Recomendaciones
    check_ableton_configuration()
    
    # Test práctico
    print(f"\n🧪 ¿EJECUTAR TEST EN VIVO? (s/n): ", end="")
    try:
        response = input().lower().strip()
        if response in ['s', 'si', 'y', 'yes']:
            test_raw_midi_reception()
        else:
            print("Test cancelado. Ejecuta manualmente cuando estés listo.")
    except KeyboardInterrupt:
        print("\nTest cancelado.")

if __name__ == "__main__":
    main()