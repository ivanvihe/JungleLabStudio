#!/bin/bash
# Clean Cache Script - JungleLabStudio
# Removes all Python cache, logs, and temporary files
# Safe to run before git push

echo "🧹 Cleaning JungleLabStudio cache..."

# Count files before cleaning
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
PYC_COUNT=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l)
LOG_COUNT=$(find . -type f -name "*.log" 2>/dev/null | wc -l)

echo ""
echo "📊 Files to clean:"
echo "   __pycache__ directories: $PYCACHE_COUNT"
echo "   .pyc files: $PYC_COUNT"
echo "   .log files: $LOG_COUNT"
echo ""

# Remove Python cache directories
echo "🗑️  Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remove Python bytecode files
echo "🗑️  Removing .pyc files..."
find . -type f -name "*.pyc" -delete 2>/dev/null

# Remove pytest cache
echo "🗑️  Removing .pytest_cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# Remove mypy cache
echo "🗑️  Removing .mypy_cache..."
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null

# Remove egg-info directories
echo "🗑️  Removing *.egg-info..."
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null

# Remove log files
echo "🗑️  Removing log files..."
find . -type f -name "*.log" -delete 2>/dev/null

# Remove ImGui config (temporary UI state)
if [ -f "imgui.ini" ]; then
    echo "🗑️  Removing imgui.ini..."
    rm -f imgui.ini
fi

# Remove logs directory content but keep the directory
if [ -d "src/logs" ]; then
    echo "🗑️  Cleaning src/logs/ directory..."
    rm -f src/logs/*.log 2>/dev/null
fi

if [ -d "logs" ]; then
    echo "🗑️  Cleaning logs/ directory..."
    rm -f logs/*.log 2>/dev/null
fi

# Remove __pycache__ from src/ specifically (most common)
if [ -d "src" ]; then
    echo "🗑️  Deep cleaning src/ directory..."
    find src -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find src -type f -name "*.pyc" -delete 2>/dev/null
fi

echo ""
echo "✅ Cache cleaned successfully!"
echo ""
echo "📦 Ready for git push"
echo ""
