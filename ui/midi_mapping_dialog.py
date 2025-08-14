# ui/midi_mapping_dialog.py

import json
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialogButtonBox, QLabel,
    QMessageBox, QGroupBox, QProgressBar, QComboBox, QWidget,
    QLineEdit, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush

class MidiMappingDialog(QDialog):
    # Señales
    start_midi_learn = pyqtSignal(int)  # Emite el row index que está aprendiendo
    mappings_saved = pyqtSignal(dict)

    def __init__(self, visualizer_presets, midi_engine, deck_id=None, parent=None, as_widget=False):
        """Create the dialog.

        Parameters
        ----------
        visualizer_presets: list
            Available visualizer names.
        midi_engine: object
            Engine handling MIDI operations.
        deck_id: str | None
            Optional deck identifier ("A" or "B").
        parent: QWidget | None
            Parent widget.
        as_widget: bool
            When True the dialog behaves as a normal widget so it can be
            embedded directly into other layouts instead of opening a new
            window.  This is used by the redesigned control panel where MIDI
            mappings live inside each deck section.
        """
        super().__init__(parent)
        self.as_widget = as_widget
        title = "Configuración de Mapeo MIDI"
        if deck_id:
            title += f" - Deck {deck_id}"
        self.setWindowTitle(title)

        # When used as an embedded widget we keep the size compact
        if as_widget:
            self.setWindowFlags(Qt.WindowType.Widget)
            self.setMinimumSize(0, 0)
            self.resize(400, 250)
        else:
            self.setMinimumSize(1000, 700)
            self.resize(1200, 800)

        self.visualizer_presets = visualizer_presets or []
        self.midi_engine = midi_engine
        self.deck_id = deck_id
        self.deck_target = f"deck{deck_id.lower()}" if deck_id else None
        self.existing_engine_mappings = {}
        self.learning_row = -1
        self.learning_timeout_timer = QTimer()
        self.learning_timeout_timer.setSingleShot(True)
        self.learning_timeout_timer.timeout.connect(self.stop_learning)
        
        # Cargar mapeos existentes y convertir al formato interno
        try:
            if hasattr(self.midi_engine, 'get_midi_mappings'):
                self.existing_engine_mappings = self.midi_engine.get_midi_mappings()
                dialog_mappings = self.convert_engine_mappings_to_dialog_format(self.existing_engine_mappings)
                if self.deck_target:
                    self.mappings = [m for m in dialog_mappings if m.get('target') == self.deck_target]
                else:
                    self.mappings = dialog_mappings
                logging.info(f"Loaded {len(self.mappings)} existing mappings from engine")
            else:
                self.mappings = []
        except Exception as e:
            logging.warning(f"Could not load existing mappings: {e}")
            self.mappings = []

        # Conectar señal MIDI si está disponible
        if self.midi_engine and hasattr(self.midi_engine, 'midi_message_received_for_learning'):
            try:
                self.midi_engine.midi_message_received_for_learning.connect(self.on_midi_learned)
                logging.debug("Connected to MIDI learning signal")
            except Exception as e:
                logging.warning(f"Could not connect MIDI learning signal: {e}")

        self.init_ui()
        self.populate_table()

    def convert_engine_mappings_to_dialog_format(self, engine_mappings):
        """Convierte mapeos del engine al formato del diálogo"""
        dialog_mappings = []
        try:
            for action_id, mapping_data in engine_mappings.items():
                if isinstance(mapping_data, dict):
                    action_type = mapping_data.get('type', 'unknown')
                    params = mapping_data.get('params', {})
                    midi_key = mapping_data.get('midi', 'Sin asignar')
                    
                    if action_type == 'load_preset':
                        dialog_mapping = {
                            'action': 'Set Preset',
                            'preset': params.get('preset_name', ''),
                            'target': f"deck{params.get('deck_id', 'A')}",
                            'values': params.get('custom_values', ''),
                            'midi': midi_key
                        }
                        dialog_mappings.append(dialog_mapping)
                        
                    elif action_type == 'crossfade_action':
                        dialog_mapping = {
                            'action': 'Mix Fader',
                            'preset': params.get('preset', 'A to B'),
                            'target': params.get('target', 'Visual Mix'),
                            'values': params.get('duration', ''),
                            'midi': midi_key
                        }
                        dialog_mappings.append(dialog_mapping)
                        
                    elif action_type == 'control_parameter':
                        dialog_mapping = {
                            'action': 'Control Parameter',
                            'preset': params.get('preset', 'Custom'),
                            'target': params.get('target', 'deckA'),
                            'values': params.get('values', ''),
                            'midi': midi_key
                        }
                        dialog_mappings.append(dialog_mapping)
                        
        except Exception as e:
            logging.error(f"Error converting engine mappings: {e}")
        
        return dialog_mappings

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        if self.as_widget:
            layout.setContentsMargins(0, 0, 0, 0)

        # Título
        title_label = QLabel("Configuración de Mapeo MIDI" if not self.as_widget else "MIDI Mapping")
        title_font = QFont()
        title_font.setPointSize(14 if not self.as_widget else 10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Estado MIDI
        status_group = QGroupBox("Estado MIDI")
        status_layout = QVBoxLayout(status_group)
        
        self.midi_status_label = QLabel("Verificando estado MIDI...")
        self.update_midi_status()
        status_layout.addWidget(self.midi_status_label)

        self.learning_status_label = QLabel("Listo para configurar mapeos MIDI")
        self.learning_status_label.setStyleSheet("color: green; font-weight: bold;")
        status_layout.addWidget(self.learning_status_label)

        self.learning_progress = QProgressBar()
        self.learning_progress.setVisible(False)
        self.learning_progress.setMaximum(100)
        status_layout.addWidget(self.learning_progress)

        if self.as_widget:
            status_group.setMaximumHeight(80)
        layout.addWidget(status_group)

        # Instrucciones
        if not self.as_widget:
            instructions = QLabel(
                "Instrucciones:\n"
                "1. Haz clic en 'Add Mapping' para añadir una nueva asignación\n"
                "2. Configura la acción, preset, target y valores\n"
                "3. Haz clic en 'Learn' y envía el mensaje MIDI desde tu controlador\n"
                "4. Haz clic en 'Save' para guardar todos los cambios"
            )
            instructions.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
            layout.addWidget(instructions)

        # Botón Add Mapping
        add_button_layout = QHBoxLayout()
        self.add_mapping_btn = QPushButton("Add Mapping")
        self.add_mapping_btn.clicked.connect(self.add_new_mapping)
        self.add_mapping_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        add_button_layout.addWidget(self.add_mapping_btn)
        add_button_layout.addStretch()
        layout.addLayout(add_button_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Action, Preset, Target, Values, MIDI, Controls
        self.table.setHorizontalHeaderLabels(["Action", "Preset", "Target", "Values", "MIDI", "Controls"])
        
        # Configurar columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Action
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Preset
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Target
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Values
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # MIDI
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)             # Controls
        self.table.setColumnWidth(5, 100)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        if self.as_widget:
            self.table.setMaximumHeight(150)
        layout.addWidget(self.table)

        # Botones
        button_layout = QHBoxLayout()
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_mappings)
        clear_all_btn.setStyleSheet("background-color: #ffcccc;")
        button_layout.addWidget(clear_all_btn)
        
        button_layout.addStretch()

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.save_mappings)
        button_box.rejected.connect(self.reject)

        apply_btn = button_box.button(QDialogButtonBox.StandardButton.Apply)
        if apply_btn:
            apply_btn.clicked.connect(self.apply_mappings)
            if self.as_widget:
                apply_btn.hide()
        if self.as_widget:
            cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
            if cancel_btn:
                cancel_btn.hide()

        button_layout.addWidget(button_box)
        layout.addLayout(button_layout)

    def get_action_definitions(self):
        """Define todas las acciones disponibles y sus presets"""
        return {
            "Set Preset": {
                "presets": self.visualizer_presets,
                "targets": ["deckA", "deckB"],
                "values_template": "lines:2;speed:20",
                "description": "Carga un preset visual en un deck"
            },
            "Mix Fader": {
                "presets": ["A to B", "B to A", "Cut to Center", "Instant A", "Instant B"],
                "targets": ["Visual Mix"],
                "values_template": "duration:5s",
                "description": "Controla el crossfader/mezclador"
            },
            "Control Parameter": {
                "presets": ["Speed", "Intensity", "Color", "Size", "Custom"],
                "targets": ["deckA", "deckB", "Both Decks"],
                "values_template": "parameter:speed;min:0;max:100",
                "description": "Controla parámetros específicos del visualizador"
            }
        }

    def add_new_mapping(self):
        """Añadir un nuevo mapeo a la tabla"""
        target = self.deck_target if self.deck_target else 'deckA'
        new_mapping = {
            'action': 'Set Preset',
            'preset': self.visualizer_presets[0] if self.visualizer_presets else '',
            'target': target,
            'values': '',
            'midi': 'Sin asignar'
        }
        self.mappings.append(new_mapping)
        self.populate_table()
        
        # Scroll to the new row
        new_row = len(self.mappings) - 1
        self.table.scrollToItem(self.table.item(new_row, 0))

    def populate_table(self):
        """Poblar la tabla con los mapeos actuales"""
        self.table.setRowCount(len(self.mappings))
        action_definitions = self.get_action_definitions()

        for row, mapping in enumerate(self.mappings):
            try:
                # Columna 0: Action (ComboBox)
                action_combo = QComboBox()
                action_combo.addItems(list(action_definitions.keys()))
                current_action = mapping.get('action', 'Set Preset')
                if current_action in action_definitions:
                    action_combo.setCurrentText(current_action)
                action_combo.currentTextChanged.connect(lambda text, r=row: self.on_action_changed(r, text))
                self.table.setCellWidget(row, 0, action_combo)

                # Columna 1: Preset (ComboBox)
                preset_combo = QComboBox()
                current_action = mapping.get('action', 'Set Preset')
                if current_action in action_definitions:
                    preset_combo.addItems(action_definitions[current_action]["presets"])
                current_preset = mapping.get('preset', '')
                if current_preset and current_preset in action_definitions[current_action]["presets"]:
                    preset_combo.setCurrentText(current_preset)
                preset_combo.currentTextChanged.connect(lambda text, r=row: self.on_preset_changed(r, text))
                self.table.setCellWidget(row, 1, preset_combo)

                # Columna 2: Target (ComboBox)
                target_combo = QComboBox()
                if self.deck_target:
                    target_combo.addItem(self.deck_target)
                    target_combo.setCurrentText(self.deck_target)
                    target_combo.setEnabled(False)
                else:
                    if current_action in action_definitions:
                        target_combo.addItems(action_definitions[current_action]["targets"])
                    current_target = mapping.get('target', 'deckA')
                    if current_target and current_target in action_definitions[current_action]["targets"]:
                        target_combo.setCurrentText(current_target)
                    target_combo.currentTextChanged.connect(lambda text, r=row: self.on_target_changed(r, text))
                self.table.setCellWidget(row, 2, target_combo)

                # Columna 3: Values (LineEdit)
                values_edit = QLineEdit()
                values_edit.setText(mapping.get('values', ''))
                if current_action in action_definitions:
                    values_edit.setPlaceholderText(action_definitions[current_action]["values_template"])
                values_edit.textChanged.connect(lambda text, r=row: self.on_values_changed(r, text))
                self.table.setCellWidget(row, 3, values_edit)

                # Columna 4: MIDI (Label)
                midi_item = QTableWidgetItem(mapping.get('midi', 'Sin asignar'))
                midi_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                if mapping.get('midi', 'Sin asignar') != 'Sin asignar':
                    midi_item.setBackground(QBrush(QColor(200, 255, 200)))
                self.table.setItem(row, 4, midi_item)

                # Columna 5: Controls (Buttons)
                controls_widget = self.create_control_buttons(row)
                self.table.setCellWidget(row, 5, controls_widget)

            except Exception as e:
                logging.error(f"Error populating table row {row}: {e}")
                continue
        
        self.table.resizeRowsToContents()

    def create_control_buttons(self, row):
        """Crear botones de control para cada fila"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Botón Learn
        learn_btn = QPushButton("Learn")
        learn_btn.setFixedSize(45, 25)
        learn_btn.clicked.connect(lambda: self.learn_midi(row))
        layout.addWidget(learn_btn)

        # Botón Delete
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(25, 25)
        delete_btn.setToolTip("Eliminar mapeo")
        delete_btn.setStyleSheet("background-color: #ffcccc;")
        delete_btn.clicked.connect(lambda: self.delete_mapping(row))
        layout.addWidget(delete_btn)

        return widget

    def on_action_changed(self, row, action):
        """Manejar cambio de acción"""
        if row < len(self.mappings):
            self.mappings[row]['action'] = action
            # Actualizar presets y targets disponibles
            self.update_row_options(row)

    def on_preset_changed(self, row, preset):
        """Manejar cambio de preset"""
        if row < len(self.mappings):
            self.mappings[row]['preset'] = preset

    def on_target_changed(self, row, target):
        """Manejar cambio de target"""
        if row < len(self.mappings):
            self.mappings[row]['target'] = target

    def on_values_changed(self, row, values):
        """Manejar cambio de valores"""
        if row < len(self.mappings):
            self.mappings[row]['values'] = values

    def update_row_options(self, row):
        """Actualizar las opciones de preset y target para una fila"""
        if row >= len(self.mappings):
            return
            
        action = self.mappings[row]['action']
        action_definitions = self.get_action_definitions()
        
        if action in action_definitions:
            # Actualizar preset combo
            preset_combo = self.table.cellWidget(row, 1)
            if isinstance(preset_combo, QComboBox):
                preset_combo.clear()
                preset_combo.addItems(action_definitions[action]["presets"])

            # Actualizar target combo
            target_combo = self.table.cellWidget(row, 2)
            if isinstance(target_combo, QComboBox):
                target_combo.clear()
                if self.deck_target:
                    target_combo.addItem(self.deck_target)
                    target_combo.setCurrentText(self.deck_target)
                    target_combo.setEnabled(False)
                else:
                    target_combo.addItems(action_definitions[action]["targets"])

            # Actualizar placeholder de values
            values_edit = self.table.cellWidget(row, 3)
            if isinstance(values_edit, QLineEdit):
                values_edit.setPlaceholderText(action_definitions[action]["values_template"])

    def learn_midi(self, row):
        """Iniciar aprendizaje MIDI para una fila específica"""
        self.update_midi_status()
        
        if not self.midi_engine:
            QMessageBox.warning(self, "Error MIDI", "Motor MIDI no disponible")
            return

        # Verificar conexión MIDI
        midi_connected = False
        try:
            if hasattr(self.midi_engine, 'is_port_open'):
                midi_connected = self.midi_engine.is_port_open()
            elif hasattr(self.midi_engine, 'is_connected'):
                midi_connected = self.midi_engine.is_connected()
        except Exception as e:
            logging.error(f"Error checking MIDI connection: {e}")

        if not midi_connected:
            QMessageBox.warning(self, "MIDI No Conectado", 
                               "No hay dispositivos MIDI conectados.\n"
                               "Conecta un dispositivo MIDI en Preferencias.")
            return

        # Iniciar aprendizaje
        self.learning_row = row
        self.start_midi_learn.emit(row)
        
        # Actualizar UI
        self.learning_status_label.setText(f"🎵 Escuchando MIDI para fila {row + 1}...")
        self.learning_status_label.setStyleSheet("color: blue; font-weight: bold;")
        
        # Mostrar progreso
        self.learning_progress.setVisible(True)
        self.learning_progress.setValue(0)
        self.start_progress_animation()
        
        # Resaltar fila
        self.highlight_learning_row(row)
        
        # Timeout
        self.learning_timeout_timer.start(10000)

    def start_progress_animation(self):
        """Iniciar animación de progreso"""
        self.progress_timer = QTimer()
        self.progress_value = 0
        
        def update_progress():
            self.progress_value += 1
            self.learning_progress.setValue(self.progress_value)
            if self.progress_value >= 100:
                self.progress_timer.stop()
        
        self.progress_timer.timeout.connect(update_progress)
        self.progress_timer.start(100)

    def highlight_learning_row(self, row):
        """Resaltar la fila que está aprendiendo"""
        for r in range(self.table.rowCount()):
            midi_item = self.table.item(r, 4)
            if midi_item:
                if r == row:
                    midi_item.setBackground(QBrush(QColor(255, 255, 150)))  # Yellow
                    midi_item.setText("Escuchando...")
                else:
                    # Restaurar color normal
                    if midi_item.text() != 'Sin asignar':
                        midi_item.setBackground(QBrush(QColor(200, 255, 200)))  # Green
                    else:
                        midi_item.setBackground(QBrush(QColor(255, 255, 255)))  # White

    def on_midi_learned(self, message_key):
        """Manejar mensaje MIDI aprendido"""
        if self.learning_row < 0:
            return

        try:
            # Parar timers
            self.learning_timeout_timer.stop()
            if hasattr(self, 'progress_timer'):
                self.progress_timer.stop()

            # Verificar duplicados
            for i, mapping in enumerate(self.mappings):
                if i != self.learning_row and mapping.get('midi') == message_key:
                    result = QMessageBox.question(
                        self, "Asignación Duplicada",
                        f"El control MIDI '{message_key}' ya está asignado a la fila {i + 1}.\n"
                        f"¿Quieres reasignarlo a la fila {self.learning_row + 1}?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if result == QMessageBox.StandardButton.No:
                        self.stop_learning()
                        return
                    
                    # Limpiar asignación anterior
                    self.mappings[i]['midi'] = 'Sin asignar'

            # Asignar nuevo MIDI
            self.mappings[self.learning_row]['midi'] = message_key
            
            # Actualizar UI
            self.learning_status_label.setText(f"✅ Asignado: {message_key}")
            self.learning_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Actualizar tabla
            self.populate_table()
            
            logging.info(f"MIDI learned: {message_key} for row {self.learning_row}")
            
        except Exception as e:
            logging.error(f"Error processing MIDI learning: {e}")
            QMessageBox.critical(self, "Error", f"Error al procesar MIDI: {str(e)}")
        
        finally:
            self.stop_learning()

    def stop_learning(self):
        """Detener el proceso de aprendizaje"""
        self.learning_row = -1
        self.learning_timeout_timer.stop()
        
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        
        self.learning_progress.setVisible(False)
        self.learning_status_label.setText("Listo para configurar mapeos MIDI")
        self.learning_status_label.setStyleSheet("color: green; font-weight: bold;")
        
        # Restaurar colores de tabla
        self.populate_table()

    def delete_mapping(self, row):
        """Eliminar un mapeo"""
        if 0 <= row < len(self.mappings):
            result = QMessageBox.question(
                self, "Confirmar",
                f"¿Eliminar el mapeo de la fila {row + 1}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                del self.mappings[row]
                self.populate_table()

    def clear_all_mappings(self):
        """Limpiar todos los mapeos"""
        result = QMessageBox.question(
            self, "Confirmar",
            "¿Eliminar todos los mapeos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            self.mappings.clear()
            self.populate_table()

    def update_midi_status(self):
        """Actualizar estado MIDI"""
        if not self.midi_engine:
            self.midi_status_label.setText("❌ Motor MIDI no disponible")
            self.midi_status_label.setStyleSheet("color: red; font-weight: bold;")
            return

        try:
            midi_connected = False
            if hasattr(self.midi_engine, 'is_port_open'):
                midi_connected = self.midi_engine.is_port_open()
            elif hasattr(self.midi_engine, 'is_connected'):
                midi_connected = self.midi_engine.is_connected()
            
            if midi_connected:
                device_name = ""
                if hasattr(self.midi_engine, 'get_connected_device_name'):
                    device_name = self.midi_engine.get_connected_device_name() or ""
                
                self.midi_status_label.setText(f"✅ MIDI conectado: {device_name}")
                self.midi_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.midi_status_label.setText("❌ MIDI desconectado")
                self.midi_status_label.setStyleSheet("color: red; font-weight: bold;")
                
        except Exception as e:
            self.midi_status_label.setText(f"❌ Error MIDI: {str(e)}")
            self.midi_status_label.setStyleSheet("color: red; font-weight: bold;")

    def convert_to_engine_format(self):
        """Convertir mapeos al formato que espera el engine"""
        engine_mappings = {}
        
        for i, mapping in enumerate(self.mappings):
            if mapping.get('midi', 'Sin asignar') == 'Sin asignar':
                continue
                
            action_id = f"mapping_{i}"
            action = mapping.get('action', '')
            preset = mapping.get('preset', '')
            target = mapping.get('target', '')
            values = mapping.get('values', '')
            midi_key = mapping.get('midi', '')
            
            if action == 'Set Preset':
                engine_mappings[action_id] = {
                    'type': 'load_preset',
                    'params': {
                        'deck_id': target.replace('deck', '').upper(),
                        'preset_name': preset,
                        'custom_values': values
                    },
                    'midi': midi_key
                }
            elif action == 'Mix Fader':
                engine_mappings[action_id] = {
                    'type': 'crossfade_action',
                    'params': {
                        'preset': preset,
                        'duration': values,
                        'target': target
                    },
                    'midi': midi_key
                }
            elif action == 'Control Parameter':
                engine_mappings[action_id] = {
                    'type': 'control_parameter',
                    'params': {
                        'preset': preset,
                        'target': target,
                        'values': values
                    },
                    'midi': midi_key
                }
        
        logging.info(f"Converted {len(self.mappings)} dialog mappings to {len(engine_mappings)} engine mappings")
        return engine_mappings

    def apply_mappings(self):
        """Aplicar mapeos sin cerrar diálogo"""
        try:
            engine_mappings = self.convert_to_engine_format()
            if self.deck_target and self.midi_engine and hasattr(self.midi_engine, 'get_midi_mappings'):
                existing = self.midi_engine.get_midi_mappings()
                to_remove = []
                for action_id, data in existing.items():
                    try:
                        action_type = data.get('type')
                        params = data.get('params', {})
                        deck = None
                        if action_type == 'load_preset':
                            deck = params.get('deck_id')
                        elif action_type == 'control_parameter':
                            target = params.get('target', '')
                            if target.startswith('deck'):
                                deck = target.replace('deck', '').upper()
                        if deck and deck.lower() == self.deck_target.replace('deck', ''):
                            to_remove.append(action_id)
                    except Exception:
                        continue
                for action_id in to_remove:
                    existing.pop(action_id, None)
                existing.update(engine_mappings)
                engine_mappings = existing
            if self.midi_engine and hasattr(self.midi_engine, 'set_midi_mappings'):
                self.midi_engine.set_midi_mappings(engine_mappings)
                logging.info(f"Applied {len(engine_mappings)} MIDI mappings to engine")
            
            self.mappings_saved.emit(engine_mappings)
            
            self.learning_status_label.setText("✅ Mapeos aplicados correctamente")
            self.learning_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            QTimer.singleShot(2000, lambda: self.learning_status_label.setText("Listo para configurar mapeos MIDI"))
            
        except Exception as e:
            logging.error(f"Error applying mappings: {e}")
            QMessageBox.critical(self, "Error", f"Error al aplicar mapeos: {str(e)}")

    def save_mappings(self):
        """Guardar mapeos y cerrar diálogo"""
        try:
            engine_mappings = self.convert_to_engine_format()
            if self.deck_target and self.midi_engine and hasattr(self.midi_engine, 'get_midi_mappings'):
                existing = self.midi_engine.get_midi_mappings()
                to_remove = []
                for action_id, data in existing.items():
                    try:
                        action_type = data.get('type')
                        params = data.get('params', {})
                        deck = None
                        if action_type == 'load_preset':
                            deck = params.get('deck_id')
                        elif action_type == 'control_parameter':
                            target = params.get('target', '')
                            if target.startswith('deck'):
                                deck = target.replace('deck', '').upper()
                        if deck and deck.lower() == self.deck_target.replace('deck', ''):
                            to_remove.append(action_id)
                    except Exception:
                        continue
                for action_id in to_remove:
                    existing.pop(action_id, None)
                existing.update(engine_mappings)
                engine_mappings = existing
            if self.midi_engine and hasattr(self.midi_engine, 'set_midi_mappings'):
                self.midi_engine.set_midi_mappings(engine_mappings)
                logging.info(f"Saved {len(engine_mappings)} MIDI mappings to engine")

            self.mappings_saved.emit(engine_mappings)
            self.accept()
            
        except Exception as e:
            logging.error(f"Error saving mappings: {e}")
            QMessageBox.critical(self, "Error", f"Error al guardar mapeos: {str(e)}")

    def closeEvent(self, event):
        """Manejar cierre del diálogo"""
        self.stop_learning()
        
        if (self.midi_engine and 
            hasattr(self.midi_engine, 'midi_message_received_for_learning')):
            try:
                self.midi_engine.midi_message_received_for_learning.disconnect(self.on_midi_learned)
            except Exception as e:
                logging.warning(f"Could not disconnect MIDI signal: {e}")
        
        super().closeEvent(event)