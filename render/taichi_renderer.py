"""Enhanced Taichi renderer with proper initialization."""

import numpy as np
import taichi as ti
from typing import Tuple, Callable

class TaichiRenderer:
    """Enhanced Taichi renderer with automatic initialization."""
    
    _initialized = False
    
    def __init__(self, resolution: Tuple[int, int] = (640, 480)):
        # Initialize Taichi if not already done
        if not TaichiRenderer._initialized:
            self._init_taichi()
            TaichiRenderer._initialized = True
            
        self.resolution = resolution
        self.canvas = ti.Vector.field(4, dtype=ti.f32, shape=resolution)
        self._passes = []
        self._frame_count = 0
        
    def _init_taichi(self):
        """Initialize Taichi with best available backend."""
        backends = [ti.vulkan, ti.cuda, ti.opengl, ti.cpu]
        
        for backend in backends:
            try:
                ti.init(arch=backend, debug=False)
                print(f" Taichi initialized with {backend}")
                return
            except Exception as e:
                print(f" Failed to initialize {backend}: {e}")
                continue
                
        # Fallback
        try:
            ti.init(arch=ti.cpu, debug=False)
            print("Taichi initialized with CPU fallback")
        except Exception as e:
            print(f" Failed to initialize Taichi: {e}")
            raise
        
    def add_pass(self, name: str, compute_func: Callable):
        """Add a render pass."""
        self._passes.append((name, compute_func))
        
    def render(self) -> np.ndarray:
        """Execute all render passes and return the result."""
        # Clear canvas
        self._clear_canvas()
        
        # Execute passes
        for name, func in self._passes:
            try:
                func(self.canvas)
            except Exception as e:
                print(f"Error in render pass '{name}': {e}")
                
        self._frame_count += 1
        
        # Convert to numpy and return grayscale
        canvas_np = self.canvas.to_numpy()
        # Convert RGBA to grayscale
        if len(canvas_np.shape) == 3 and canvas_np.shape[2] >= 3:
            gray = np.dot(canvas_np[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = canvas_np.mean(axis=2) if len(canvas_np.shape) == 3 else canvas_np
            
        return gray.astype(np.float32)
    
    @ti.kernel
    def _clear_canvas(self):
        """Clear the canvas."""
        for i, j in self.canvas:
            self.canvas[i, j] = ti.Vector([0.0, 0.0, 0.0, 1.0])
            
    def get_frame_count(self) -> int:
        """Get current frame count."""
        return self._frame_count