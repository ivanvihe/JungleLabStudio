import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from render.engine import VisualEngine


def main():
    # Check for preset argument
    preset_path = None
    if len(sys.argv) > 1:
        preset_path = sys.argv[1]
        print(f"Loading preset: {preset_path}")

    app = VisualEngine(preset_path=preset_path)
    app.run()


if __name__ == "__main__":
    main()
