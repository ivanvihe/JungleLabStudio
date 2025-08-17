from visuals.base_visualizer import BaseVisualizer

class BuildingMadnessVisualizer(BaseVisualizer):
    """Minimal placeholder visualizer for testing."""
    visual_name = "Building Madness"

    def get_controls(self):
        controls = super().get_controls()
        # Additional default control example
        controls.update({
            "Color Shift": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "value": 50,
            }
        })
        return controls
