"""
ShadertoyImporter - Import shaders from Shadertoy.com or raw code

This module provides tools to import Shadertoy shaders and convert them
to JungleLabStudio YAML presets.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .converter import ShadertoyConverter


class ShadertoyImporter:
    """
    Import Shadertoy shaders and generate YAML presets

    Supports:
    - Import from raw Shadertoy code
    - Import from Shadertoy.com URL (using API)
    - Automatic dependency detection
    - Multi-pass shader support (BufferA, BufferB, etc.)
    - Texture input generation
    """

    def __init__(self):
        self.converter = ShadertoyConverter()

    def import_from_code(
        self,
        code: str,
        name: str = "Shadertoy Import",
        author: str = "Unknown",
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Import shader from raw Shadertoy code

        Args:
            code: Shadertoy shader code (mainImage function)
            name: Name for the preset
            author: Author name
            description: Description text
            tags: List of tags

        Returns:
            Complete preset dictionary ready for YAML export

        Example:
            >>> importer = ShadertoyImporter()
            >>> preset = importer.import_from_code(
            ...     shadertoy_code,
            ...     name="Cool Shader",
            ...     author="John Doe"
            ... )
            >>> # Save to file
            >>> with open('preset.yaml', 'w') as f:
            ...     yaml.dump(preset, f)
        """
        # Validate shader
        validation = self.converter.validate_shader(code)
        if not validation['valid']:
            raise ValueError(f"Invalid shader: {validation['errors']}")

        # Detect dependencies
        deps = self.converter.detect_dependencies(code)

        # Extract metadata from code comments if available
        code_metadata = self.converter.extract_shader_metadata(code)
        if code_metadata['author']:
            author = code_metadata['author']
        if code_metadata['description']:
            description = code_metadata['description']

        # Build tags
        if tags is None:
            tags = ['shadertoy', 'imported']
        else:
            tags = ['shadertoy'] + tags

        # Add dependency tags
        if deps['uses_mouse']:
            tags.append('interactive')
        if deps['uses_audio']:
            tags.append('audio-reactive')
        if deps['channels']:
            tags.append('textures')

        # Create preset structure
        preset = {
            'preset': {
                'name': name,
                'description': description or f"Imported from Shadertoy",
                'author': author,
                'version': '1.0.0',
                'source': 'shadertoy',
                'imported_at': datetime.now().isoformat(),
                'tags': tags,
                'settings': {
                    'bpm': 120.0,
                    'audio_reactive': deps['uses_audio'],
                    'midi_enabled': False
                },
                'nodes': []
            }
        }

        # Create texture input nodes if needed
        for channel_idx in deps['channels']:
            texture_node = {
                'id': f'texture_ch{channel_idx}',
                'type': 'generator.checkerboard',  # Placeholder texture
                'position': [100, 100 + channel_idx * 150],
                'params': {
                    'rows': 8.0,
                    'cols': 8.0,
                    'color1': [0.2, 0.2, 0.2],
                    'color2': [0.8, 0.8, 0.8]
                }
            }
            preset['preset']['nodes'].append(texture_node)

        # Create main Shadertoy node
        main_node = {
            'id': 'shadertoy_main',
            'type': 'shadertoy',
            'position': [400, 200],
            'params': {
                'shadertoy_code': code
            }
        }

        # Connect texture inputs
        if deps['channels']:
            main_node['inputs'] = {}
            for channel_idx in deps['channels']:
                main_node['inputs'][f'channel{channel_idx}'] = f'texture_ch{channel_idx}'

        preset['preset']['nodes'].append(main_node)

        # Create output node
        output_node = {
            'id': 'output',
            'type': 'output',
            'position': [700, 200],
            'inputs': {
                'input0': 'shadertoy_main'
            }
        }
        preset['preset']['nodes'].append(output_node)

        return preset

    def import_from_url(self, url: str) -> Dict[str, Any]:
        """
        Import shader from Shadertoy.com URL

        Note: This requires Shadertoy API access (API key needed)
        For now, this is a placeholder that extracts the shader ID

        Args:
            url: Shadertoy URL (e.g., https://www.shadertoy.com/view/XsXXDN)

        Returns:
            Preset dictionary

        Raises:
            NotImplementedError: API integration not yet implemented
        """
        # Extract shader ID from URL
        shader_id = self._extract_shader_id(url)

        if not shader_id:
            raise ValueError(f"Invalid Shadertoy URL: {url}")

        # TODO: Implement API fetch
        # For now, raise error with instructions
        raise NotImplementedError(
            f"Shadertoy API import not yet implemented.\n"
            f"Shader ID: {shader_id}\n\n"
            f"To import this shader:\n"
            f"1. Go to {url}\n"
            f"2. Copy the shader code\n"
            f"3. Use importer.import_from_code() instead\n\n"
            f"API integration coming in Phase 5!"
        )

    def import_multipass(
        self,
        shaders: Dict[str, str],
        name: str = "Multi-pass Shader",
        author: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        Import multi-pass shader (BufferA, BufferB, Image, etc.)

        Args:
            shaders: Dictionary mapping pass names to shader code
                     e.g., {'Image': code1, 'BufferA': code2, 'BufferB': code3}
            name: Preset name
            author: Author name

        Returns:
            Preset dictionary with connected buffer nodes

        Example:
            >>> shaders = {
            ...     'Image': image_code,
            ...     'BufferA': buffer_a_code,
            ...     'BufferB': buffer_b_code
            ... }
            >>> preset = importer.import_multipass(shaders, "Complex Shader")
        """
        preset = {
            'preset': {
                'name': name,
                'description': f"Multi-pass shader with {len(shaders)} passes",
                'author': author,
                'version': '1.0.0',
                'source': 'shadertoy',
                'tags': ['shadertoy', 'multi-pass', 'imported'],
                'settings': {
                    'bpm': 120.0,
                    'audio_reactive': False,
                    'midi_enabled': False
                },
                'nodes': []
            }
        }

        # Create nodes for each pass
        node_ids = {}
        y_offset = 100

        for pass_name, code in shaders.items():
            # Determine node type
            if pass_name.lower().startswith('buffer'):
                node_type = 'shadertoy.buffer'
                node_id = f'buffer_{pass_name.lower()}'
            else:
                node_type = 'shadertoy'
                node_id = 'shadertoy_main'

            # Create node
            node = {
                'id': node_id,
                'type': node_type,
                'position': [300, y_offset],
                'params': {
                    'shadertoy_code': code
                }
            }

            node_ids[pass_name] = node_id
            preset['preset']['nodes'].append(node)
            y_offset += 150

        # TODO: Auto-connect buffers based on dependencies
        # For now, user needs to connect manually

        # Add output
        output_node = {
            'id': 'output',
            'type': 'output',
            'position': [600, 200],
            'inputs': {
                'input0': node_ids.get('Image', 'shadertoy_main')
            }
        }
        preset['preset']['nodes'].append(output_node)

        return preset

    def save_preset(
        self,
        preset: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Save preset to YAML file

        Args:
            preset: Preset dictionary
            output_path: Optional custom output path

        Returns:
            Path where preset was saved
        """
        if output_path is None:
            # Generate filename from preset name
            preset_name = preset['preset']['name']
            safe_name = re.sub(r'[^\w\s-]', '', preset_name).strip().replace(' ', '_')
            safe_name = safe_name.lower()

            output_dir = Path('community_presets/shadertoy')
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f'{safe_name}.yaml'

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as YAML
        with open(output_path, 'w') as f:
            yaml.dump(preset, f, default_flow_style=False, sort_keys=False)

        return output_path

    def _extract_shader_id(self, url: str) -> Optional[str]:
        """
        Extract shader ID from Shadertoy URL

        Args:
            url: Shadertoy URL

        Returns:
            Shader ID or None if invalid
        """
        # Pattern: https://www.shadertoy.com/view/XXXXXX
        pattern = r'shadertoy\.com/view/([a-zA-Z0-9]+)'
        match = re.search(pattern, url)

        if match:
            return match.group(1)

        return None

    def create_template_preset(
        self,
        name: str = "New Shadertoy Shader",
        author: str = "Your Name"
    ) -> Dict[str, Any]:
        """
        Create empty template preset for manual shader entry

        Args:
            name: Preset name
            author: Author name

        Returns:
            Template preset dictionary
        """
        template_code = """void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalize coordinates
    vec2 uv = fragCoord / iResolution.xy;

    // Your shader code here
    vec3 col = vec3(uv, 0.5 + 0.5 * sin(iTime));

    // Output
    fragColor = vec4(col, 1.0);
}"""

        return self.import_from_code(
            template_code,
            name=name,
            author=author,
            description="Template shader - edit the shadertoy_code parameter"
        )


# Convenience functions

def quick_import(
    code: str,
    name: str = "Shadertoy Import",
    save: bool = True
) -> Dict[str, Any]:
    """
    Quick import from Shadertoy code

    Args:
        code: Shadertoy shader code
        name: Preset name
        save: Whether to save to file

    Returns:
        Preset dictionary

    Example:
        >>> preset = quick_import(shadertoy_code, "Cool Shader")
    """
    importer = ShadertoyImporter()
    preset = importer.import_from_code(code, name=name)

    if save:
        path = importer.save_preset(preset)
        print(f"Preset saved to: {path}")

    return preset


def create_template(name: str = "New Shader") -> Path:
    """
    Create empty template preset

    Args:
        name: Preset name

    Returns:
        Path to saved preset

    Example:
        >>> path = create_template("My Shader")
        >>> print(f"Edit this file: {path}")
    """
    importer = ShadertoyImporter()
    preset = importer.create_template_preset(name=name)
    path = importer.save_preset(preset)
    return path
