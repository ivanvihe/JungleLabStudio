# visuals/visualizer_manager.py
import logging
import importlib
import os
import sys
from pathlib import Path

class VisualizerManager:
    def __init__(self):
        self.visualizers = {}
        self.load_visualizers()

    def load_visualizers(self):
        """Load all visualizer modules from the visuals directory"""
        try:
            # Get the directory where this file is located
            current_dir = Path(__file__).parent
            presets_dir = current_dir / "presets"
            logging.info(f"🔍 Loading visualizers from: {presets_dir}")
            
            # List of visualizer modules to load (in order of preference)
            visualizer_modules = [
                'simple_test',        # Simple test visualizer (should always work)
                'intro_background',    # Intro background visualizer
                'intro_text_robotica', # Intro text overlay
                'wire_terrain',       # Wire terrain
                'abstract_lines',     # Abstract lines
                'geometric_particles',
                'evolutive_particles',
                'abstract_shapes',
                'mobius_band',
                'building_madness',
                'cosmic_flow',
                'fluid_particles',
                'vortex_particles',
                'kaleido_tunney',
                'science_analyzer',
            ]
            
            loaded_count = 0
            failed_modules = []
            
            for module_name in visualizer_modules:
                try:
                    # Check if file exists
                    module_file = presets_dir / f"{module_name}.py"
                    if not module_file.exists():
                        logging.debug(f"⚠️ Module file not found: {module_file}")
                        continue
                    
                    # Import the module
                    full_module_name = f"visuals.presets.{module_name}"
                    
                    # Force reload if already imported
                    if full_module_name in sys.modules:
                        module = importlib.reload(sys.modules[full_module_name])
                    else:
                        module = importlib.import_module(full_module_name)
                    
                    # Find the visualizer class in the module
                    visualizer_class = None
                    visualizer_name = None
                    
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        # Check if it's a class that inherits from BaseVisualizer
                        if (isinstance(attr, type) and 
                            hasattr(attr, 'visual_name') and 
                            attr_name != 'BaseVisualizer'):
                            
                            visualizer_class = attr
                            visualizer_name = attr.visual_name
                            break
                    
                    if visualizer_class and visualizer_name:
                        self.visualizers[visualizer_name] = visualizer_class
                        loaded_count += 1
                        logging.info(f"✅ Loaded visualizer: {visualizer_name} from {module_name}")
                    else:
                        logging.warning(f"⚠️ No visualizer class found in {module_name}")
                        failed_modules.append(module_name)
                        
                except ImportError as e:
                    logging.error(f"❌ Failed to import {module_name}: {e}")
                    failed_modules.append(module_name)
                except Exception as e:
                    logging.error(f"❌ Error loading {module_name}: {e}")
                    failed_modules.append(module_name)
            
            # Log summary
            logging.info(f"📊 Visualizer loading complete:")
            logging.info(f"   ✅ Successfully loaded: {loaded_count} visualizers")
            if failed_modules:
                logging.info(f"   ❌ Failed to load: {failed_modules}")
            
            # List all loaded visualizers
            if self.visualizers:
                logging.info(f"📋 Available visualizers:")
                for name in self.visualizers.keys():
                    logging.info(f"   • {name}")
            else:
                logging.error("❌ No visualizers loaded! Application may not work correctly.")
                
                # Try to create at least a fallback visualizer
                self._create_fallback_visualizer()
                
        except Exception as e:
            logging.error(f"❌ Critical error in load_visualizers: {e}")
            import traceback
            traceback.print_exc()
            
            # Create fallback
            self._create_fallback_visualizer()

    def _create_fallback_visualizer(self):
        """Create a minimal fallback visualizer"""
        try:
            logging.info("🛠️ Creating fallback visualizer...")
            
            from .base_visualizer import BaseVisualizer
            from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT
            import time
            import math
            
            class FallbackVisualizer(BaseVisualizer):
                visual_name = "Fallback"
                
                def __init__(self):
                    super().__init__()
                    self.start_time = time.time()
                
                def initializeGL(self):
                    glClearColor(0.0, 0.0, 0.0, 0.0)
                
                def paintGL(self):
                    t = time.time() - self.start_time
                    r = 0.5 + 0.5 * math.sin(t)
                    g = 0.5 + 0.5 * math.sin(t + 2.094)
                    b = 0.5 + 0.5 * math.sin(t + 4.189)
                    glClearColor(r * 0.3, g * 0.3, b * 0.3, 0.8)
                    glClear(GL_COLOR_BUFFER_BIT)
                
                def get_controls(self):
                    return {}
            
            self.visualizers["Fallback"] = FallbackVisualizer
            logging.info("✅ Fallback visualizer created")
            
        except Exception as e:
            logging.error(f"❌ Failed to create fallback visualizer: {e}")

    def get_visualizer_names(self):
        """Get list of available visualizer names"""
        names = list(self.visualizers.keys())
        logging.debug(f"📋 Available visualizers: {names}")
        return names

    def get_visualizer_class(self, name):
        """Get visualizer class by name"""
        visualizer_class = self.visualizers.get(name)
        if visualizer_class:
            logging.debug(f"✅ Found visualizer class for: {name}")
        else:
            logging.error(f"❌ Visualizer not found: {name}")
            # Return fallback if available
            if "Fallback" in self.visualizers:
                logging.warning(f"⚠️ Using fallback visualizer instead of {name}")
                return self.visualizers["Fallback"]
        return visualizer_class

    def create_visualizer(self, name):
        """Create an instance of a visualizer by name"""
        visualizer_class = self.get_visualizer_class(name)
        if visualizer_class:
            try:
                instance = visualizer_class()
                logging.info(f"✅ Created instance of {name}")
                return instance
            except Exception as e:
                logging.error(f"❌ Failed to create instance of {name}: {e}")
                import traceback
                traceback.print_exc()
        return None

    def reload_visualizers(self):
        """Reload all visualizers (useful for development)"""
        logging.info("🔄 Reloading all visualizers...")
        self.visualizers.clear()
        self.load_visualizers()