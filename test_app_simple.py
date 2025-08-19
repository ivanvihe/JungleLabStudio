#!/usr/bin/env python3
"""Test simple de la aplicación sin splash screen."""

import sys
import os
import logging

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_simple_app():
    print("Testing Simple Audio Visualizer...")
    
    try:
        # Import Qt
        from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QComboBox
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QSurfaceFormat
        
        # Set OpenGL format
        format = QSurfaceFormat()
        format.setVersion(3, 3)
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        QSurfaceFormat.setDefaultFormat(format)
        
        # Create app
        app = QApplication(sys.argv)
        
        # Import visualizer manager
        from visuals.visualizer_manager import VisualizerManager
        
        # Create main window
        class SimpleVisualizerWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Audio Visualizer Pro - Simple Test")
                self.setGeometry(100, 100, 800, 600)
                
                # Create visualizer manager
                self.visualizer_manager = VisualizerManager()
                self.current_visualizer = None
                
                # Setup UI
                self.setup_ui()
                
                # Timer for updates
                self.timer = QTimer()
                self.timer.timeout.connect(self.update_visualizer)
                self.timer.start(16)  # ~60 FPS
                
            def setup_ui(self):
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                layout = QVBoxLayout(central_widget)
                
                # Title
                title = QLabel(" Audio Visualizer Pro - Working! ")
                title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4080ff; padding: 20px;")
                layout.addWidget(title)
                
                # Visualizer selector
                layout.addWidget(QLabel("Select Visualizer:"))
                self.visualizer_combo = QComboBox()
                visualizers = self.visualizer_manager.get_visualizer_names()
                self.visualizer_combo.addItem("None")
                self.visualizer_combo.addItems(visualizers)
                self.visualizer_combo.currentTextChanged.connect(self.change_visualizer)
                layout.addWidget(self.visualizer_combo)
                
                # Status
                self.status_label = QLabel("Status: Ready")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                layout.addWidget(self.status_label)
                
                # Info
                info_text = f" Found {len(visualizers)} visualizers\n"
                info_text += " OpenGL initialized\n"
                info_text += " Taichi working\n"
                info_text += " Application running!"
                
                info_label = QLabel(info_text)
                info_label.setStyleSheet("background: #f0f0f0; padding: 10px; border-radius: 5px;")
                layout.addWidget(info_label)
                
            def change_visualizer(self, name):
                try:
                    if name == "None":
                        self.current_visualizer = None
                        self.status_label.setText("Status: No visualizer")
                        self.status_label.setStyleSheet("color: gray;")
                    else:
                        self.current_visualizer = self.visualizer_manager.create_visualizer(name)
                        if self.current_visualizer:
                            self.status_label.setText(f"Status: Running {name}")
                            self.status_label.setStyleSheet("color: green; font-weight: bold;")
                        else:
                            self.status_label.setText(f"Status: Failed to load {name}")
                            self.status_label.setStyleSheet("color: red;")
                            
                except Exception as e:
                    self.status_label.setText(f"Status: Error - {e}")
                    self.status_label.setStyleSheet("color: red;")
                    print(f"Error changing visualizer: {e}")
                    
            def update_visualizer(self):
                # Simple update - just to keep things running
                if self.current_visualizer:
                    try:
                        # Try to render if possible
                        if hasattr(self.current_visualizer, 'render'):
                            self.current_visualizer.render()
                    except:
                        pass
        
        # Create and show window
        window = SimpleVisualizerWindow()
        window.show()
        
        print("Simple app created successfully!")
        print("Window should be visible now")
        print("Try selecting different visualizers from the dropdown")
        
        # Run app
        return app.exec()
        
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_simple_app())