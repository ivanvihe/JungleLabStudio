"""Preview panel for live output visualization"""
from imgui_bundle import imgui
import moderngl
from typing import Optional


class PreviewPanel:
    def __init__(self):
        self.show_preview = True
        self.preview_size = (640, 480)
        self.texture_id = None

    def render(self, executor, graph, display_w: float):
        """Render preview window showing the output texture"""
        if not self.show_preview:
            return

        flags = (imgui.WindowFlags_.no_collapse |
                imgui.WindowFlags_.no_resize | 
                imgui.WindowFlags_.no_title_bar)

        if imgui.begin("Live Preview", flags=flags):
            # 1. Determine Target Aspect Ratio from Init Node
            target_ratio = 16.0 / 9.0  # Default Horizontal
            
            if graph:
                for node in graph.nodes.values():
                    if node.node_type == "init":
                        ar_param = node.params.get("aspect_ratio", "horizontal")
                        if ar_param == "vertical":
                            target_ratio = 9.0 / 16.0
                        elif ar_param == "square":
                            target_ratio = 1.0
                        break

            # 2. Calculate Layout
            available = imgui.get_content_region_avail()
            avail_w, avail_h = available.x, available.y
            
            # 3. Draw Striped Background
            draw_list = imgui.get_window_draw_list()
            p_min = imgui.get_cursor_screen_pos()
            p_max = imgui.ImVec2(p_min.x + avail_w, p_min.y + avail_h)
            
            # Background fill
            draw_list.add_rect_filled(p_min, p_max, imgui.get_color_u32((0.1, 0.1, 0.1, 1.0)))
            
            # Stripes
            stripe_color = imgui.get_color_u32((0.15, 0.15, 0.15, 1.0))
            spacing = 20.0
            
            # Simple diagonal lines
            # We iterate a bit inefficiently here but fine for UI
            steps = int((avail_w + avail_h) / spacing)
            for i in range(steps):
                x1 = p_min.x + i * spacing
                y1 = p_min.y
                x2 = p_min.x + i * spacing - avail_h
                y2 = p_min.y + avail_h
                
                # Clip to bounds manually if needed, but simple lines are okay usually
                # Or utilize push_clip_rect
                pass # Actually ImGui has push_clip_rect
            
            draw_list.push_clip_rect(p_min, p_max, True)
            for i in range(steps * 2): # Cover enough range
                # Diagonal /
                # Start from top-left extended area
                offset = (i * spacing) - avail_h
                p1 = imgui.ImVec2(p_min.x + offset, p_min.y)
                p2 = imgui.ImVec2(p_min.x + offset + avail_h, p_min.y + avail_h)
                draw_list.add_line(p1, p2, stripe_color, 2.0)
            draw_list.pop_clip_rect()

            # 4. Calculate Centered Image Size
            display_w = avail_w
            display_h = display_w / target_ratio
            
            if display_h > avail_h:
                display_h = avail_h
                display_w = display_h * target_ratio
                
            # Center it
            offset_x = (avail_w - display_w) * 0.5
            offset_y = (avail_h - display_h) * 0.5
            
            # 5. Render Texture or Placeholder
            output_tex = executor.get_output_texture() if executor else None
            
            if output_tex:
                # Position cursor for image
                current_cursor = imgui.get_cursor_pos()
                imgui.set_cursor_pos(imgui.ImVec2(current_cursor.x + offset_x, current_cursor.y + offset_y))
                
                imgui.image(
                    imgui.ImTextureRef(output_tex.glo),
                    imgui.ImVec2(display_w, display_h),
                    uv0=imgui.ImVec2(0, 1),
                    uv1=imgui.ImVec2(1, 0)
                )
            else:
                # Draw placeholder rect if no output
                p_img_min = imgui.ImVec2(p_min.x + offset_x, p_min.y + offset_y)
                p_img_max = imgui.ImVec2(p_img_min.x + display_w, p_img_min.y + display_h)
                draw_list.add_rect(p_img_min, p_img_max, imgui.get_color_u32((0.5, 0.5, 0.5, 1.0)))
                
                # Centered text
                text = "No Output"
                text_size = imgui.calc_text_size(text)
                text_pos = imgui.ImVec2(
                    p_img_min.x + (display_w - text_size.x) * 0.5,
                    p_img_min.y + (display_h - text_size.y) * 0.5
                )
                draw_list.add_text(text_pos, imgui.get_color_u32((1,1,1,1)), text)

        imgui.end()

    def toggle(self):
        """Toggle preview visibility"""
        self.show_preview = not self.show_preview
