#!/bin/bash

# Clean cache before running
echo "🧹 Cleaning cache..."
cd /home/ivan/git/JungleLabStudio

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Remove ImGui config (UI state)
rm -f imgui.ini 2>/dev/null

echo "✅ Cache cleaned"
echo ""

# Run application
cd /home/ivan/git/JungleLabStudio/src
source ../venv/bin/activate
export PYTHONUNBUFFERED=1
python -u main.py 2>&1
