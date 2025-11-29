import cv2
import numpy as np
import moderngl
from typing import List, Optional, Dict, Any
from pathlib import Path
from presets.base import VisualPreset, PresetState
from render.resources import load_shader
from core.error_handling import get_error_handler, ErrorCategory, ErrorSeverity

QUAD_VERT = """
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 uv;
void main() {
    uv = in_uv;
    // Flip Y for texture coordinates if needed, mostly for video
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""


def create_placeholder_image(size: tuple) -> np.ndarray:
    """Create a placeholder image (checkerboard pattern) for missing media"""
    width, height = size
    image = np.zeros((height, width, 3), dtype=np.uint8)

    # Create checkerboard pattern
    square_size = max(16, min(width, height) // 16)
    for i in range(0, height, square_size):
        for j in range(0, width, square_size):
            if (i // square_size + j // square_size) % 2 == 0:
                image[i:i+square_size, j:j+square_size] = [60, 60, 60]  # Dark gray
            else:
                image[i:i+square_size, j:j+square_size] = [100, 100, 100]  # Light gray

    # Draw diagonal cross to indicate missing media
    cv2.line(image, (0, 0), (width-1, height-1), (200, 50, 50), 2)
    cv2.line(image, (width-1, 0), (0, height-1), (200, 50, 50), 2)

    # Add text if size is large enough
    if width > 200 and height > 100:
        text = "Media Not Found"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = min(width, height) / 400.0
        thickness = max(1, int(font_scale * 2))
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        cv2.putText(image, text, (text_x, text_y), font, font_scale, (200, 200, 200), thickness)

    return image

class MediaPreset(VisualPreset):
    name = "media_player"

    def init(self) -> None:
        self.file_path = getattr(self.state, 'file_path', "")
        self.prog = self.ctx.program(vertex_shader=QUAD_VERT, fragment_shader=load_shader("media_glitch.glsl"))

        self.quad = self.ctx.vertex_array(
            self.prog,
            [(self.ctx.buffer(np.array([
                -1.0, -1.0, 0.0, 1.0,
                1.0, -1.0, 1.0, 1.0,
                -1.0,  1.0, 0.0, 0.0,
                1.0,  1.0, 1.0, 0.0,
            ], dtype="f4").tobytes()), "2f 2f", "in_pos", "in_uv")],
             self.ctx.buffer(np.array([0, 1, 2, 2, 1, 3], dtype="i4").tobytes())
        )
        self.texture = self.ctx.texture(self.size, 3, dtype="f1")
        self.cap = None
        self.is_video = False
        self.frame_data = None

        if self.file_path:
            self.load_media(self.file_path)

        # Effects State
        self.timers = {
            "slice": 0.0,
            "transform": 0.0,
            "rays": 0.0,
            "inter": 0.0
        }
        self.durations = {
            "slice": 2.0,
            "transform": 2.0,
            "rays": 2.0,
            "inter": 2.0
        }

    def load_media(self, path: str):
        error_handler = get_error_handler()
        media_path = Path(path)

        # Check if file exists
        if not media_path.exists():
            error_handler.handle_media_error(
                media_path,
                f"File not found: {path}"
            )
            self._load_placeholder()
            return

        # Try video first
        try:
            cap = cv2.VideoCapture(path)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self.cap = cap
                    self.is_video = True
                    self.update_frame(frame)
                    error_handler.log(
                        f"MediaPreset: Loaded video: {media_path.name}",
                        ErrorSeverity.INFO,
                        ErrorCategory.MEDIA
                    )
                    return
                else:
                    cap.release()
        except Exception as e:
            error_handler.log(
                f"MediaPreset: Failed to open video {media_path.name}: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MEDIA
            )

        # Try image
        try:
            img = cv2.imread(path)
            if img is not None:
                self.is_video = False
                self.update_frame(img)
                error_handler.log(
                    f"MediaPreset: Loaded image: {media_path.name}",
                    ErrorSeverity.INFO,
                    ErrorCategory.MEDIA
                )
                return
        except Exception as e:
            error_handler.log(
                f"MediaPreset: Failed to load image {media_path.name}: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MEDIA
            )

        # If all else fails, load placeholder
        error_handler.handle_media_error(
            media_path,
            f"Failed to load media (unsupported format or corrupted file): {path}"
        )
        self._load_placeholder()

    def _load_placeholder(self):
        """Load a placeholder image when media fails to load"""
        error_handler = get_error_handler()
        placeholder = create_placeholder_image(self.size)
        self.texture.write(placeholder.tobytes())
        self.is_video = False
        self.cap = None
        error_handler.log(
            "MediaPreset: Using placeholder image",
            ErrorSeverity.DEBUG,
            ErrorCategory.MEDIA
        )

    def update_frame(self, frame):
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize? For now, let's just upload. Or render to texture size.
        # OpenCV resize is fast.
        frame = cv2.resize(frame, self.size)
        self.texture.write(frame.tobytes())

    def update_render(self, dt: float, audio_tex, fft_gain: float, bands, midi_events, orientation: str) -> None:
        if self.is_video and self.cap:
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
            if ret:
                self.update_frame(frame)
        
        # Update Timers
        for k in self.timers:
            self.timers[k] = max(0.0, self.timers[k] - dt)
            
        # Render
        self.texture.use(location=0)
        self.prog["tex0"].value = 0
        self.prog["time"].value = 0.0 # use system time passed in? Engine passes `time.time()` usually to post, but `dt` here. 
        # Let's use accumulated time or just dt accumulation
        # Base class doesn't store time.
        if not hasattr(self, '_acc_time'): self._acc_time = 0.0
        self._acc_time += dt
        self.prog["time"].value = self._acc_time
        self.prog["resolution"].value = self.size
        
        # Set Effect Uniforms
        # Map timer > 0 to 1.0 intensity (or fade out?)
        # Prompt says "apply for 2 seconds". Let's do linear fade? Or sustain.
        # "during 2 seconds" usually implies a pulse.
        
        def get_amt(name):
            t = self.timers[name]
            d = self.durations[name]
            if t <= 0: return 0.0
            return 1.0 # Sustain? Or t/d for fade? Let's do fade out.
            # return t/d
        
        self.prog["slice_amt"].value = 1.0 if self.timers["slice"] > 0 else 0.0
        self.prog["transform_amt"].value = (self.timers["transform"] / self.durations["transform"]) * 0.5 # Scaling
        self.prog["rays_amt"].value = 1.0 if self.timers["rays"] > 0 else 0.0
        self.prog["interference_amt"].value = 1.0 if self.timers["inter"] > 0 else 0.0
        
        self.quad.render(moderngl.TRIANGLE_STRIP)

    @property
    def actions(self) -> List[str]:
        return ["trigger_slice", "trigger_transform", "trigger_rays", "trigger_inter"]

    def trigger_action(self, action: str, payload=None):
        # Map actions to effects
        key = action.replace("trigger_", "")
        if key in self.timers:
            self.timers[key] = self.durations[key]
