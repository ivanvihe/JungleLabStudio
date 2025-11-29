"""YAML Editor Panel"""
from imgui_bundle import imgui
from editor.state import EditorState
from editor.dsl.serializer import PresetSerializer, PresetDeserializer
from editor.events import event_system, Events

class YamlEditor:
    def __init__(self, state: EditorState):
        self.state = state
        self.yaml_text = ""
        self.last_update_time = 0
        self.needs_refresh = True

    def render(self):
        """Render the YAML editor"""
        # Control buttons
        if imgui.button("Refresh from Graph"):
            self.refresh()
            
        imgui.same_line()
        
        if imgui.button("Apply to Graph"):
            self.apply()
            
        imgui.same_line()
        imgui.text_disabled("(Ctrl+Enter to Apply)")

        # Main text editor
        flags = imgui.InputTextFlags_.allow_tab_input | imgui.InputTextFlags_.ctrl_enter_for_new_line
        
        # Make editor fill available space
        avail = imgui.get_content_region_avail()
        
        changed, self.yaml_text = imgui.input_text_multiline(
            "##yaml_code", 
            self.yaml_text, 
            imgui.ImVec2(avail.x, avail.y),
            flags=flags
        )
        
        if changed:
            self.needs_refresh = False
            
        # Handle Ctrl+Enter for apply (if focused)
        if imgui.is_item_focused() and imgui.is_key_pressed(imgui.Key.enter) and imgui.get_io().key_ctrl:
            self.apply()

        # Auto-refresh if we just switched here and haven't edited?
        # For now, explicit refresh is safer to avoid overwriting user work.
        # But we can do initial load.
        if self.needs_refresh and not self.yaml_text:
            self.refresh()

    def refresh(self):
        """Serialize current graph to text"""
        try:
            self.yaml_text = PresetSerializer.serialize(self.state.graph)
            self.needs_refresh = False
        except Exception as e:
            print(f"YAML Serialization Error: {e}")

    def apply(self):
        """Parse text and update graph"""
        try:
            new_graph = PresetDeserializer.deserialize(self.yaml_text)
            # Preserve some state if needed, or just replace
            self.state.graph = new_graph
            
            # Notify system
            event_system.emit(Events.FILE_OPENED, new_graph)
            print("YAML applied successfully")
            
        except Exception as e:
            print(f"YAML Parsing Error: {e}")
            # Could show a popup or error text here
