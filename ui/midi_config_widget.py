# ui/midi_config_widget.py - UI MEJORADA PARA CONFIGURACIÓN MIDI
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel, 
    QPushButton, QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QSpinBox, QCheckBox, QMessageBox, QSplitter,
    QTextEdit, QFrame, QScrollArea, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush

class MidiConfigWidget(QWidget):
    """Widget principal para configuración MIDI completa"""
    
    # Señales
    mapping_changed = pyqtSignal()
    start_learning = pyqtSignal(str)  # Emite la clave MIDI que está aprendiendo
    
    def __init__(self, midi_engine, visualizer_manager, parent=None):
        super().__init__(parent)
        self.midi_engine = midi_engine
        self.visualizer_manager = visualizer_manager
        self.learning_key = None
        self.learning_timer = QTimer()
        self.learning_timer.setSingleShot(True)
        self.learning_timer.timeout.connect(self.stop_learning)
        
        # Conectar señales MIDI
        if self.midi_engine and hasattr(self.midi_engine, 'midi_message_received_for_learning'):
            self.midi_engine.midi_message_received_for_learning.connect(self.on_midi_learned)
        
        self.init_ui()
        self.load_current_mappings()
        
    def init_ui(self):
        """Inicializar la interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Header con información MIDI
        header = self.create_header()
        layout.addWidget(header)
        
        # Tabs principales
        tabs = QTabWidget()

        # Editor único que muestra todos los mappings
        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, "🎛️ Editor MIDI")

        # Tab 2: Configuración de canales
        channels_tab = self.create_channels_tab()
        tabs.addTab(channels_tab, "📡 Canales MIDI")

        # Tab 3: Importar/Exportar
        import_export_tab = self.create_import_export_tab()
        tabs.addTab(import_export_tab, "💾 Importar/Exportar")
        
        layout.addWidget(tabs)
        
        # Footer con controles globales
        footer = self.create_footer()
        layout.addWidget(footer)
    
    def create_header(self):
        """Crear header con información MIDI"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.StyledPanel)
        header.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 2px solid #00ff00;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Título
        title = QLabel("🎹 CONFIGURACIÓN MIDI")
        title.setStyleSheet("color: #00ff00; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Estado MIDI
        self.midi_status = QLabel("Verificando...")
        self.midi_status.setStyleSheet("color: #ffaa00; font-weight: bold;")
        layout.addWidget(self.midi_status)
        
        # Estado de aprendizaje
        self.learning_status = QLabel("Listo")
        self.learning_status.setStyleSheet("color: #00ff00; font-weight: bold;")
        layout.addWidget(self.learning_status)
        
        # Actualizar estado
        self.update_midi_status()
        
        return header
    
    def create_quick_config_tab(self):
        """Tab de configuración rápida por notas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instrucciones
        instructions = QLabel("""
        <b>Configuración Rápida por Notas MIDI:</b><br>
        • Selecciona una nota y presiona "Learn" para asignar un control MIDI<br>
        • Configura qué acción realizar cuando se presione esa nota<br>
        • Los cambios se guardan automáticamente
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Selector de rango de notas
        range_group = QGroupBox("Rango de Notas")
        range_layout = QHBoxLayout(range_group)
        
        range_layout.addWidget(QLabel("Desde:"))
        self.start_note_spin = QSpinBox()
        self.start_note_spin.setRange(0, 127)
        self.start_note_spin.setValue(36)  # C1
        self.start_note_spin.valueChanged.connect(self.update_notes_table)
        range_layout.addWidget(self.start_note_spin)
        
        range_layout.addWidget(QLabel("Hasta:"))
        self.end_note_spin = QSpinBox()
        self.end_note_spin.setRange(0, 127)
        self.end_note_spin.setValue(71)  # B3
        self.end_note_spin.valueChanged.connect(self.update_notes_table)
        range_layout.addWidget(self.end_note_spin)
        
        update_btn = QPushButton("Actualizar")
        update_btn.clicked.connect(self.update_notes_table)
        range_layout.addWidget(update_btn)
        
        range_layout.addStretch()
        layout.addWidget(range_group)
        
        # Tabla de notas
        self.notes_table = QTableWidget()
        self.notes_table.setColumnCount(6)
        self.notes_table.setHorizontalHeaderLabels([
            "Nota", "Nombre", "Acción", "Preset/Target", "Canal", "Controles"
        ])
        
        # Configurar tabla
        header = self.notes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Nota
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Acción
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Preset
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Canal
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Controles
        
        self.notes_table.setColumnWidth(0, 60)
        self.notes_table.setColumnWidth(1, 80)
        self.notes_table.setColumnWidth(4, 80)
        self.notes_table.setColumnWidth(5, 120)
        
        self.notes_table.setAlternatingRowColors(True)
        layout.addWidget(self.notes_table)
        
        return widget
    
    def create_advanced_tab(self):
        """Tab de editor avanzado"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controles superiores
        controls_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Añadir Mapping")
        add_btn.clicked.connect(self.add_custom_mapping)
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        controls_layout.addWidget(add_btn)
        
        clear_btn = QPushButton("🗑️ Limpiar Todo")
        clear_btn.clicked.connect(self.clear_all_mappings)
        clear_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        
        reset_btn = QPushButton("🔄 Restaurar Defaults")
        reset_btn.clicked.connect(self.restore_defaults)
        reset_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 8px;")
        controls_layout.addWidget(reset_btn)
        
        layout.addLayout(controls_layout)
        
        # Tabla de mappings avanzada
        self.advanced_table = QTableWidget()
        self.advanced_table.setColumnCount(7)
        self.advanced_table.setHorizontalHeaderLabels([
            "ID", "Tipo", "MIDI Key", "Deck", "Preset", "Parámetros", "Controles"
        ])
        
        # Configurar tabla avanzada
        header = self.advanced_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        
        self.advanced_table.setColumnWidth(3, 80)
        self.advanced_table.setColumnWidth(6, 100)
        
        layout.addWidget(self.advanced_table)
        
        return widget
    
    def create_channels_tab(self):
        """Tab de configuración de canales"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuración de canales aceptados
        channels_group = QGroupBox("Canales MIDI Aceptados")
        channels_layout = QGridLayout(channels_group)
        
        self.channel_checkboxes = {}
        for i in range(16):
            checkbox = QCheckBox(f"Canal {i+1}")
            checkbox.setChecked(i == 0)  # Solo canal 1 por defecto
            checkbox.stateChanged.connect(self.update_accepted_channels)
            self.channel_checkboxes[i] = checkbox
            channels_layout.addWidget(checkbox, i // 4, i % 4)
        
        layout.addWidget(channels_group)
        
        # Canal por defecto
        default_group = QGroupBox("Canal por Defecto para Nuevos Mappings")
        default_layout = QHBoxLayout(default_group)
        
        default_layout.addWidget(QLabel("Canal por defecto:"))
        self.default_channel_combo = QComboBox()
        for i in range(16):
            self.default_channel_combo.addItem(f"Canal {i+1}", i)
        self.default_channel_combo.setCurrentIndex(0)
        self.default_channel_combo.currentIndexChanged.connect(self.update_default_channel)
        default_layout.addWidget(self.default_channel_combo)
        
        default_layout.addStretch()
        layout.addWidget(default_group)
        
        # Información de canales
        info_group = QGroupBox("Información de Canales")
        info_layout = QVBoxLayout(info_group)
        
        self.channel_info = QTextEdit()
        self.channel_info.setMaximumHeight(150)
        self.channel_info.setReadOnly(True)
        self.update_channel_info()
        info_layout.addWidget(self.channel_info)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        return widget
    
    def create_import_export_tab(self):
        """Tab de importar/exportar"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Exportar
        export_group = QGroupBox("Exportar Configuración")
        export_layout = QVBoxLayout(export_group)
        
        export_info = QLabel("Exporta tu configuración MIDI para hacer backup o compartir con otros.")
        export_layout.addWidget(export_info)
        
        export_buttons = QHBoxLayout()
        
        export_json_btn = QPushButton("📄 Exportar como JSON")
        export_json_btn.clicked.connect(self.export_json)
        export_buttons.addWidget(export_json_btn)
        
        export_readable_btn = QPushButton("📝 Exportar Legible")
        export_readable_btn.clicked.connect(self.export_readable)
        export_buttons.addWidget(export_readable_btn)
        
        export_buttons.addStretch()
        export_layout.addLayout(export_buttons)
        
        layout.addWidget(export_group)
        
        # Importar
        import_group = QGroupBox("Importar Configuración")
        import_layout = QVBoxLayout(import_group)
        
        import_info = QLabel("Importa configuración MIDI desde archivo JSON.")
        import_layout.addWidget(import_info)
        
        import_buttons = QHBoxLayout()
        
        import_btn = QPushButton("📁 Importar desde JSON")
        import_btn.clicked.connect(self.import_json)
        import_buttons.addWidget(import_btn)
        
        import_buttons.addStretch()
        import_layout.addLayout(import_buttons)
        
        layout.addWidget(import_group)
        
        # Templates
        templates_group = QGroupBox("Templates Predefinidos")
        templates_layout = QVBoxLayout(templates_group)
        
        templates_info = QLabel("Carga configuraciones predefinidas para diferentes controladores.")
        templates_layout.addWidget(templates_info)
        
        templates_buttons = QHBoxLayout()
        
        ableton_btn = QPushButton("🎛️ Ableton Push")
        ableton_btn.clicked.connect(lambda: self.load_template("ableton_push"))
        templates_buttons.addWidget(ableton_btn)
        
        apc_btn = QPushButton("🎹 APC40")
        apc_btn.clicked.connect(lambda: self.load_template("apc40"))
        templates_buttons.addWidget(apc_btn)
        
        generic_btn = QPushButton("🎮 Controlador Genérico")
        generic_btn.clicked.connect(lambda: self.load_template("generic"))
        templates_buttons.addWidget(generic_btn)
        
        templates_buttons.addStretch()
        templates_layout.addLayout(templates_buttons)
        
        layout.addWidget(templates_group)
        
        layout.addStretch()
        return widget
    
    def create_footer(self):
        """Crear footer con controles globales"""
        footer = QFrame()
        footer.setFrameStyle(QFrame.Shape.StyledPanel)
        footer.setStyleSheet("background-color: #1a1a1a; border: 1px solid #666; border-radius: 5px; padding: 5px;")
        
        layout = QHBoxLayout(footer)
        
        # Información de mappings
        self.mappings_info = QLabel("Mappings: 0")
        self.mappings_info.setStyleSheet("color: #ffffff; font-weight: bold;")
        layout.addWidget(self.mappings_info)
        
        layout.addStretch()
        
        # Botón de test
        test_btn = QPushButton("🧪 Test Mapping")
        test_btn.clicked.connect(self.test_random_mapping)
        layout.addWidget(test_btn)
        
        # Botón de guardar
        save_btn = QPushButton("💾 Guardar")
        save_btn.clicked.connect(self.save_mappings)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(save_btn)
        
        return footer
    
    def update_notes_table(self):
        """Actualizar tabla de notas"""
        try:
            start_note = self.start_note_spin.value()
            end_note = self.end_note_spin.value()
            
            if start_note > end_note:
                end_note = start_note + 35  # Máximo 36 notas
                self.end_note_spin.setValue(end_note)
            
            note_count = end_note - start_note + 1
            self.notes_table.setRowCount(note_count)
            
            for i, note in enumerate(range(start_note, end_note + 1)):
                # Columna 0: Número de nota
                note_item = QTableWidgetItem(str(note))
                note_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                note_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.notes_table.setItem(i, 0, note_item)
                
                # Columna 1: Nombre de nota
                note_name = self.get_note_name(note)
                name_item = QTableWidgetItem(note_name)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.notes_table.setItem(i, 1, name_item)
                
                # Columna 2: Acción
                action_combo = QComboBox()
                action_combo.addItems(["Sin Asignar", "Cargar Preset", "Crossfade", "Control Parámetro"])
                action_combo.currentTextChanged.connect(lambda text, row=i: self.on_action_changed(row, text))
                self.notes_table.setCellWidget(i, 2, action_combo)
                
                # Columna 3: Preset/Target
                preset_combo = QComboBox()
                preset_combo.addItem("-- Seleccionar --")
                self.notes_table.setCellWidget(i, 3, preset_combo)
                
                # Columna 4: Canal
                channel_combo = QComboBox()
                for ch in range(16):
                    channel_combo.addItem(f"Ch {ch+1}", ch)
                channel_combo.setCurrentIndex(0)  # Canal 1 por defecto
                self.notes_table.setCellWidget(i, 4, channel_combo)
                
                # Columna 5: Controles
                controls_widget = self.create_note_controls(note)
                self.notes_table.setCellWidget(i, 5, controls_widget)
                
                # Cargar mapping existente si existe
                self.load_existing_mapping_for_note(i, note)
            
            self.notes_table.resizeRowsToContents()
            
        except Exception as e:
            logging.error(f"Error updating notes table: {e}")
    
    def create_note_controls(self, note):
        """Crear controles para una nota"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Botón Learn
        learn_btn = QPushButton("Learn")
        learn_btn.setMaximumWidth(50)
        learn_btn.clicked.connect(lambda: self.learn_note(note))
        layout.addWidget(learn_btn)
        
        # Botón Test
        test_btn = QPushButton("Test")
        test_btn.setMaximumWidth(40)
        test_btn.clicked.connect(lambda: self.test_note(note))
        layout.addWidget(test_btn)
        
        # Botón Delete
        delete_btn = QPushButton("×")
        delete_btn.setMaximumWidth(25)
        delete_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
        delete_btn.clicked.connect(lambda: self.delete_note_mapping(note))
        layout.addWidget(delete_btn)
        
        return widget
    
    def load_existing_mapping_for_note(self, row, note):
        """Cargar mapping existente para una nota"""
        try:
            if not self.midi_engine:
                return
                
            # Buscar mapping para esta nota
            mappings = self.midi_engine.get_midi_mappings()
            note_mapping = None

            for action_id, mapping_data in mappings.items():
                if not isinstance(mapping_data, dict):
                    continue
                midi_key = mapping_data.get('midi', '')
                if f'note{note}' in midi_key:
                    note_mapping = mapping_data
                    break
            
            if note_mapping:
                # Configurar acción
                action_combo = self.notes_table.cellWidget(row, 2)
                action_type = note_mapping.get('type', '')
                
                if action_type == 'load_preset':
                    action_combo.setCurrentText("Cargar Preset")
                elif action_type == 'crossfade_action':
                    action_combo.setCurrentText("Crossfade")
                elif action_type == 'control_parameter':
                    action_combo.setCurrentText("Control Parámetro")
                
                # Actualizar preset/target
                self.update_preset_combo_for_action(row, action_combo.currentText())
                
                # Configurar preset específico
                params = note_mapping.get('params', {})
                preset_combo = self.notes_table.cellWidget(row, 3)
                
                if action_type == 'load_preset':
                    preset_name = params.get('preset_name', '')
                    if preset_name:
                        index = preset_combo.findText(preset_name)
                        if index >= 0:
                            preset_combo.setCurrentIndex(index)
                
                # Extraer canal del midi_key
                midi_key = note_mapping.get('midi', '')
                if '_ch' in midi_key:
                    try:
                        channel_part = midi_key.split('_ch')[1].split('_')[0]
                        channel = int(channel_part)
                        channel_combo = self.notes_table.cellWidget(row, 4)
                        channel_combo.setCurrentIndex(channel)
                    except:
                        pass
                        
        except Exception as e:
            logging.error(f"Error loading existing mapping for note {note}: {e}")
    
    def on_action_changed(self, row, action_text):
        """Manejar cambio de acción"""
        try:
            self.update_preset_combo_for_action(row, action_text)
            self.save_note_mapping(row)
        except Exception as e:
            logging.error(f"Error on action changed: {e}")
    
    def update_preset_combo_for_action(self, row, action_text):
        """Actualizar combo de preset basado en la acción"""
        try:
            preset_combo = self.notes_table.cellWidget(row, 3)
            preset_combo.clear()
            
            if action_text == "Cargar Preset":
                preset_combo.addItem("-- Seleccionar Preset --")
                preset_combo.addItem("Clear (Sin Preset)")
                if self.visualizer_manager:
                    presets = self.visualizer_manager.get_visualizer_names()
                    for preset in presets:
                        preset_combo.addItem(preset)
            
            elif action_text == "Crossfade":
                preset_combo.addItem("-- Seleccionar Acción --")
                crossfade_actions = [
                    "A to B (10s)", "B to A (10s)",
                    "A to B (5s)", "B to A (5s)",
                    "A to B (500ms)", "B to A (500ms)",
                    "Instant A", "Instant B", "Cut to Center", "Reset Mix"
                ]
                for action in crossfade_actions:
                    preset_combo.addItem(action)
            
            elif action_text == "Control Parámetro":
                preset_combo.addItem("-- Seleccionar Parámetro --")
                parameters = ["Speed", "Intensity", "Color", "Size", "Brightness", "Custom"]
                for param in parameters:
                    preset_combo.addItem(param)
            
            else:
                preset_combo.addItem("-- Sin Asignar --")
            
            # Conectar señal de cambio
            preset_combo.currentTextChanged.connect(lambda: self.save_note_mapping(row))
            
        except Exception as e:
            logging.error(f"Error updating preset combo: {e}")
    
    def save_note_mapping(self, row):
        """Guardar mapping de una nota"""
        try:
            if not self.midi_engine:
                return
                
            # Obtener datos de la fila
            note_item = self.notes_table.item(row, 0)
            if not note_item:
                return
                
            note = int(note_item.text())
            action_combo = self.notes_table.cellWidget(row, 2)
            preset_combo = self.notes_table.cellWidget(row, 3)
            channel_combo = self.notes_table.cellWidget(row, 4)
            
            action_text = action_combo.currentText()
            preset_text = preset_combo.currentText()
            channel = channel_combo.currentData()
            
            # Si no hay acción asignada, eliminar mapping existente
            if action_text == "Sin Asignar":
                self.delete_note_mapping(note)
                return
            
            # Crear nuevo mapping
            midi_key = f"note_on_ch{channel}_note{note}"
            action_id = f"note_{note}_ch{channel}"
            
            mapping_data = None
            
            if action_text == "Cargar Preset" and not preset_text.startswith("--"):
                deck_id = "A" if note < 60 else "B"  # Heurística simple
                preset_name = None if preset_text == "Clear (Sin Preset)" else preset_text
                
                mapping_data = {
                    "type": "load_preset",
                    "params": {
                        "deck_id": deck_id,
                        "preset_name": preset_name,
                        "custom_values": ""
                    },
                    "midi": midi_key
                }
            
            elif action_text == "Crossfade" and not preset_text.startswith("--"):
                # Parsear preset_text para obtener preset y duración
                if "10s" in preset_text:
                    duration = "10s"
                elif "5s" in preset_text:
                    duration = "5s"
                elif "500ms" in preset_text:
                    duration = "500ms"
                else:
                    duration = "50ms"
                
                if "A to B" in preset_text:
                    preset = "A to B"
                elif "B to A" in preset_text:
                    preset = "B to A"
                elif "Instant A" in preset_text:
                    preset = "Instant A"
                elif "Instant B" in preset_text:
                    preset = "Instant B"
                elif "Cut to Center" in preset_text:
                    preset = "Cut to Center"
                elif "Reset Mix" in preset_text:
                    preset = "Reset Mix"
                else:
                    preset = "A to B"
                
                mapping_data = {
                    "type": "crossfade_action",
                    "params": {
                        "preset": preset,
                        "duration": duration,
                        "target": "Visual Mix"
                    },
                    "midi": midi_key
                }
            
            # Guardar mapping si se creó
            if mapping_data:
                self.midi_engine.add_midi_mapping(action_id, mapping_data)
                logging.info(f"✅ Saved mapping for note {note}: {action_text}")
                self.mapping_changed.emit()
                self.update_mappings_info()
            
        except Exception as e:
            logging.error(f"Error saving note mapping: {e}")
    
    def delete_note_mapping(self, note):
        """Eliminar mapping de una nota"""
        try:
            if not self.midi_engine:
                return
                
            # Buscar y eliminar mappings para esta nota
            mappings = self.midi_engine.get_midi_mappings()
            to_delete = []

            for action_id, mapping_data in mappings.items():
                if not isinstance(mapping_data, dict):
                    continue
                midi_key = mapping_data.get('midi', '')
                if f'note{note}' in midi_key:
                    to_delete.append(action_id)
            
            for action_id in to_delete:
                self.midi_engine.remove_midi_mapping(action_id)
                logging.info(f"✅ Deleted mapping for note {note}")
            
            if to_delete:
                self.mapping_changed.emit()
                self.update_mappings_info()
                # Actualizar la fila en la tabla
                for row in range(self.notes_table.rowCount()):
                    note_item = self.notes_table.item(row, 0)
                    if note_item and int(note_item.text()) == note:
                        action_combo = self.notes_table.cellWidget(row, 2)
                        action_combo.setCurrentText("Sin Asignar")
                        break
            
        except Exception as e:
            logging.error(f"Error deleting note mapping: {e}")
    
    def learn_note(self, note):
        """Iniciar aprendizaje para una nota"""
        try:
            if not self.midi_engine or not self.midi_engine.is_port_open():
                QMessageBox.warning(self, "MIDI No Conectado", 
                                  "No hay dispositivo MIDI conectado.")
                return
            
            # Obtener canal seleccionado
            for row in range(self.notes_table.rowCount()):
                note_item = self.notes_table.item(row, 0)
                if note_item and int(note_item.text()) == note:
                    channel_combo = self.notes_table.cellWidget(row, 4)
                    channel = channel_combo.currentData()
                    break
            else:
                channel = 0
            
            self.learning_key = f"note_on_ch{channel}_note{note}"
            
            self.learning_status.setText(f"🎵 Aprendiendo nota {note}...")
            self.learning_status.setStyleSheet("color: #ffaa00; font-weight: bold;")
            
            self.start_learning.emit(self.learning_key)
            
            # Timeout de 10 segundos
            self.learning_timer.start(10000)
            
        except Exception as e:
            logging.error(f"Error learning note: {e}")
    
    def stop_learning(self):
        """Detener aprendizaje"""
        self.learning_key = None
        self.learning_status.setText("Listo")
        self.learning_status.setStyleSheet("color: #00ff00; font-weight: bold;")
        self.learning_timer.stop()
    
    def on_midi_learned(self, message_key):
        """Manejar MIDI aprendido"""
        try:
            if not self.learning_key:
                return
            
            # Verificar si coincide con lo que estamos aprendiendo
            if 'note' in message_key and 'note' in self.learning_key:
                # Extraer número de nota
                try:
                    learned_note = int(message_key.split('note')[1])
                    expected_note = int(self.learning_key.split('note')[1])
                    
                    # Si es la nota correcta, actualizar
                    if learned_note == expected_note:
                        self.learning_status.setText(f"✅ Nota {learned_note} aprendida!")
                        self.learning_status.setStyleSheet("color: #00ff00; font-weight: bold;")
                        
                        # Actualizar la tabla
                        for row in range(self.notes_table.rowCount()):
                            note_item = self.notes_table.item(row, 0)
                            if note_item and int(note_item.text()) == expected_note:
                                # Extraer canal del mensaje aprendido
                                if '_ch' in message_key:
                                    channel = int(message_key.split('_ch')[1].split('_')[0])
                                    channel_combo = self.notes_table.cellWidget(row, 4)
                                    channel_combo.setCurrentIndex(channel)
                                break
                        
                        QTimer.singleShot(2000, self.stop_learning)
                        return
                        
                except ValueError:
                    pass
            
            # Si no coincide, mostrar advertencia
            self.learning_status.setText(f"⚠️ Se recibió {message_key}, esperando nota específica...")
            self.learning_status.setStyleSheet("color: #ffaa00; font-weight: bold;")
            
        except Exception as e:
            logging.error(f"Error on MIDI learned: {e}")
    
    def test_note(self, note):
        """Probar mapping de una nota"""
        try:
            if self.midi_engine:
                self.midi_engine.test_midi_mapping(note)
                QMessageBox.information(self, "Test MIDI", 
                                      f"Mapping de nota {note} ejecutado.\nRevisa la consola para detalles.")
        except Exception as e:
            logging.error(f"Error testing note: {e}")
    
    def update_accepted_channels(self):
        """Actualizar canales aceptados"""
        try:
            if not self.midi_engine:
                return
                
            accepted_channels = []
            for channel, checkbox in self.channel_checkboxes.items():
                if checkbox.isChecked():
                    accepted_channels.append(channel)
            
            if accepted_channels:
                self.midi_engine.set_accepted_channels(accepted_channels)
                self.update_channel_info()
            else:
                # Al menos un canal debe estar seleccionado
                self.channel_checkboxes[0].setChecked(True)
                
        except Exception as e:
            logging.error(f"Error updating accepted channels: {e}")
    
    def update_default_channel(self):
        """Actualizar canal por defecto"""
        try:
            if not self.midi_engine:
                return
                
            channel = self.default_channel_combo.currentData()
            self.midi_engine.set_default_channel(channel)
            self.update_channel_info()
            
        except Exception as e:
            logging.error(f"Error updating default channel: {e}")
    
    def update_channel_info(self):
        """Actualizar información de canales"""
        try:
            if not self.midi_engine:
                return
                
            accepted = []
            for channel, checkbox in self.channel_checkboxes.items():
                if checkbox.isChecked():
                    accepted.append(f"Canal {channel+1}")
            
            default_channel = self.default_channel_combo.currentData() + 1
            
            info_text = f"""
<b>Configuración Actual:</b><br>
• Canales aceptados: {', '.join(accepted)}<br>
• Canal por defecto: Canal {default_channel}<br>
• Total mappings: {len(self.midi_engine.get_midi_mappings())}<br><br>

<b>Información:</b><br>
• Los canales aceptados determinan qué mensajes MIDI se procesan<br>
• El canal por defecto se usa para nuevos mappings<br>
• Puedes tener diferentes mappings en diferentes canales
            """
            
            self.channel_info.setHtml(info_text)
            
        except Exception as e:
            logging.error(f"Error updating channel info: {e}")
    
    def load_current_mappings(self):
        """Cargar mappings actuales"""
        try:
            self.update_advanced_table()
            self.update_mappings_info()
        except Exception as e:
            logging.error(f"Error loading current mappings: {e}")
    
    def update_advanced_table(self):
        """Actualizar tabla avanzada"""
        try:
            if not self.midi_engine:
                return
                
            mappings = {
                aid: m for aid, m in self.midi_engine.get_midi_mappings().items()
                if isinstance(m, dict)
            }
            self.advanced_table.setRowCount(len(mappings))

            for row, (action_id, mapping_data) in enumerate(mappings.items()):
                # ID
                id_item = QTableWidgetItem(action_id)
                self.advanced_table.setItem(row, 0, id_item)
                
                # Tipo
                type_item = QTableWidgetItem(mapping_data.get('type', 'unknown'))
                self.advanced_table.setItem(row, 1, type_item)
                
                # MIDI Key
                midi_item = QTableWidgetItem(mapping_data.get('midi', 'no_midi'))
                self.advanced_table.setItem(row, 2, midi_item)
                
                # Deck
                params = mapping_data.get('params', {})
                deck = params.get('deck_id', params.get('target', ''))
                deck_item = QTableWidgetItem(str(deck))
                self.advanced_table.setItem(row, 3, deck_item)
                
                # Preset
                preset = params.get('preset_name', params.get('preset', ''))
                preset_item = QTableWidgetItem(str(preset))
                self.advanced_table.setItem(row, 4, preset_item)
                
                # Parámetros
                param_str = ', '.join([f"{k}:{v}" for k, v in params.items() if k not in ['deck_id', 'preset_name', 'preset']])
                param_item = QTableWidgetItem(param_str)
                self.advanced_table.setItem(row, 5, param_item)
                
                # Controles
                controls_widget = self.create_advanced_controls(action_id)
                self.advanced_table.setCellWidget(row, 6, controls_widget)
            
            self.advanced_table.resizeRowsToContents()
            
        except Exception as e:
            logging.error(f"Error updating advanced table: {e}")
    
    def create_advanced_controls(self, action_id):
        """Crear controles para tabla avanzada"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Botón Edit
        edit_btn = QPushButton("✏️")
        edit_btn.setMaximumWidth(30)
        edit_btn.setToolTip("Editar")
        edit_btn.clicked.connect(lambda: self.edit_mapping(action_id))
        layout.addWidget(edit_btn)
        
        # Botón Delete
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(30)
        delete_btn.setToolTip("Eliminar")
        delete_btn.setStyleSheet("background-color: #ff4444; color: white;")
        delete_btn.clicked.connect(lambda: self.delete_mapping(action_id))
        layout.addWidget(delete_btn)
        
        return widget
    
    def update_mappings_info(self):
        """Actualizar información de mappings"""
        try:
            if self.midi_engine:
                count = len(self.midi_engine.get_midi_mappings())
                self.mappings_info.setText(f"Mappings: {count}")
            else:
                self.mappings_info.setText("Mappings: 0")
        except Exception as e:
            logging.error(f"Error updating mappings info: {e}")
    
    def update_midi_status(self):
        """Actualizar estado MIDI"""
        try:
            if not self.midi_engine:
                self.midi_status.setText("❌ Engine no disponible")
                self.midi_status.setStyleSheet("color: #ff4444; font-weight: bold;")
                return
                
            if self.midi_engine.is_port_open():
                device_name = self.midi_engine.get_connected_device_name()
                self.midi_status.setText(f"✅ {device_name}")
                self.midi_status.setStyleSheet("color: #00ff00; font-weight: bold;")
            else:
                self.midi_status.setText("❌ Desconectado")
                self.midi_status.setStyleSheet("color: #ff4444; font-weight: bold;")
                
        except Exception as e:
            logging.error(f"Error updating MIDI status: {e}")
    
    def get_note_name(self, note_number):
        """Convertir número de nota MIDI a nombre"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note_name = note_names[note_number % 12]
        return f"{note_name}{octave}"
    
    # === FUNCIONES DE IMPORTAR/EXPORTAR ===
    
    def export_json(self):
        """Exportar mappings como JSON"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Exportar Mappings MIDI", 
                "midi_mappings.json", 
                "JSON files (*.json)"
            )
            
            if filename:
                if self.midi_engine and self.midi_engine.export_mappings_to_file(filename):
                    QMessageBox.information(self, "Exportar", f"Mappings exportados a:\n{filename}")
                else:
                    QMessageBox.warning(self, "Error", "No se pudo exportar el archivo")
                    
        except Exception as e:
            logging.error(f"Error exporting JSON: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando: {str(e)}")
    
    def export_readable(self):
        """Exportar mappings en formato legible"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Exportar Mappings Legible", 
                "midi_mappings.txt", 
                "Text files (*.txt)"
            )
            
            if filename and self.midi_engine:
                mappings = self.midi_engine.get_midi_mappings()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== CONFIGURACIÓN MIDI MAPPINGS ===\n\n")
                    f.write(f"Total mappings: {len(mappings)}\n")
                    f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # Agrupar por tipo
                    preset_mappings = []
                    mix_mappings = []
                    control_mappings = []
                    
                    for action_id, mapping_data in mappings.items():
                        action_type = mapping_data.get('type', 'unknown')
                        if action_type == 'load_preset':
                            preset_mappings.append((action_id, mapping_data))
                        elif action_type == 'crossfade_action':
                            mix_mappings.append((action_id, mapping_data))
                        else:
                            control_mappings.append((action_id, mapping_data))
                    
                    # Escribir presets
                    if preset_mappings:
                        f.write("=== PRESET MAPPINGS ===\n")
                        for action_id, mapping_data in sorted(preset_mappings, key=lambda x: x[1].get('midi', '')):
                            midi_key = mapping_data.get('midi', '')
                            params = mapping_data.get('params', {})
                            
                            # Extraer nota
                            note_num = 'N/A'
                            if 'note' in midi_key:
                                try:
                                    note_num = midi_key.split('note')[1]
                                    note_name = self.get_note_name(int(note_num))
                                    note_display = f"{note_name} ({note_num})"
                                except:
                                    note_display = note_num
                            else:
                                note_display = midi_key
                            
                            deck = params.get('deck_id', 'N/A')
                            preset = params.get('preset_name', 'Clear')
                            
                            f.write(f"  {note_display} -> Deck {deck}: {preset}\n")
                        f.write("\n")
                    
                    # Escribir mix actions
                    if mix_mappings:
                        f.write("=== MIX ACTIONS ===\n")
                        for action_id, mapping_data in sorted(mix_mappings, key=lambda x: x[1].get('midi', '')):
                            midi_key = mapping_data.get('midi', '')
                            params = mapping_data.get('params', {})
                            
                            # Extraer nota
                            if 'note' in midi_key:
                                try:
                                    note_num = midi_key.split('note')[1]
                                    note_name = self.get_note_name(int(note_num))
                                    note_display = f"{note_name} ({note_num})"
                                except:
                                    note_display = midi_key
                            else:
                                note_display = midi_key
                            
                            preset = params.get('preset', 'N/A')
                            duration = params.get('duration', 'instant')
                            
                            f.write(f"  {note_display} -> {preset} ({duration})\n")
                        f.write("\n")
                    
                    # Escribir controles
                    if control_mappings:
                        f.write("=== CONTROL MAPPINGS ===\n")
                        for action_id, mapping_data in control_mappings:
                            midi_key = mapping_data.get('midi', '')
                            params = mapping_data.get('params', {})
                            f.write(f"  {midi_key} -> {params}\n")
                        f.write("\n")
                
                QMessageBox.information(self, "Exportar", f"Mappings exportados en formato legible a:\n{filename}")
                
        except Exception as e:
            logging.error(f"Error exporting readable: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando: {str(e)}")
    
    def import_json(self):
        """Importar mappings desde JSON"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getOpenFileName(
                self, "Importar Mappings MIDI", 
                "", "JSON files (*.json)"
            )
            
            if filename:
                result = QMessageBox.question(
                    self, "Confirmar Importación",
                    "¿Quieres reemplazar todos los mappings actuales?\n\n"
                    "Esta acción no se puede deshacer.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if result == QMessageBox.StandardButton.Yes:
                    if self.midi_engine and self.midi_engine.import_mappings_from_file(filename):
                        QMessageBox.information(self, "Importar", "Mappings importados correctamente")
                        self.load_current_mappings()
                    else:
                        QMessageBox.warning(self, "Error", "No se pudo importar el archivo")
                        
        except Exception as e:
            logging.error(f"Error importing JSON: {e}")
            QMessageBox.critical(self, "Error", f"Error importando: {str(e)}")
    
    def load_template(self, template_name):
        """Cargar template predefinido"""
        try:
            if template_name == "ableton_push":
                self.load_ableton_push_template()
            elif template_name == "apc40":
                self.load_apc40_template()
            elif template_name == "generic":
                self.load_generic_template()
            
        except Exception as e:
            logging.error(f"Error loading template {template_name}: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando template: {str(e)}")
    
    def load_ableton_push_template(self):
        """Cargar template para Ableton Push"""
        result = QMessageBox.question(
            self, "Cargar Template Ableton Push",
            "¿Cargar configuración optimizada para Ableton Push?\n\n"
            "Esto reemplazará la configuración actual.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Template específico para Push (pads 36-99)
            self.start_note_spin.setValue(36)
            self.end_note_spin.setValue(99)
            self.update_notes_table()
            QMessageBox.information(self, "Template", "Template Ableton Push cargado")
    
    def load_apc40_template(self):
        """Cargar template para APC40"""
        result = QMessageBox.question(
            self, "Cargar Template APC40",
            "¿Cargar configuración optimizada para APC40?\n\n"
            "Esto reemplazará la configuración actual.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Template específico para APC40
            self.start_note_spin.setValue(53)  # Clip launch buttons
            self.end_note_spin.setValue(92)
            self.update_notes_table()
            QMessageBox.information(self, "Template", "Template APC40 cargado")
    
    def load_generic_template(self):
        """Cargar template genérico"""
        result = QMessageBox.question(
            self, "Cargar Template Genérico",
            "¿Cargar configuración genérica?\n\n"
            "Configuración estándar para controladores MIDI generales.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Template genérico (rango estándar)
            self.start_note_spin.setValue(36)
            self.end_note_spin.setValue(71)
            self.update_notes_table()
            QMessageBox.information(self, "Template", "Template genérico cargado")
    
    # === FUNCIONES DE GESTIÓN ===
    
    def add_custom_mapping(self):
        """Añadir mapping personalizado"""
        try:
            # Crear diálogo simple para mapping personalizado
            from PyQt6.QtWidgets import QDialog, QFormLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Añadir Mapping Personalizado")
            dialog.setModal(True)
            
            layout = QFormLayout(dialog)
            
            # Tipo de acción
            action_type_combo = QComboBox()
            action_type_combo.addItems(["load_preset", "crossfade_action", "control_parameter"])
            layout.addRow("Tipo de Acción:", action_type_combo)
            
            # MIDI Key
            midi_key_edit = QLineEdit()
            midi_key_edit.setPlaceholderText("ej: note_on_ch0_note60")
            layout.addRow("MIDI Key:", midi_key_edit)
            
            # Parámetros (JSON)
            params_edit = QTextEdit()
            params_edit.setMaximumHeight(100)
            params_edit.setPlainText('{"deck_id": "A", "preset_name": "Abstract Lines"}')
            layout.addRow("Parámetros (JSON):", params_edit)
            
            # Botones
            from PyQt6.QtWidgets import QDialogButtonBox
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                try:
                    import json
                    action_type = action_type_combo.currentText()
                    midi_key = midi_key_edit.text().strip()
                    params_text = params_edit.toPlainText()
                    
                    if not midi_key:
                        QMessageBox.warning(self, "Error", "MIDI Key no puede estar vacío")
                        return
                    
                    params = json.loads(params_text)
                    
                    action_id = self.midi_engine.add_custom_mapping(action_type, params, midi_key)
                    
                    if action_id:
                        QMessageBox.information(self, "Éxito", f"Mapping personalizado añadido: {action_id}")
                        self.load_current_mappings()
                    else:
                        QMessageBox.warning(self, "Error", "No se pudo añadir el mapping")
                        
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Error", "Los parámetros deben ser JSON válido")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error añadiendo mapping: {str(e)}")
                    
        except Exception as e:
            logging.error(f"Error adding custom mapping: {e}")
    
    def clear_all_mappings(self):
        """Limpiar todos los mappings"""
        result = QMessageBox.question(
            self, "Confirmar",
            "¿Eliminar TODOS los mappings MIDI?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            if self.midi_engine:
                self.midi_engine.clear_all_mappings()
                self.load_current_mappings()
                QMessageBox.information(self, "Limpiar", "Todos los mappings han sido eliminados")
    
    def restore_defaults(self):
        """Restaurar mappings por defecto"""
        result = QMessageBox.question(
            self, "Restaurar Defaults",
            "¿Restaurar la configuración MIDI por defecto?\n\n"
            "Esto eliminará todos los mappings actuales.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            if self.midi_engine:
                # Limpiar mappings actuales
                self.midi_engine.clear_all_mappings()
                
                # Recrear defaults
                default_mappings = self.midi_engine.create_default_midi_mappings()
                self.midi_engine.set_midi_mappings(default_mappings)
                
                self.load_current_mappings()
                QMessageBox.information(self, "Restaurar", "Configuración por defecto restaurada")
    
    def edit_mapping(self, action_id):
        """Editar mapping existente"""
        try:
            # Implementar editor de mapping
            QMessageBox.information(self, "Editor", f"Editor para {action_id} (por implementar)")
        except Exception as e:
            logging.error(f"Error editing mapping: {e}")
    
    def delete_mapping(self, action_id):
        """Eliminar mapping específico"""
        result = QMessageBox.question(
            self, "Eliminar Mapping",
            f"¿Eliminar el mapping '{action_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            if self.midi_engine:
                self.midi_engine.remove_midi_mapping(action_id)
                self.load_current_mappings()
    
    def test_random_mapping(self):
        """Probar un mapping aleatorio"""
        try:
            if self.midi_engine:
                mappings = self.midi_engine.get_midi_mappings()
                if mappings:
                    import random
                    action_id = random.choice(list(mappings.keys()))
                    mapping_data = mappings[action_id]
                    midi_key = mapping_data.get('midi', '')
                    
                    # Extraer nota si es un mapping de nota
                    if 'note' in midi_key:
                        try:
                            note = int(midi_key.split('note')[1])
                            self.midi_engine.test_midi_mapping(note)
                            QMessageBox.information(self, "Test", 
                                                  f"Probando mapping: {action_id}\n"
                                                  f"MIDI: {midi_key}\n"
                                                  f"Revisa la consola para detalles.")
                        except:
                            QMessageBox.information(self, "Test", 
                                                  f"Mapping seleccionado: {action_id}\n"
                                                  f"MIDI: {midi_key}")
                    else:
                        QMessageBox.information(self, "Test", 
                                              f"Mapping seleccionado: {action_id}\n"
                                              f"MIDI: {midi_key}")
                else:
                    QMessageBox.information(self, "Test", "No hay mappings para probar")
            else:
                QMessageBox.warning(self, "Test", "MIDI Engine no disponible")
                
        except Exception as e:
            logging.error(f"Error testing random mapping: {e}")
    
    def save_mappings(self):
        """Guardar mappings manualmente"""
        try:
            if self.midi_engine:
                # Los mappings ya se guardan automáticamente, pero podemos forzar un guardado
                mappings = self.midi_engine.get_midi_mappings()
                self.midi_engine.set_midi_mappings(mappings)
                QMessageBox.information(self, "Guardar", 
                                      f"Mappings guardados correctamente.\n"
                                      f"Total: {len(mappings)} mappings")
            else:
                QMessageBox.warning(self, "Guardar", "MIDI Engine no disponible")
                
        except Exception as e:
            logging.error(f"Error saving mappings: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando: {str(e)}")
    
    def refresh_ui(self):
        """Refrescar toda la interfaz"""
        try:
            self.update_midi_status()
            self.load_current_mappings()
            self.update_channel_info()
        except Exception as e:
            logging.error(f"Error refreshing UI: {e}")


# === WIDGET INTEGRADO PARA CONTROL PANEL ===

class CompactMidiConfigWidget(QWidget):
    """Versión compacta del configurador MIDI para embedding"""
    
    def __init__(self, midi_engine, visualizer_manager, deck_id=None, parent=None):
        super().__init__(parent)
        self.midi_engine = midi_engine
        self.visualizer_manager = visualizer_manager
        self.deck_id = deck_id  # Para filtrar por deck
        
        self.init_compact_ui()
        self.load_deck_mappings()
    
    def init_compact_ui(self):
        """UI compacta para embedding en control panel"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header compacto
        header_layout = QHBoxLayout()
        
        title = f"MIDI Config {self.deck_id}" if self.deck_id else "MIDI Config"
        header_label = QLabel(title)
        header_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Botón para abrir configuración completa
        config_btn = QPushButton("⚙️")
        config_btn.setMaximumWidth(30)
        config_btn.setToolTip("Configuración completa")
        config_btn.clicked.connect(self.open_full_config)
        header_layout.addWidget(config_btn)
        
        layout.addLayout(header_layout)
        
        # Lista compacta de mappings
        self.compact_table = QTableWidget()
        self.compact_table.setColumnCount(3)
        self.compact_table.setHorizontalHeaderLabels(["Nota", "Preset", "Controles"])
        self.compact_table.setMaximumHeight(200)
        
        # Configurar tabla compacta
        header = self.compact_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        
        self.compact_table.setColumnWidth(0, 60)
        self.compact_table.setColumnWidth(2, 80)
        
        layout.addWidget(self.compact_table)
    
    def load_deck_mappings(self):
        """Cargar mappings específicos del deck"""
        try:
            if not self.midi_engine or not self.deck_id:
                return
                
            mappings = self.midi_engine.get_midi_mappings()
            deck_mappings = []
            
            for action_id, mapping_data in mappings.items():
                params = mapping_data.get('params', {})
                if params.get('deck_id') == self.deck_id:
                    deck_mappings.append((action_id, mapping_data))
            
            self.compact_table.setRowCount(len(deck_mappings))
            
            for row, (action_id, mapping_data) in enumerate(deck_mappings):
                midi_key = mapping_data.get('midi', '')
                params = mapping_data.get('params', {})
                
                # Extraer nota
                note_display = "N/A"
                if 'note' in midi_key:
                    try:
                        note_num = int(midi_key.split('note')[1])
                        note_name = self.get_note_name(note_num)
                        note_display = f"{note_name} ({note_num})"
                    except:
                        note_display = midi_key
                
                note_item = QTableWidgetItem(note_display)
                note_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.compact_table.setItem(row, 0, note_item)
                
                # Preset
                preset = params.get('preset_name', 'Clear')
                preset_item = QTableWidgetItem(str(preset))
                self.compact_table.setItem(row, 1, preset_item)
                
                # Controles compactos
                controls = QPushButton("⚙️")
                controls.setMaximumWidth(30)
                controls.clicked.connect(lambda checked, aid=action_id: self.edit_compact_mapping(aid))
                self.compact_table.setCellWidget(row, 2, controls)
            
        except Exception as e:
            logging.error(f"Error loading deck mappings: {e}")
    
    def get_note_name(self, note_number):
        """Convertir número de nota a nombre"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note_name = note_names[note_number % 12]
        return f"{note_name}{octave}"
    
    def open_full_config(self):
        """Abrir configuración completa"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Configuración MIDI Completa")
            dialog.setModal(True)
            dialog.resize(1200, 800)
            
            layout = QVBoxLayout(dialog)
            
            config_widget = MidiConfigWidget(self.midi_engine, self.visualizer_manager, dialog)
            layout.addWidget(config_widget)
            
            # Botón cerrar
            from PyQt6.QtWidgets import QDialogButtonBox
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(dialog.accept)
            layout.addWidget(buttons)
            
            dialog.exec()
            
            # Recargar después de cerrar
            self.load_deck_mappings()
            
        except Exception as e:
            logging.error(f"Error opening full config: {e}")
    
    def edit_compact_mapping(self, action_id):
        """Editar mapping en vista compacta"""
        try:
            QMessageBox.information(self, "Editor", f"Editando {action_id}\n(Funcionalidad por implementar)")
        except Exception as e:
            logging.error(f"Error editing compact mapping: {e}")

import time