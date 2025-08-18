import taichi as ti
from visuals.manager import VisualizerManager
from visuals.presets import GradientVisual

def main():
    manager = VisualizerManager(GradientVisual)
    window = ti.ui.Window("AudioVisualizer", manager.visual.renderer.resolution)
    canvas = window.get_canvas()
    while window.running:
        canvas.set_image(manager.render())
        window.show()

if __name__ == "__main__":
    main()
