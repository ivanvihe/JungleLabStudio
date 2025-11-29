"""Node inspector panel"""
from imgui_bundle import imgui
from editor.state import EditorState


class Inspector:
    def __init__(self, state: EditorState):
        self.state = state

    def render(self):
        """Render inspector panel"""
        imgui.begin("Inspector", flags=imgui.WindowFlags_.no_collapse)

        selected_nodes = self.state.graph.get_selected_nodes()

        if not selected_nodes:
            imgui.text("No node selected")
            imgui.text_disabled("Select a node to edit properties")
        elif len(selected_nodes) > 1:
            imgui.text(f"{len(selected_nodes)} nodes selected")
            imgui.text_disabled("Select a single node to edit")
        else:
            # Show properties for single node
            node = selected_nodes[0]
            
            if imgui.begin_tab_bar("NodePropsTabs"):
                
                # --- TAB 1: INSPECTOR (General Info) ---
                if imgui.begin_tab_item("Inspector")[0]:
                    imgui.text(f"Type: {node.node_type}")
                    imgui.text(f"ID: {node.id}")
                    imgui.separator()
                    
                    # Rename
                    changed, new_name = imgui.input_text("Name", node.display_name, 256)
                    if changed:
                        node.display_name = new_name
                        
                    imgui.separator()

                    # Position / Transform
                    if imgui.tree_node("Transform"):
                        changed, pos_x = imgui.input_float("X", node.position.x, step=10.0)
                        if changed: node.position.x = pos_x

                        changed, pos_y = imgui.input_float("Y", node.position.y, step=10.0)
                        if changed: node.position.y = pos_y

                        changed, size_x = imgui.input_float("Width", node.size.x, step=10.0)
                        if changed: node.size.x = max(100, size_x)

                        changed, size_y = imgui.input_float("Height", node.size.y, step=10.0)
                        if changed: node.size.y = max(60, size_y)

                        imgui.tree_pop()

                    # Ports Info
                    if imgui.tree_node("Connectivity"):
                        imgui.text("Inputs:")
                        if not node.inputs: imgui.text_disabled("  (None)")
                        for port in node.inputs:
                            status = "connected" if port.connected else "disconnected"
                            color = (0.4, 0.8, 0.4, 1) if port.connected else (0.5, 0.5, 0.5, 1)
                            imgui.text_colored(color, f"  • {port.name} ({port.data_type})")

                        imgui.text("Outputs:")
                        if not node.outputs: imgui.text_disabled("  (None)")
                        for port in node.outputs:
                            imgui.text(f"  • {port.name} ({port.data_type})")

                        imgui.tree_pop()
                    
                    imgui.end_tab_item()

                # --- TAB 2: NODE SETTINGS (Parameters, Animations, Triggers) ---
                if imgui.begin_tab_item("Node Settings")[0]:

                    # Special UI for MIDI Listener nodes
                    if node.node_type == "midi.listener":
                        self._render_midi_listener_ui(node)

                    # Parameters
                    if node.params:
                        imgui.text("Parameters")
                        imgui.separator()
                        for param_name, param_value in node.params.items():
                            # Display parameter based on type
                            if isinstance(param_value, bool):
                                changed, new_val = imgui.checkbox(param_name, param_value)
                                if changed:
                                    node.params[param_name] = new_val

                            elif isinstance(param_value, (int, float)):
                                if isinstance(param_value, int):
                                    changed, new_val = imgui.input_int(param_name, param_value)
                                else:
                                    changed, new_val = imgui.slider_float(param_name, param_value, 0.0, 10.0)

                                if changed:
                                    node.params[param_name] = new_val

                            elif isinstance(param_value, str):
                                if param_name == "aspect_ratio":
                                    # Aspect Ratio Combo
                                    if imgui.begin_combo(param_name, param_value):
                                        for ratio in ["horizontal", "vertical", "square"]:
                                            is_selected = (ratio == param_value)
                                            if imgui.selectable(ratio, is_selected)[0]:
                                                node.params[param_name] = ratio
                                            if is_selected:
                                                imgui.set_item_default_focus()
                                        imgui.end_combo()
                                else:
                                    changed, new_val = imgui.input_text(param_name, param_value, 256)
                                    if changed:
                                        node.params[param_name] = new_val
                            else:
                                imgui.text(f"{param_name}: {param_value}")
                        imgui.spacing()
                    
                    # Animations
                    if imgui.collapsing_header("Animations", True):
                        # List existing animations
                        to_remove = []
                        for i, anim in enumerate(node.animations):
                            imgui.push_id(f"anim_{i}")
                            if imgui.tree_node(f"{anim.animation_type} -> {anim.target_param}###header"):
                                # Delete button
                                if imgui.button("Delete"):
                                    to_remove.append(anim)
                                
                                # Target param selector
                                if node.params:
                                    if imgui.begin_combo("Target", anim.target_param):
                                        for p_name in node.params.keys():
                                            is_selected = (p_name == anim.target_param)
                                            if imgui.selectable(p_name, is_selected)[0]:
                                                anim.target_param = p_name
                                            if is_selected:
                                                imgui.set_item_default_focus()
                                        imgui.end_combo()
                                
                                # Type selector
                                types = ["lfo", "envelope", "noise_walk"]
                                if imgui.begin_combo("Type", anim.animation_type):
                                    for t in types:
                                        if imgui.selectable(t, t == anim.animation_type)[0]:
                                            anim.animation_type = t
                                    imgui.end_combo()
                                    
                                # LFO Properties
                                if anim.animation_type == "lfo":
                                    _, anim.lfo_frequency = imgui.slider_float("Freq", anim.lfo_frequency, 0.01, 10.0)
                                    _, anim.lfo_amplitude = imgui.slider_float("Amp", anim.lfo_amplitude, 0.0, 5.0)
                                    
                                    waveforms = ["sine", "square", "saw", "triangle"]
                                    if imgui.begin_combo("Wave", anim.lfo_waveform):
                                        for w in waveforms:
                                            if imgui.selectable(w, w == anim.lfo_waveform)[0]:
                                                anim.lfo_waveform = w
                                        imgui.end_combo()
                                        
                                imgui.tree_pop()
                            imgui.pop_id()
                            
                        # Apply removals
                        for anim in to_remove:
                            node.animations.remove(anim)
                            
                        # Add new animation
                        if imgui.button("Add Animation"):
                            from editor.graph.visual_node import AnimationBlock
                            import uuid
                            # Default to first param if available
                            target = list(node.params.keys())[0] if node.params else "none"
                            new_anim = AnimationBlock(
                                id=f"anim_{uuid.uuid4().hex[:8]}",
                                target_param=target,
                                animation_type="lfo"
                            )
                            node.animations.append(new_anim)
                        imgui.spacing()

                    # Triggers
                    if imgui.collapsing_header("Triggers / MIDI", True):
                        to_remove_trig = []
                        for i, trig in enumerate(node.triggers):
                            imgui.push_id(f"trig_{i}")
                            label = f"{trig.trigger_type}"
                            if trig.trigger_type == "midi_note": label += f" #{trig.midi_note}"
                            elif trig.trigger_type == "midi_cc": label += f" CC{trig.midi_cc}"
                            
                            if imgui.tree_node(f"{label} -> {trig.target_param}###header"):
                                if imgui.button("Delete"):
                                    to_remove_trig.append(trig)
                                    
                                # Target param
                                if node.params:
                                    if imgui.begin_combo("Target", trig.target_param):
                                        for p_name in node.params.keys():
                                            if imgui.selectable(p_name, p_name == trig.target_param)[0]:
                                                trig.target_param = p_name
                                        imgui.end_combo()
                                        
                                # Trigger Type
                                types = ["midi_note", "midi_cc", "fft_band"]
                                if imgui.begin_combo("Type", trig.trigger_type):
                                    for t in types:
                                        if imgui.selectable(t, t == trig.trigger_type)[0]:
                                            trig.trigger_type = t
                                    imgui.end_combo()
                                    
                                # Properties
                                if trig.trigger_type in ["midi_note", "midi_cc"]:
                                    # Learn Button
                                    is_learning = (self.state.midi_learn_mode and self.state.midi_learn_target == trig.id)
                                    
                                    if is_learning:
                                        imgui.push_style_color(imgui.Col_.button, (1.0, 0.6, 0.0, 1.0))
                                        if imgui.button("Listening..."):
                                            # Cancel learn
                                            self.state.midi_learn_mode = False
                                            self.state.midi_learn_target = None
                                        imgui.pop_style_color()
                                    else:
                                        if imgui.button("Learn"):
                                            self.state.midi_learn_mode = True
                                            self.state.midi_learn_target = trig.id
                                    
                                    imgui.same_line()
                                    
                                    if trig.trigger_type == "midi_note":
                                        val = trig.midi_note if trig.midi_note is not None else 60
                                        changed, val = imgui.input_int("Note", val)
                                        if changed: trig.midi_note = val
                                    elif trig.trigger_type == "midi_cc":
                                        val = trig.midi_cc if trig.midi_cc is not None else 14
                                        changed, val = imgui.input_int("CC", val)
                                        if changed: trig.midi_cc = val
                                    
                                # Channel
                                val = trig.midi_channel if trig.midi_channel is not None else 1
                                changed, val = imgui.input_int("Channel", val)
                                if changed: trig.midi_channel = max(1, min(16, val))
                                
                                imgui.tree_pop()
                            imgui.pop_id()
                            
                        for trig in to_remove_trig:
                            node.triggers.remove(trig)
                            
                        if imgui.button("Add Trigger"):
                            from editor.graph.visual_node import TriggerBinding
                            import uuid
                            target = list(node.params.keys())[0] if node.params else "none"
                            new_trig = TriggerBinding(
                                id=f"trig_{uuid.uuid4().hex[:8]}",
                                trigger_type="midi_note",
                                action_mode="set",
                                target_param=target,
                                midi_note=60
                            )
                            node.triggers.append(new_trig)

                    imgui.end_tab_item()
                
                imgui.end_tab_bar()

        imgui.end()

    def _render_node_properties(self, node):
        pass # Deprecated by render() logic above

    def _render_midi_listener_ui(self, node):
        """Render special UI for MIDI Listener nodes"""
        imgui.text("MIDI Listener Controls")
        imgui.separator()

        # MIDI Learn Button
        is_learning = hasattr(node, 'midi_learn_mode') and node.midi_learn_mode

        if is_learning:
            imgui.push_style_color(imgui.Col_.button, (0.2, 0.8, 0.2, 1.0))
            if imgui.button("Listening... (Click to cancel)"):
                node.midi_learn_mode = False
            imgui.pop_style_color()
        else:
            if imgui.button("MIDI Learn"):
                if hasattr(node, 'start_midi_learn'):
                    node.start_midi_learn()

        # Show current mapping
        if hasattr(node, 'midi_mapping') and node.midi_mapping:
            mapping = node.midi_mapping
            imgui.text_colored((0.4, 0.8, 0.4, 1.0), f"Mapped:")

            if mapping.message_type == 'note_on':
                imgui.text(f"  Note: {mapping.note} | Channel: {mapping.channel + 1}")
            elif mapping.message_type == 'control_change':
                imgui.text(f"  CC: {mapping.cc} | Channel: {mapping.channel + 1}")
            else:
                imgui.text(f"  Type: {mapping.message_type}")

        # Show current value
        if hasattr(node, 'smoothed_value'):
            value = node.smoothed_value
            # Normalize for display if needed
            normalize = node.get_param_value("normalize", 1.0) > 0.5
            display_value = value if normalize else value / 127.0

            imgui.text(f"Current Value: {value:.3f}")
            # Visual bar
            imgui.progress_bar(display_value, (200, 20), "")

        imgui.separator()
        imgui.spacing()
