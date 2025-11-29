#!/bin/bash
echo "🧪 Testing node connection system..."
echo ""
echo "Instructions:"
echo "1. Press 'E' to open the editor"
echo "2. Right-click → Generators → Particle System"
echo "3. Right-click → Output → Output"
echo "4. Click orange port on Particles (right side)"
echo "5. Drag to green port on Output (left side)"
echo "6. You should see particles rendering!"
echo ""
echo "Starting application..."
sleep 2

source .venv/bin/activate
python src/main.py
