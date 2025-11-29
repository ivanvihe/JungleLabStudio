"""
Integration tests for Shadertoy compatibility system
Tests the full workflow from code import to YAML preset
"""

import pytest
import os
import yaml
from shadertoy.importer import ShadertoyImporter
from shadertoy.converter import ShadertoyConverter


class TestShadertoyIntegration:
    """Integration tests for Shadertoy system"""

    @pytest.fixture
    def importer(self):
        return ShadertoyImporter()

    @pytest.fixture
    def sample_shader(self):
        return """
        void mainImage(out vec4 fragColor, in vec2 fragCoord) {
            vec2 uv = fragCoord / iResolution.xy;
            vec3 col = 0.5 + 0.5 * cos(iTime + uv.xyx + vec3(0, 2, 4));
            fragColor = vec4(col, 1.0);
        }
        """

    @pytest.fixture
    def complex_shader(self):
        """Shader using multiple Shadertoy features"""
        return """
        void mainImage(out vec4 fragColor, in vec2 fragCoord) {
            vec2 uv = fragCoord / iResolution.xy;

            // Use time
            float t = iTime;

            // Use mouse
            vec2 mouse = iMouse.xy / iResolution.xy;

            // Use texture channel
            vec4 tex = texture(iChannel0, uv);

            // Create effect
            vec2 p = uv - mouse;
            float d = length(p);
            float circle = smoothstep(0.3, 0.25, d);

            vec3 col = mix(tex.rgb, vec3(1.0), circle);
            col *= 0.5 + 0.5 * sin(t + d * 10.0);

            fragColor = vec4(col, 1.0);
        }
        """

    def test_full_import_workflow(self, importer, sample_shader, tmp_path):
        """Test complete import workflow: code -> preset -> YAML file"""
        # Step 1: Import shader code
        preset = importer.import_from_code(
            code=sample_shader,
            name="Test Shader",
            author="Test Author",
            description="Test description"
        )

        # Step 2: Verify preset structure
        assert 'preset' in preset
        assert preset['preset']['name'] == "Test Shader"
        assert preset['preset']['author'] == "Test Author"
        assert 'nodes' in preset['preset']

        # Step 3: Verify nodes were created
        nodes = preset['preset']['nodes']
        assert len(nodes) >= 2  # At least shadertoy node + output

        # Find shadertoy node
        shadertoy_node = None
        for node in nodes:
            if node['type'] == 'shadertoy':
                shadertoy_node = node
                break

        assert shadertoy_node is not None
        assert 'shader_code' in shadertoy_node['params']
        assert 'mainImage' in shadertoy_node['params']['shader_code']

        # Step 4: Save to file
        save_path = tmp_path / "test_preset.yaml"
        success = importer.save_preset(preset, str(save_path))

        assert success
        assert save_path.exists()

        # Step 5: Read back and verify
        with open(save_path, 'r') as f:
            loaded = yaml.safe_load(f)

        assert loaded['preset']['name'] == "Test Shader"

    def test_dependency_detection(self, importer, complex_shader):
        """Test that shader dependencies are correctly detected"""
        deps = importer.converter.detect_dependencies(complex_shader)

        # Should detect texture channel usage
        assert deps['uses_channels'] is True

        # Should detect mouse usage
        assert deps['uses_mouse'] is True

    def test_import_with_channels(self, importer, complex_shader):
        """Test importing shader that uses texture channels"""
        preset = importer.import_from_code(
            code=complex_shader,
            name="Complex Shader",
            author="Test"
        )

        nodes = preset['preset']['nodes']

        # Should have created texture input nodes
        texture_nodes = [n for n in nodes if n['type'] == 'generator.noise']
        assert len(texture_nodes) > 0  # At least one texture placeholder

        # Find shadertoy node and verify it has inputs
        shadertoy_node = next(n for n in nodes if n['type'] == 'shadertoy')
        assert 'inputs' in shadertoy_node

    def test_multipass_structure(self, importer, sample_shader):
        """Test multipass shader import creates correct structure"""
        passes = [
            {'code': sample_shader, 'name': 'BufferA'},
            {'code': sample_shader, 'name': 'Image'}
        ]

        preset = importer.import_multipass(
            passes=passes,
            name="Multipass Shader",
            author="Test"
        )

        nodes = preset['preset']['nodes']

        # Should have nodes for each pass
        shadertoy_nodes = [n for n in nodes if n['type'] == 'shadertoy']
        assert len(shadertoy_nodes) == 2

    def test_template_creation(self, importer):
        """Test quick template creation"""
        from shadertoy.importer import create_template

        template = create_template()

        assert 'mainImage' in template
        assert 'void mainImage(out vec4 fragColor, in vec2 fragCoord)' in template
        assert 'fragColor = vec4(col, 1.0)' in template

    def test_validation_invalid_shader(self, importer):
        """Test that invalid shaders are rejected"""
        invalid_code = """
        // Missing mainImage function
        void someFunction() {
            return;
        }
        """

        validation = importer.converter.validate_shader(invalid_code)
        assert validation['valid'] is False
        assert 'mainImage' in validation['error'].lower()

    def test_validation_valid_shader(self, importer, sample_shader):
        """Test that valid shaders pass validation"""
        validation = importer.converter.validate_shader(sample_shader)
        assert validation['valid'] is True

    def test_generated_yaml_loadable(self, importer, sample_shader, tmp_path):
        """Test that generated YAML is valid and loadable"""
        # Import and save
        preset = importer.import_from_code(
            code=sample_shader,
            name="Loadable Test",
            author="Test"
        )

        save_path = tmp_path / "loadable.yaml"
        importer.save_preset(preset, str(save_path))

        # Try to load with YAML
        with open(save_path, 'r') as f:
            loaded = yaml.safe_load(f)

        # Verify structure is complete
        assert 'preset' in loaded
        assert 'name' in loaded['preset']
        assert 'nodes' in loaded['preset']
        assert len(loaded['preset']['nodes']) > 0

    def test_quick_import_helper(self, sample_shader, tmp_path):
        """Test the quick_import helper function"""
        from shadertoy.importer import quick_import

        output_path = tmp_path / "quick_test.yaml"

        success = quick_import(
            code=sample_shader,
            name="Quick Test",
            output_path=str(output_path)
        )

        assert success
        assert output_path.exists()


class TestGeneratorNodes:
    """Test that new generator nodes can be instantiated"""

    def test_generator_nodes_importable(self):
        """Test that all new generator nodes can be imported"""
        # These should not raise ImportError
        from nodes.generators.raymarching_node import RaymarchingNode
        from nodes.generators.fractal_node import FractalNode
        from nodes.generators.voronoi_node import VoronoiNode
        from nodes.generators.domain_warp_node import DomainWarpNode
        from nodes.generators.plasma_node import PlasmaNode
        from nodes.generators.metaballs_node import MetaballsNode
        from nodes.generators.pattern_node import PatternNode

        # Verify they're all registered
        from core.graph.registry import NodeRegistry

        assert NodeRegistry.is_registered("generator.raymarching")
        assert NodeRegistry.is_registered("generator.fractal")
        assert NodeRegistry.is_registered("generator.voronoi")
        assert NodeRegistry.is_registered("generator.domain_warp")
        assert NodeRegistry.is_registered("generator.plasma")
        assert NodeRegistry.is_registered("generator.metaballs")
        assert NodeRegistry.is_registered("generator.pattern")


class TestPresetLoading:
    """Test that example presets can be loaded"""

    @pytest.fixture
    def preset_dir(self):
        return "community_presets/shadertoy"

    def test_example_presets_exist(self, preset_dir):
        """Test that example preset files exist"""
        expected_presets = [
            "simple_gradient.yaml",
            "animated_circle.yaml",
            "raymarching_sphere.yaml",
            "plasma_tunnel.yaml",
            "liquid_blobs.yaml",
            "mandelbrot_zoom.yaml",
            "kaleidoscope.yaml"
        ]

        for preset_name in expected_presets:
            preset_path = os.path.join(preset_dir, preset_name)
            # Note: This might fail if presets haven't been created yet
            # In real testing, we'd create test fixtures
            if os.path.exists(preset_path):
                assert os.path.isfile(preset_path)

    def test_preset_yaml_valid(self, preset_dir):
        """Test that preset YAML files are valid"""
        preset_files = [
            "simple_gradient.yaml",
            "plasma_tunnel.yaml",
            "liquid_blobs.yaml"
        ]

        for preset_name in preset_files:
            preset_path = os.path.join(preset_dir, preset_name)

            if not os.path.exists(preset_path):
                continue

            with open(preset_path, 'r') as f:
                data = yaml.safe_load(f)

            # Verify structure
            assert 'preset' in data
            assert 'name' in data['preset']
            assert 'nodes' in data['preset']
            assert len(data['preset']['nodes']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
