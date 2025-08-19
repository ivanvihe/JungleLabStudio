import taichi as ti
from visuals.base import TaichiVisual

@ti.kernel
def _lines(img: ti.template(), offset: ti.i32, spacing: ti.i32):
    for i, j in img:
        # Fixed: Use proper conditional assignment for Taichi
        if (i + offset) % spacing == 0:
            img[i, j] = 1.0
        else:
            img[i, j] = 0.0

class AbstractLinesVisualizer(TaichiVisual):
    """Simple vertical lines animation using Taichi."""
    visual_name = "Abstract Lines"

    def __init__(self, *args, **kwargs):
        self.offset = 0
        self.num_lines = 20
        self.spacing = 32  # Initialize with default value
        # Initialize parent first
        super().__init__(*args, **kwargs)

    def setup(self):
        # Derive the spacing from the current renderer resolution
        self.spacing = max(1, self.renderer.resolution[0] // self.num_lines)
        # Clear any existing passes
        self.renderer.clear_passes()
        # Add the lines pass
        self.renderer.add_pass("lines", self._render_pass)

    def _render_pass(self, img):
        """Separate render pass method for better error handling"""
        try:
            _lines(img, self.offset, self.spacing)
        except Exception as e:
            print(f"Error in lines render pass: {e}")
            # Fallback: clear the image
            for i, j in img:
                img[i, j] = 0.0

    def render(self):
        img = super().render()
        # Update offset for animation only if spacing is valid
        if self.spacing > 0:
            self.offset = (self.offset + 1) % self.spacing
        return img

    def get_controls(self):
        """Add controls for the visualizer"""
        controls = super().get_controls() if hasattr(super(), 'get_controls') else {}
        controls.update({
            "Number of Lines": {
                "type": "slider",
                "min": 5,
                "max": 100,
                "value": self.num_lines,
                "description": "Number of vertical lines to display"
            }
        })
        return controls

    def update_control(self, name, value):
        """Handle control updates"""
        if hasattr(super(), 'update_control') and super().update_control(name, value):
            return True
            
        if name == "Number of Lines":
            self.num_lines = int(value)
            # Recalculate spacing
            self.spacing = max(1, self.renderer.resolution[0] // self.num_lines)
            return True
        return False