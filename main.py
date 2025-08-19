#!/usr/bin/env python3
"""
Enhanced Audio Visualizer Pro - Main Entry Point

This is the improved version with:
- Modern OpenGL compatibility
- Enhanced visual effects
- Better error handling
- Performance optimizations
- Modern UI design
"""

import sys
import os
import logging
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our enhanced application
try:
    from ui.main_application import MainApplication
    from opengl_fixes import init_opengl_debug, get_opengl_info, test_opengl_functionality
    from visuals.render_backend import get_backend_info
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install PySide6 numpy taichi pyopengl")
    sys.exit(1)


def setup_logging():
    """Set up comprehensive logging."""
    # Create logs directory
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File handler with rotation
    log_file = logs_dir / "audiovisualizer.log"
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Console handler  
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s - %(message)s'
    ))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress verbose third-party loggers
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    return log_file


def check_dependencies():
    """Check for required dependencies and system compatibility."""
    required_modules = {
        'PySide6': 'PySide6',
        'numpy': 'numpy', 
        'taichi': 'taichi'
    }
    
    optional_modules = {
        'OpenGL': 'PyOpenGL',
        'moderngl': 'moderngl'
    }
    
    missing_required = []
    missing_optional = []
    
    # Check required modules
    for module_name, pip_name in required_modules.items():
        try:
            __import__(module_name)
            logging.info(f"✅ {module_name} available")
        except ImportError:
            missing_required.append(pip_name)
            logging.error(f"❌ {module_name} not found")
    
    # Check optional modules
    for module_name, pip_name in optional_modules.items():
        try:
            __import__(module_name)
            logging.info(f"✅ {module_name} available (optional)")
        except ImportError:
            missing_optional.append(pip_name)
            logging.warning(f"⚠️ {module_name} not found (optional)")
    
    if missing_required:
        print("❌ Missing required dependencies:")
        print(f"   pip install {' '.join(missing_required)}")
        return False
        
    if missing_optional:
        print("ℹ️ Optional dependencies not found (some features may be limited):")
        print(f"   pip install {' '.join(missing_optional)}")
    
    return True


def check_system_info():
    """Check and log system information."""
    import platform
    
    logging.info("📋 System Information:")
    logging.info(f"   OS: {platform.system()} {platform.release()}")
    logging.info(f"   Python: {platform.python_version()}")
    logging.info(f"   Architecture: {platform.machine()}")
    
    # Check available memory
    try:
        import psutil
        memory = psutil.virtual_memory()
        logging.info(f"   RAM: {memory.total // (1024**3)} GB ({memory.percent}% used)")
    except ImportError:
        logging.info("   RAM: Unknown (psutil not available)")


def test_graphics_backends():
    """Test available graphics backends."""
    logging.info("🎮 Testing Graphics Backends:")
    
    # Test OpenGL
    try:
        opengl_info = get_opengl_info()
        if opengl_info.get('available'):
            logging.info(f"   OpenGL: {opengl_info['version']} - {opengl_info['renderer']}")
            logging.info(f"   Core Profile: {opengl_info['core_profile']}")
            
            # Test functionality
            func_tests = test_opengl_functionality()
            for test, result in func_tests.items():
                if result is True:
                    logging.info(f"     ✅ {test}")
                elif result is False:
                    logging.warning(f"     ❌ {test}")
                else:
                    logging.info(f"     ➖ {test} (not supported)")
        else:
            logging.warning("   OpenGL: Not available")
    except Exception as e:
        logging.error(f"   OpenGL test failed: {e}")
    
    # Test render backends
    try:
        backend_info = get_backend_info()
        logging.info(f"   Available backends: {backend_info['available_backends']}")
        logging.info(f"   Recommended: {backend_info['recommended_backend']}")
        
        for backend, test_result in backend_info['backend_tests'].items():
            status = "✅" if test_result['success'] else "❌"
            logging.info(f"     {status} {backend}: {test_result['message']}")
            
    except Exception as e:
        logging.error(f"   Backend test failed: {e}")


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.critical("💥 Uncaught exception occurred!", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Try to show error dialog if possible
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance()
        if app:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Critical Error")
            msg.setText(f"An unexpected error occurred:\n\n{exc_value}")
            msg.setDetailedText(
                "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            )
            msg.exec()
    except:
        pass  # Fallback if GUI not available


def main():
    """Enhanced main entry point."""
    print("🚀 Starting Audio Visualizer Pro...")
    print("=" * 50)
    
    # Set up logging first
    log_file = setup_logging()
    logging.info("🚀 Audio Visualizer Pro starting...")
    logging.info(f"📝 Log file: {log_file}")
    
    # Set global exception handler
    sys.excepthook = handle_exception
    
    try:
        # System checks
        logging.info("🔍 Performing system checks...")
        check_system_info()
        
        if not check_dependencies():
            return 1
            
        # Graphics backend tests
        test_graphics_backends()
        
        # Initialize OpenGL debugging
        logging.info("🎮 Initializing graphics...")
        init_opengl_debug()
        
        # Create and run application
        logging.info("🏗️ Creating application...")
        app = MainApplication()
        
        logging.info("▶️ Starting application...")
        exit_code = app.run()
        
        logging.info(f"🏁 Application finished with exit code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        logging.info("⏹️ Application interrupted by user")
        return 0
        
    except Exception as e:
        logging.critical(f"💥 Critical error in main: {e}", exc_info=True)
        print(f"\n❌ Critical error: {e}")
        print(f"📝 Check log file for details: {log_file}")
        return 1


if __name__ == "__main__":
    # Ensure we're running with Python 3.8+
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    # Check if we're in the right directory
    if not (project_root / "visuals").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run the application
    sys.exit(main())