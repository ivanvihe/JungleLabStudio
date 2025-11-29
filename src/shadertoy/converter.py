"""
ShadertoyConverter - Converts Shadertoy code to JungleLabStudio format

This module provides automatic conversion of Shadertoy shaders to be compatible
with JungleLabStudio's rendering system.
"""

import re
from typing import Dict, List


class ShadertoyConverter:
    """
    Converts Shadertoy shader code to JungleLabStudio-compatible GLSL

    Features:
    - Wraps mainImage() function with proper vertex/fragment shader structure
    - Declares all Shadertoy uniforms
    - Converts fragCoord coordinate system
    - Detects shader dependencies (channels, mouse, audio, etc.)
    """

    # GLSL wrapper template for Shadertoy shaders
    WRAPPER_TEMPLATE = """#version 330

// ==================== VERTEX SHADER ====================
#ifdef VERTEX_SHADER
in vec2 in_pos;
in vec2 in_uv;
out vec2 v_fragCoord;

uniform vec3 iResolution;

void main() {
    // Convert normalized UV (0-1) to pixel coordinates (0-resolution)
    v_fragCoord = in_uv * iResolution.xy;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
#endif

// ==================== FRAGMENT SHADER ====================
#ifdef FRAGMENT_SHADER
in vec2 v_fragCoord;
out vec4 fragColor;

// Shadertoy standard uniforms
uniform vec3 iResolution;           // viewport resolution (in pixels)
uniform float iTime;                // shader playback time (in seconds)
uniform float iTimeDelta;           // render time (in seconds)
uniform int iFrame;                 // shader playback frame
uniform vec4 iMouse;                // mouse pixel coords (xy: current, zw: click)
uniform sampler2D iChannel0;        // input channel 0
uniform sampler2D iChannel1;        // input channel 1
uniform sampler2D iChannel2;        // input channel 2
uniform sampler2D iChannel3;        // input channel 3
uniform vec3 iChannelResolution[4]; // channel resolution (in pixels)
uniform float iChannelTime[4];      // channel playback time (in seconds)
uniform vec4 iDate;                 // (year, month, day, time in seconds)
uniform float iSampleRate;          // sound sample rate (44100)

// ==================== SHADERTOY CODE ====================
{SHADERTOY_CODE}

// ==================== WRAPPER ====================
void main() {
    mainImage(fragColor, v_fragCoord);
}
#endif
"""

    def convert(self, shadertoy_code: str) -> str:
        """
        Convert Shadertoy shader code to JungleLabStudio format

        Args:
            shadertoy_code: Raw Shadertoy shader code containing mainImage() function

        Returns:
            Complete GLSL code ready to compile with vertex and fragment shaders

        Example:
            >>> converter = ShadertoyConverter()
            >>> shadertoy_code = '''
            ... void mainImage(out vec4 fragColor, in vec2 fragCoord) {
            ...     vec2 uv = fragCoord / iResolution.xy;
            ...     fragColor = vec4(uv, 0.5 + 0.5 * sin(iTime), 1.0);
            ... }
            ... '''
            >>> glsl_code = converter.convert(shadertoy_code)
        """
        # Clean up the code (remove leading/trailing whitespace)
        shadertoy_code = shadertoy_code.strip()

        # Insert Shadertoy code into template
        wrapped_code = self.WRAPPER_TEMPLATE.replace(
            '{SHADERTOY_CODE}',
            shadertoy_code
        )

        return wrapped_code

    def detect_dependencies(self, code: str) -> Dict[str, any]:
        """
        Detect what features and inputs the shader uses

        Args:
            code: Shadertoy shader code

        Returns:
            Dictionary with detected dependencies:
            {
                'channels': [0, 1, 2, 3],  # List of used iChannel indices
                'uses_mouse': bool,         # Whether shader uses iMouse
                'uses_audio': bool,         # Whether shader uses iSampleRate
                'uses_time': bool,          # Whether shader uses iTime
                'uses_frame': bool,         # Whether shader uses iFrame
                'uses_date': bool,          # Whether shader uses iDate
                'buffer_count': int,        # Number of buffer passes needed
            }
        """
        deps = {
            'channels': [],
            'uses_mouse': False,
            'uses_audio': False,
            'uses_time': False,
            'uses_frame': False,
            'uses_date': False,
            'buffer_count': 0,
        }

        # Detect used channels (iChannel0-3)
        for i in range(4):
            if f'iChannel{i}' in code:
                deps['channels'].append(i)

        # Detect mouse usage
        if 'iMouse' in code:
            deps['uses_mouse'] = True

        # Detect audio usage
        if 'iSampleRate' in code:
            deps['uses_audio'] = True

        # Detect time usage
        if 'iTime' in code or 'iGlobalTime' in code:  # iGlobalTime is legacy name
            deps['uses_time'] = True

        # Detect frame counter usage
        if 'iFrame' in code:
            deps['uses_frame'] = True

        # Detect date usage
        if 'iDate' in code:
            deps['uses_date'] = True

        return deps

    def validate_shader(self, code: str) -> Dict[str, any]:
        """
        Validate Shadertoy shader code

        Args:
            code: Shadertoy shader code

        Returns:
            Validation result:
            {
                'valid': bool,
                'errors': [str],      # List of error messages
                'warnings': [str],    # List of warning messages
            }
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Check for proper mainImage signature
        mainimage_pattern = r'void\s+mainImage\s*\(\s*out\s+vec4\s+\w+\s*,\s*in\s+vec2\s+\w+\s*\)'
        if not re.search(mainimage_pattern, code):
            result['valid'] = False
            result['errors'].append(
                'Missing or invalid mainImage() function. '
                'Shadertoy shaders must have: '
                'void mainImage(out vec4 fragColor, in vec2 fragCoord)'
            )

        # Warn about potentially missing features
        if 'texture' in code.lower() and not any(f'iChannel{i}' in code for i in range(4)):
            result['warnings'].append(
                'Shader contains texture() calls but no iChannel uniforms detected. '
                'You may need to connect texture inputs.'
            )

        return result

    def extract_shader_metadata(self, code: str) -> Dict[str, any]:
        """
        Extract metadata from shader comments (if present)

        Some Shadertoy shaders include metadata in comments like:
        // Author: username
        // License: CC BY-NC-SA 3.0

        Args:
            code: Shadertoy shader code

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'author': None,
            'license': None,
            'description': None,
        }

        # Try to extract author
        author_match = re.search(r'//\s*[Aa]uthor\s*:\s*(.+)', code)
        if author_match:
            metadata['author'] = author_match.group(1).strip()

        # Try to extract license
        license_match = re.search(r'//\s*[Ll]icense\s*:\s*(.+)', code)
        if license_match:
            metadata['license'] = license_match.group(1).strip()

        # Try to extract description (first block comment)
        desc_match = re.search(r'/\*\s*(.+?)\s*\*/', code, re.DOTALL)
        if desc_match:
            metadata['description'] = desc_match.group(1).strip()

        return metadata


# Convenience function for quick conversion
def convert_shadertoy(code: str) -> str:
    """
    Quick conversion function

    Args:
        code: Shadertoy shader code

    Returns:
        Converted GLSL code
    """
    converter = ShadertoyConverter()
    return converter.convert(code)
