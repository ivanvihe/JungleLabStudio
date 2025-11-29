"""
Basic tests for Shadertoy compatibility system - Phase 1
Tests the converter and validates basic functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shadertoy.converter import ShadertoyConverter


def test_converter_basic():
    """Test basic conversion of Shadertoy code"""
    converter = ShadertoyConverter()

    simple_shader = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    fragColor = vec4(uv, 0.5 + 0.5 * sin(iTime), 1.0);
}
"""

    glsl_code = converter.convert(simple_shader)

    # Verify conversion
    assert 'mainImage' in glsl_code
    assert 'void main()' in glsl_code
    assert 'uniform vec3 iResolution' in glsl_code
    assert 'uniform float iTime' in glsl_code
    assert '#ifdef VERTEX_SHADER' in glsl_code
    assert '#ifdef FRAGMENT_SHADER' in glsl_code

    print("✅ test_converter_basic passed")


def test_dependency_detection():
    """Test dependency detection"""
    converter = ShadertoyConverter()

    # Shader with no dependencies
    simple_shader = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    fragColor = vec4(uv, 0.5, 1.0);
}
"""

    deps = converter.detect_dependencies(simple_shader)
    assert deps['channels'] == []
    assert deps['uses_mouse'] == False
    assert deps['uses_time'] == False

    print("✅ Simple shader: no dependencies detected")

    # Shader with time
    time_shader = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    fragColor = vec4(sin(iTime), 0.0, 0.0, 1.0);
}
"""

    deps = converter.detect_dependencies(time_shader)
    assert deps['uses_time'] == True

    print("✅ Time shader: iTime detected")

    # Shader with mouse
    mouse_shader = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 mouse = iMouse.xy / iResolution.xy;
    fragColor = vec4(mouse, 0.0, 1.0);
}
"""

    deps = converter.detect_dependencies(mouse_shader)
    assert deps['uses_mouse'] == True

    print("✅ Mouse shader: iMouse detected")

    # Shader with texture
    texture_shader = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    fragColor = texture(iChannel0, uv);
}
"""

    deps = converter.detect_dependencies(texture_shader)
    assert 0 in deps['channels']

    print("✅ Texture shader: iChannel0 detected")


def test_validation():
    """Test shader validation"""
    converter = ShadertoyConverter()

    # Valid shader
    valid_shader = """
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    fragColor = vec4(1.0);
}
"""

    result = converter.validate_shader(valid_shader)
    assert result['valid'] == True
    assert len(result['errors']) == 0

    print("✅ Valid shader validation passed")

    # Invalid shader (no mainImage)
    invalid_shader = """
void myFunction() {
    // Missing mainImage
}
"""

    result = converter.validate_shader(invalid_shader)
    assert result['valid'] == False
    assert len(result['errors']) > 0

    print("✅ Invalid shader validation caught error")


def test_metadata_extraction():
    """Test metadata extraction from comments"""
    converter = ShadertoyConverter()

    shader_with_metadata = """
// Author: TestAuthor
// License: MIT

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    fragColor = vec4(1.0);
}
"""

    metadata = converter.extract_shader_metadata(shader_with_metadata)
    assert metadata['author'] == 'TestAuthor'
    assert metadata['license'] == 'MIT'

    print("✅ Metadata extraction passed")


def run_all_tests():
    """Run all basic tests"""
    print("\n" + "="*60)
    print("SHADERTOY COMPATIBILITY TESTS - PHASE 1")
    print("="*60 + "\n")

    try:
        test_converter_basic()
        test_dependency_detection()
        test_validation()
        test_metadata_extraction()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")

        print("Phase 1 Complete! 🎉")
        print("\nImplemented:")
        print("  ✅ ShadertoyConverter")
        print("  ✅ ShadertoyNode structure")
        print("  ✅ All basic Shadertoy uniforms")
        print("  ✅ Code validation")
        print("  ✅ Dependency detection")
        print("\nReady for Phase 2: Texture inputs and UI!")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
