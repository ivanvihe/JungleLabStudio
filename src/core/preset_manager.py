import json
import os
import shutil
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Optional, Any

class PresetManager:
    def __init__(self, base_dir: str = "presets"):
        self.base_dir = Path(base_dir)
        self.presets_dir = self.base_dir  # Alias for compatibility
        self.media_dir = self.base_dir / "media"
        self.templates_dir = self.base_dir / "templates"
        self.registry_path = self.base_dir / "library.json"
        self.presets = {}
        self._init_dirs()
        self.load_library()
        self.scan_templates()

    def _init_dirs(self):
        self.base_dir.mkdir(exist_ok=True)
        self.media_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)

    def load_library(self):
        if self.registry_path.exists():
            try:
                self.presets = json.loads(self.registry_path.read_text())
            except Exception as e:
                print(f"Error loading library: {e}")
                self.presets = {}
        else:
            self.presets = {}

    def scan_templates(self):
        """Auto-register YAML templates from templates directory"""
        # Scan for .yaml files
        for f in self.templates_dir.glob("*.yaml"):
            name = f.stem
            # Always update the path in case file was moved
            self.presets[name] = {
                "name": name,
                "path": str(f),
                "kind": "graph",
                "tags": ["generative"]
            }

        # Also scan for .yml files
        for f in self.templates_dir.glob("*.yml"):
            name = f.stem
            self.presets[name] = {
                "name": name,
                "path": str(f),
                "kind": "graph",
                "tags": ["generative"]
            }

        self.save_library()
        print(f"PresetManager: Scanned templates, found {len([p for p in self.presets.values() if p.get('kind') == 'graph'])} graph presets")

    def save_library(self):
        self.registry_path.write_text(json.dumps(self.presets, indent=2))

    def create_media_preset(self, name: str, source_path: str) -> bool:
        try:
            # 1. Create media dir
            preset_media_dir = self.media_dir / name
            preset_media_dir.mkdir(exist_ok=True)
            
            # 2. Copy file
            src = Path(source_path)
            dst = preset_media_dir / src.name
            shutil.copy2(src, dst)
            
            # 3. Create .preset file
            preset_data = {
                "name": name,
                "kind": "media",
                "media_file": src.name,
                "actions": ["trigger_slice", "trigger_transform", "trigger_rays", "trigger_inter"]
            }
            
            preset_path = self.base_dir / f"{name}.preset"
            preset_path.write_text(json.dumps(preset_data, indent=2))
            
            # 4. Update Index
            self.presets[name] = {
                "path": str(preset_path),
                "kind": "media"
            }
            self.save_library()
            return True
        except Exception as e:
            print(f"Error creating media preset: {e}")
            return False

    def load_preset_logic(self, name: str) -> Optional[Any]:
        if name not in self.presets:
            return None
            
        info = self.presets[name]
        path = Path(info["path"])
        
        # Handle Graph Presets (.yaml)
        if info.get("kind") == "graph" or path.suffix == ".yaml":
            return {
                "class": "GraphPreset",
                "file_path": str(path)
            }
        
        try:
            data = json.loads(path.read_text())
            
            if data["kind"] == "media":
                # Return config to instantiate MediaPreset
                media_path = self.media_dir / name / data["media_file"]
                return {
                    "class": "MediaPreset",
                    "file_path": str(media_path)
                }
            
            elif data["kind"] == "code":
                # Execute code and return class
                spec = importlib.util.spec_from_loader(f"dynamic_preset_{name}", loader=None)
                module = importlib.util.module_from_spec(spec)
                exec(data["code"], module.__dict__)
                cls = getattr(module, data["class_name"])
                return {"class": cls}
                
        except Exception as e:
            print(f"Error loading preset logic {name}: {e}")
            return None

    def migrate_builtin(self, name: str, cls_obj, code_file_path: str):
        try:
            code = Path(code_file_path).read_text()
            data = {
                "name": name,
                "kind": "code",
                "class_name": cls_obj.__name__,
                "code": code
            }
            preset_path = self.base_dir / f"{name}.preset"
            preset_path.write_text(json.dumps(data, indent=2))
            
            self.presets[name] = {
                "path": str(preset_path),
                "kind": "code"
            }
            self.save_library()
        except Exception as e:
            print(f"Migration failed for {name}: {e}")