import os
import importlib
import inspect
import logging
from visuals.base_visualizer import BaseVisualizer

class VisualizerManager:
    def __init__(self, visual_directory="visuals"):
        self.visualizers = {}
        self.load_visualizers(visual_directory)

    def load_visualizers(self, visual_directory):
        logging.debug(f"Scanning directory: {visual_directory}")
        for filename in os.listdir(visual_directory):
            if filename.endswith(".py") and not filename.startswith("__"):
                logging.debug(f"Found file: {filename}")
                module_name = f"{visual_directory}.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseVisualizer) and obj is not BaseVisualizer:
                            if hasattr(obj, 'visual_name'):
                                readable_name = obj.visual_name
                            else:
                                readable_name = " ".join(word.capitalize() for word in obj.__name__.replace("Visualizer", "").split("_"))
                            self.visualizers[readable_name.strip()] = obj
                            logging.debug(f"Loaded visualizer: {readable_name}")
                except Exception as e:
                    logging.error(f"Error loading visualizer from {filename}: {e}")

    def get_visualizer_names(self):
        logging.debug(f"Returning visualizer names: {list(self.visualizers.keys())}")
        return list(self.visualizers.keys())

    def get_visualizer_class(self, name):
        return self.visualizers.get(name)
