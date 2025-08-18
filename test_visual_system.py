#!/usr/bin/env python3
"""
Test script to verify the visual system is working
Run this to check if visualizers are loading and rendering correctly
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

try:  # OpenGL is optional after migration to Taichi
    from OpenGL.GL import *  # type: ignore
except Exception:  # pragma: no cover - skip tests if OpenGL unavailable
    import pytest

    pytest.skip("PyOpenGL not available", allow_module_level=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_visualizer_loading():
    """Test if visualizers can be loaded"""
    logging.info("=" * 60)
    logging.info("TESTING VISUALIZER LOADING")
    logging.info("=" * 60)
    
    try:
        from visuals.visualizer_manager import VisualizerManager
        
        vm = VisualizerManager()
        names = vm.get_visualizer_names()
        
        logging.info(f"✅ Found {len(names)} visualizers:")
        for name in names:
            logging.info(f"   • {name}")
            
        # Try to create an instance of each
        for name in names:
            try:
                vis_class = vm.get_visualizer_class(name)
                if vis_class:
                    instance = vis_class()
                    logging.info(f"   ✅ Created instance of {name}")
                    
                    # Check if it has required methods
                    has_init = hasattr(instance, 'initializeGL')
                    has_paint = hasattr(instance, 'paintGL')
                    has_resize = hasattr(instance, 'resizeGL')
                    
                    logging.info(f"      Methods: init={has_init}, paint={has_paint}, resize={has_resize}")
                    
            except Exception as e:
                logging.error(f"   ❌ Failed to create {name}: {e}")
                
        return len(names) > 0
        
    except Exception as e:
        logging.error(f"❌ Failed to test visualizer loading: {e}")
        import traceback
        traceback.print_exc()
        return False

class TestGLWidget(QOpenGLWidget):
    """Simple GL widget to test rendering"""
    
    def __init__(self):
        super().__init__()
        self.visualizer = None
        self.frame_count = 0
        
    def set_visualizer(self, visualizer):
        """Set the visualizer to test"""
        self.visualizer = visualizer
        if self.visualizer and self.isValid():
            self.makeCurrent()
            if hasattr(self.visualizer, 'initializeGL'):
                self.visualizer.initializeGL()
            if hasattr(self.visualizer, 'resizeGL'):
                self.visualizer.resizeGL(self.width(), self.height())
            self.doneCurrent()
            
    def initializeGL(self):
        logging.info("TestGLWidget.initializeGL")
        glClearColor(0.1, 0.1, 0.2, 1.0)
        
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if self.visualizer and hasattr(self.visualizer, 'paintGL'):
            try:
                self.visualizer.paintGL()
                
                self.frame_count += 1
                if self.frame_count % 60 == 0:
                    logging.info(f"   Rendered {self.frame_count} frames")
                    
            except Exception as e:
                logging.error(f"Error painting visualizer: {e}")
                # Draw error pattern
                glClearColor(0.5, 0.0, 0.0, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
        else:
            # Draw test pattern
            glClearColor(0.0, 0.0, 0.5, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        if self.visualizer and hasattr(self.visualizer, 'resizeGL'):
            self.visualizer.resizeGL(w, h)

class TestWindow(QMainWindow):
    """Test window for visualizers"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizer Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Info label
        self.info_label = QLabel("Testing Visualizers...")
        layout.addWidget(self.info_label)
        
        # GL widget
        self.gl_widget = TestGLWidget()
        layout.addWidget(self.gl_widget)
        
        # Test button
        self.test_button = QPushButton("Run Tests")
        self.test_button.clicked.connect(self.run_tests)
        layout.addWidget(self.test_button)
        
        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.gl_widget.update)
        self.timer.start(16)  # 60 FPS
        
        # Auto-run tests
        QTimer.singleShot(100, self.run_tests)
        
    def run_tests(self):
        """Run visualizer tests"""
        logging.info("\n" + "=" * 60)
        logging.info("RUNNING VISUALIZER TESTS")
        logging.info("=" * 60)
        
        try:
            from visuals.visualizer_manager import VisualizerManager
            
            vm = VisualizerManager()
            names = vm.get_visualizer_names()
            
            if not names:
                self.info_label.setText("❌ No visualizers found!")
                return
                
            # Test the first visualizer
            test_name = names[0]
            self.info_label.setText(f"Testing: {test_name}")
            
            vis_class = vm.get_visualizer_class(test_name)
            if vis_class:
                visualizer = vis_class()
                self.gl_widget.set_visualizer(visualizer)
                logging.info(f"✅ Set visualizer: {test_name}")
                
                # Cycle through visualizers
                self.cycle_visualizers(vm, names)
            else:
                self.info_label.setText(f"❌ Failed to get {test_name}")
                
        except Exception as e:
            logging.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            self.info_label.setText(f"❌ Error: {e}")
            
    def cycle_visualizers(self, vm, names):
        """Cycle through all visualizers"""
        self.current_index = 0
        self.vm = vm
        self.names = names
        
        def next_visualizer():
            if self.current_index >= len(self.names):
                self.current_index = 0
                
            name = self.names[self.current_index]
            self.info_label.setText(f"Testing: {name} ({self.current_index + 1}/{len(self.names)})")
            
            try:
                vis_class = self.vm.get_visualizer_class(name)
                if vis_class:
                    visualizer = vis_class()
                    self.gl_widget.set_visualizer(visualizer)
                    logging.info(f"✅ Switched to: {name}")
            except Exception as e:
                logging.error(f"❌ Failed to switch to {name}: {e}")
                
            self.current_index += 1
            
        # Switch every 3 seconds
        self.switch_timer = QTimer()
        self.switch_timer.timeout.connect(next_visualizer)
        self.switch_timer.start(3000)
        
        # Start with first one
        next_visualizer()

def main():
    """Main test function"""
    logging.info("Starting Visualizer Test System")
    
    # Test loading first
    if not test_visualizer_loading():
        logging.error("❌ Visualizer loading test failed!")
        return 1
        
    # Setup OpenGL format
    format = QSurfaceFormat()
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    format.setDepthBufferSize(24)
    format.setSamples(4)
    QSurfaceFormat.setDefaultFormat(format)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    # Run
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())