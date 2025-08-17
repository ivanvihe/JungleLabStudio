#!/usr/bin/env python3
"""
Test script to verify the fixed audio visualizer system
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_system():
    """Test the fixed system"""
    try:
        logging.info("=" * 60)
        logging.info("AUDIO VISUALIZER SYSTEM TEST")
        logging.info("=" * 60)
        
        # Import the main application
        from ui.main_application import MainApplication
        
        # Create and run the application
        app = MainApplication()
        
        # Show windows
        app.show_windows()
        
        # Set up a test sequence
        def test_sequence():
            logging.info("\n" + "=" * 60)
            logging.info("RUNNING TEST SEQUENCE")
            logging.info("=" * 60)
            
            # Test deck A
            logging.info("\n🎮 Testing Deck A...")
            app.mixer_window.safe_set_deck_visualizer('A', 'Intro Background')
            
            # Test deck B  
            logging.info("\n🎮 Testing Deck B...")
            visualizers = app.visualizer_manager.get_visualizer_names()
            if len(visualizers) > 1:
                app.mixer_window.safe_set_deck_visualizer('B', visualizers[1])
            else:
                app.mixer_window.safe_set_deck_visualizer('B', 'Intro Background')
            
            # Test crossfader
            logging.info("\n🎚️ Testing Crossfader...")
            for value in [0, 25, 50, 75, 100]:
                app.mixer_window.safe_set_mix_value(value)
                logging.info(f"  Mix value: {value}%")
            
            # Check deck states
            logging.info("\n📊 System Status:")
            current_vis = app.mixer_window.get_current_visualizers()
            logging.info(f"  Deck A: {current_vis.get('A', 'Unknown')}")
            logging.info(f"  Deck B: {current_vis.get('B', 'Unknown')}")
            logging.info(f"  Mix: {app.mixer_window.get_mix_value_percent()}%")
            
            # Check for OpenGL errors
            from OpenGL.GL import glGetError, GL_NO_ERROR
            error = glGetError()
            if error == GL_NO_ERROR:
                logging.info("  ✅ No OpenGL errors")
            else:
                logging.error(f"  ❌ OpenGL error: {error}")
            
            logging.info("\n" + "=" * 60)
            logging.info("TEST SEQUENCE COMPLETE")
            logging.info("=" * 60)
        
        # Run test sequence after a short delay
        QTimer.singleShot(2000, test_sequence)
        
        # Run the application
        return app.run()
        
    except Exception as e:
        logging.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_system())