"""
Shadertoy Compatibility Demo
Demonstrates how to use the Shadertoy system in JungleLabStudio
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shadertoy.converter import ShadertoyConverter


def demo_converter():
    """Demonstrate the Shadertoy converter"""
    print("="*70)
    print("SHADERTOY CONVERTER DEMO")
    print("="*70)
    print()

    # Create converter
    converter = ShadertoyConverter()

    # Example Shadertoy shader (classic animated circle)
    shadertoy_code = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalize coordinates
    vec2 uv = fragCoord / iResolution.xy;
    uv = uv * 2.0 - 1.0;
    uv.x *= iResolution.x / iResolution.y;

    // Animated circle
    vec2 circlePos = vec2(sin(iTime), cos(iTime)) * 0.3;
    float d = length(uv - circlePos);

    // Color based on distance and time
    vec3 col = vec3(
        0.5 + 0.5 * sin(iTime),
        0.5 + 0.5 * cos(iTime * 0.7),
        0.5 + 0.5 * sin(iTime * 1.3)
    );

    // Create circle with smooth edge
    float circle = smoothstep(0.2, 0.18, d);
    col *= circle;

    // Add glow
    col += vec3(0.1, 0.2, 0.3) / (d * 10.0);

    fragColor = vec4(col, 1.0);
}
"""

    print("INPUT: Shadertoy code")
    print("-" * 70)
    print(shadertoy_code)
    print()

    # Convert
    print("CONVERTING...")
    glsl_code = converter.convert(shadertoy_code)

    print("\nOUTPUT: JungleLabStudio GLSL")
    print("-" * 70)
    # Show first 30 lines
    lines = glsl_code.split('\n')
    for i, line in enumerate(lines[:30]):
        print(f"{i+1:3d}: {line}")
    print("...")
    print(f"\nTotal lines: {len(lines)}")
    print()

    # Detect dependencies
    print("DEPENDENCIES DETECTED:")
    print("-" * 70)
    deps = converter.detect_dependencies(shadertoy_code)
    print(f"  Channels used: {deps['channels']}")
    print(f"  Uses mouse: {deps['uses_mouse']}")
    print(f"  Uses time: {deps['uses_time']}")
    print(f"  Uses frame counter: {deps['uses_frame']}")
    print(f"  Uses date: {deps['uses_date']}")
    print(f"  Uses audio: {deps['uses_audio']}")
    print()

    # Validate
    print("VALIDATION:")
    print("-" * 70)
    validation = converter.validate_shader(shadertoy_code)
    print(f"  Valid: {validation['valid']}")
    if validation['errors']:
        print(f"  Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"  Warnings: {validation['warnings']}")
    else:
        print("  No warnings")
    print()


def demo_yaml_preset():
    """Show how to use in YAML preset"""
    print("="*70)
    print("YAML PRESET EXAMPLE")
    print("="*70)
    print()

    yaml_example = """preset:
  name: "My Shadertoy Import"
  description: "Shader imported from Shadertoy"
  author: "Your Name"
  source: "shadertoy"
  tags: ["shadertoy", "animated"]

  nodes:
    # Shadertoy shader node
    - id: my_shader
      type: shadertoy
      position: [100, 100]
      params:
        # Paste Shadertoy code here
        shadertoy_code: |
          void mainImage(out vec4 fragColor, in vec2 fragCoord) {
              vec2 uv = fragCoord / iResolution.xy;
              vec3 col = vec3(uv, 0.5 + 0.5 * sin(iTime));
              fragColor = vec4(col, 1.0);
          }

    # Output
    - id: output
      type: output
      position: [300, 100]
      inputs:
        input0: my_shader
"""

    print(yaml_example)
    print()


def demo_python_usage():
    """Show how to use from Python code"""
    print("="*70)
    print("PYTHON USAGE EXAMPLE")
    print("="*70)
    print()

    python_example = """
from shadertoy.converter import ShadertoyConverter
from nodes.shadertoy import ShadertoyNode

# 1. Convert Shadertoy code
converter = ShadertoyConverter()
shadertoy_code = '''
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    fragColor = vec4(uv, 0.5, 1.0);
}
'''

# Validate before converting
validation = converter.validate_shader(shadertoy_code)
if not validation['valid']:
    print("Invalid shader:", validation['errors'])
else:
    # Convert to GLSL
    glsl_code = converter.convert(shadertoy_code)

    # 2. Create node (requires ModernGL context)
    # node = ShadertoyNode(ctx, "shader_001", (1920, 1080))
    # node.set_shadertoy_code(shadertoy_code)
    # node.render()  # Render the shader

# 3. Check dependencies
deps = converter.detect_dependencies(shadertoy_code)
print("Dependencies:", deps)
"""

    print(python_example)
    print()


def show_features():
    """Show implemented features"""
    print("="*70)
    print("IMPLEMENTED SHADERTOY FEATURES")
    print("="*70)
    print()

    features = {
        "Uniforms": {
            "iResolution (vec3)": "✅ Viewport resolution + aspect ratio",
            "iTime (float)": "✅ Shader playback time",
            "iTimeDelta (float)": "✅ Frame delta time",
            "iFrame (int)": "✅ Frame counter",
            "iMouse (vec4)": "✅ Mouse position and click",
            "iDate (vec4)": "✅ Date and time info",
            "iSampleRate (float)": "✅ Audio sample rate (44100)",
            "iChannel0-3": "⚙️  Structure ready (Fase 2)",
            "iChannelTime[4]": "✅ Channel playback time",
            "iChannelResolution[4]": "✅ Channel resolution",
        },
        "Features": {
            "mainImage() conversion": "✅ Automatic wrapping",
            "fragCoord in pixels": "✅ Correct coordinate system",
            "Aspect ratio": "✅ Automatic correction",
            "Code validation": "✅ Error detection",
            "Dependency detection": "✅ Auto-detect features used",
            "Metadata extraction": "✅ From comments",
        },
        "Compatibility": {
            "Simple shaders": "✅ Full support",
            "Raymarching": "✅ Full support",
            "Mathematical functions": "✅ Full support",
            "Procedural generation": "✅ Full support",
        }
    }

    for category, items in features.items():
        print(f"\n{category}:")
        print("-" * 70)
        for name, status in items.items():
            print(f"  {status}  {name}")

    print()


def main():
    """Run all demos"""
    print()
    print("🎨 JungleLabStudio - Shadertoy Compatibility System")
    print()

    # Show features
    show_features()

    input("Press ENTER to see converter demo...")
    demo_converter()

    input("Press ENTER to see YAML preset example...")
    demo_yaml_preset()

    input("Press ENTER to see Python usage example...")
    demo_python_usage()

    print("="*70)
    print("✅ DEMO COMPLETE!")
    print("="*70)
    print()
    print("Next steps:")
    print("1. Try the example presets in community_presets/shadertoy/")
    print("2. Paste your own Shadertoy code into a preset")
    print("3. Run: python tests/test_shadertoy_basic.py")
    print()
    print("For full documentation, see:")
    print("  - SHADERTOY_COMPATIBILITY_PLAN.md")
    print("  - SHADERTOY_PHASE1_COMPLETE.md")
    print("  - src/shadertoy/README.md")
    print()


if __name__ == "__main__":
    main()
