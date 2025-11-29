"""Shadertoy Importer Panel"""
from imgui_bundle import imgui
from editor.state import EditorState
from shadertoy.importer import ShadertoyImporter
from editor.events import event_system, Events
import os


class ShadertoyImporterUI:
    """
    ImGui UI for importing Shadertoy shaders

    Allows users to:
    - Paste Shadertoy shader code
    - Set preset name and metadata
    - Validate shader code
    - Import to YAML preset
    - Save preset to file
    """

    def __init__(self, state: EditorState):
        self.state = state
        self.importer = ShadertoyImporter()

        # UI State
        self.shader_code = ""
        self.preset_name = "My Shadertoy Effect"
        self.preset_author = "Anonymous"
        self.preset_description = ""

        # Validation state
        self.validation_result = None
        self.last_validated_code = ""

        # Import result
        self.import_success = False
        self.import_error = ""
        self.generated_yaml = ""

        # File save state
        self.save_path = "community_presets/shadertoy/"
        self.save_filename = "my_shader.yaml"

    def render(self):
        """Render the Shadertoy importer panel"""
        imgui.push_item_width(250)

        # Header
        imgui.text_colored(imgui.ImVec4(0.4, 0.8, 1.0, 1.0), "Shadertoy Importer")
        imgui.separator()
        imgui.spacing()

        # --- Metadata Section ---
        imgui.text("Preset Metadata:")
        _, self.preset_name = imgui.input_text("Name##preset_name", self.preset_name)
        _, self.preset_author = imgui.input_text("Author##preset_author", self.preset_author)
        _, self.preset_description = imgui.input_text(
            "Description##preset_desc",
            self.preset_description
        )

        imgui.spacing()
        imgui.separator()
        imgui.spacing()

        # --- Shader Code Section ---
        imgui.text("Shadertoy Code:")
        imgui.text_disabled("Paste your Shadertoy shader code here (mainImage function)")

        # Code editor
        flags = imgui.InputTextFlags_.allow_tab_input
        avail = imgui.get_content_region_avail()
        code_editor_height = max(200, avail.y - 300)  # Leave space for buttons below

        changed, self.shader_code = imgui.input_text_multiline(
            "##shader_code",
            self.shader_code,
            imgui.ImVec2(-1, code_editor_height),
            flags=flags
        )

        if changed:
            # Reset validation when code changes
            self.validation_result = None
            self.import_success = False

        imgui.spacing()

        # --- Validation Section ---
        if imgui.button("Validate Shader", imgui.ImVec2(150, 0)):
            self._validate_shader()

        imgui.same_line()

        # Show validation result
        if self.validation_result:
            if self.validation_result['valid']:
                imgui.text_colored(
                    imgui.ImVec4(0.0, 1.0, 0.0, 1.0),
                    "✓ Valid Shadertoy code"
                )
            else:
                imgui.text_colored(
                    imgui.ImVec4(1.0, 0.0, 0.0, 1.0),
                    "✗ Invalid"
                )
                if imgui.is_item_hovered():
                    imgui.set_tooltip(self.validation_result.get('error', 'Unknown error'))

        imgui.spacing()

        # Show detected dependencies
        if self.validation_result and self.validation_result['valid']:
            deps = self.validation_result.get('dependencies', {})
            if any(deps.values()):
                imgui.text("Detected dependencies:")
                if deps.get('uses_channels'):
                    imgui.bullet_text("Uses texture channels (iChannel0-3)")
                if deps.get('uses_mouse'):
                    imgui.bullet_text("Uses mouse input (iMouse)")
                if deps.get('uses_audio'):
                    imgui.bullet_text("Uses audio input (FFT)")
                if deps.get('uses_keyboard'):
                    imgui.bullet_text("Uses keyboard input")

        imgui.spacing()
        imgui.separator()
        imgui.spacing()

        # --- Import Section ---
        if imgui.button("Import to Preset", imgui.ImVec2(150, 0)):
            self._import_shader()

        imgui.same_line()

        if self.import_success:
            imgui.text_colored(
                imgui.ImVec4(0.0, 1.0, 0.0, 1.0),
                "✓ Imported successfully"
            )
        elif self.import_error:
            imgui.text_colored(
                imgui.ImVec4(1.0, 0.0, 0.0, 1.0),
                f"✗ Error: {self.import_error[:50]}..."
            )
            if imgui.is_item_hovered():
                imgui.set_tooltip(self.import_error)

        imgui.spacing()

        # --- Save Section ---
        if self.import_success:
            imgui.text("Save Preset:")
            _, self.save_path = imgui.input_text("Directory##save_path", self.save_path)
            _, self.save_filename = imgui.input_text("Filename##save_filename", self.save_filename)

            full_path = os.path.join(self.save_path, self.save_filename)
            imgui.text_disabled(f"Will save to: {full_path}")

            if imgui.button("Save to File", imgui.ImVec2(150, 0)):
                self._save_preset()

            imgui.same_line()

            if imgui.button("Load to Editor", imgui.ImVec2(150, 0)):
                self._load_to_editor()

        imgui.spacing()
        imgui.separator()
        imgui.spacing()

        # --- Help Section ---
        if imgui.collapsing_header("Help & Examples"):
            imgui.text_wrapped(
                "This importer allows you to paste Shadertoy shader code and "
                "convert it to a JungleLabStudio preset.\n\n"
                "Your shader code should contain a mainImage() function:\n"
                "  void mainImage(out vec4 fragColor, in vec2 fragCoord)\n\n"
                "All Shadertoy uniforms are supported:\n"
                "  - iTime, iTimeDelta, iFrame\n"
                "  - iResolution, iMouse\n"
                "  - iChannel0-3 (texture inputs)\n"
                "  - iDate, iSampleRate\n\n"
                "Example minimal shader:\n"
            )

            imgui.text_disabled(
                "void mainImage(out vec4 fragColor, in vec2 fragCoord) {\n"
                "    vec2 uv = fragCoord / iResolution.xy;\n"
                "    vec3 col = 0.5 + 0.5 * cos(iTime + uv.xyx + vec3(0,2,4));\n"
                "    fragColor = vec4(col, 1.0);\n"
                "}"
            )

        imgui.pop_item_width()

    def _validate_shader(self):
        """Validate the shader code"""
        if not self.shader_code.strip():
            self.validation_result = {
                'valid': False,
                'error': 'Shader code is empty'
            }
            return

        # Validate using the converter
        validation = self.importer.converter.validate_shader(self.shader_code)
        self.validation_result = validation
        self.last_validated_code = self.shader_code

        # Also detect dependencies
        if validation['valid']:
            deps = self.importer.converter.detect_dependencies(self.shader_code)
            self.validation_result['dependencies'] = deps

    def _import_shader(self):
        """Import the shader to a preset"""
        # Validate first if not already validated
        if not self.validation_result or self.last_validated_code != self.shader_code:
            self._validate_shader()

        if not self.validation_result or not self.validation_result['valid']:
            self.import_error = "Please validate the shader first"
            self.import_success = False
            return

        try:
            # Import using the importer
            preset_data = self.importer.import_from_code(
                code=self.shader_code,
                name=self.preset_name or "Untitled",
                author=self.preset_author or "Anonymous",
                description=self.preset_description
            )

            # Convert to YAML string for preview
            import yaml
            self.generated_yaml = yaml.dump(preset_data, default_flow_style=False, sort_keys=False)

            self.import_success = True
            self.import_error = ""

        except Exception as e:
            self.import_error = str(e)
            self.import_success = False

    def _save_preset(self):
        """Save the imported preset to a file"""
        if not self.import_success or not self.generated_yaml:
            print("No preset to save")
            return

        try:
            # Ensure directory exists
            os.makedirs(self.save_path, exist_ok=True)

            # Save file
            full_path = os.path.join(self.save_path, self.save_filename)

            # Use the importer's save method
            import yaml
            preset_data = yaml.safe_load(self.generated_yaml)

            success = self.importer.save_preset(preset_data, full_path)

            if success:
                print(f"✓ Preset saved to: {full_path}")
                # Show notification
                event_system.emit(Events.FILE_SAVED, full_path)
            else:
                print(f"✗ Failed to save preset")

        except Exception as e:
            print(f"Error saving preset: {e}")

    def _load_to_editor(self):
        """Load the imported preset into the editor"""
        if not self.import_success or not self.generated_yaml:
            print("No preset to load")
            return

        try:
            # Parse the YAML and load into editor
            from editor.dsl.serializer import PresetDeserializer

            new_graph = PresetDeserializer.deserialize(self.generated_yaml)
            self.state.graph = new_graph

            # Notify system
            event_system.emit(Events.FILE_OPENED, new_graph)
            print("✓ Shadertoy preset loaded to editor")

        except Exception as e:
            print(f"Error loading to editor: {e}")


def render_shadertoy_window(state: EditorState, importer_ui: ShadertoyImporterUI = None):
    """
    Standalone function to render Shadertoy importer as a window

    Usage in main editor loop:
        from editor.ui.shadertoy_importer import render_shadertoy_window, ShadertoyImporterUI

        # Create once
        shadertoy_ui = ShadertoyImporterUI(state)

        # In render loop
        if show_shadertoy_window:
            show_shadertoy_window = render_shadertoy_window(state, shadertoy_ui)
    """
    if importer_ui is None:
        importer_ui = ShadertoyImporterUI(state)

    expanded, opened = imgui.begin("Shadertoy Importer", True)

    if expanded:
        importer_ui.render()

    imgui.end()

    return opened  # Return opened state so caller can close window
