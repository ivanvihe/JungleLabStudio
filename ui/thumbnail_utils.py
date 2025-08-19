# ui/thumbnail_utils.py - MODERNIZED VERSION
from PySide6.QtGui import QPixmap, QColor, QPainter, QPen, QBrush, QPolygon, QLinearGradient
from PySide6.QtCore import QPoint, Qt, QRect
import math
from pathlib import Path
import json

THUMBNAIL_CONFIG = Path("config/custom_thumbnails.json")

# Modern color palette for thumbnails
MODERN_THUMBNAIL_COLORS = {
    'primary_base': QColor(255, 107, 53),    # Orange
    'secondary_base': QColor(74, 158, 255),   # Blue  
    'accent_base': QColor(0, 212, 170),      # Teal
    'purple_base': QColor(139, 92, 246),     # Purple
    'background': QColor(10, 10, 10),       # Dark background
    'highlight': QColor(255, 255, 255, 80), # Subtle highlight
    'shadow': QColor(0, 0, 0, 120)          # Subtle shadow
}

def _load_thumbnail_config():
    if THUMBNAIL_CONFIG.exists():
        try:
            with THUMBNAIL_CONFIG.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_thumbnail_config(data):
    THUMBNAIL_CONFIG.parent.mkdir(exist_ok=True)
    with THUMBNAIL_CONFIG.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_custom_thumbnail_path(visual_name):
    data = _load_thumbnail_config()
    path = data.get(visual_name)
    if path and Path(path).exists():
        return path
    return None

def set_custom_thumbnail_path(visual_name, path):
    data = _load_thumbnail_config()
    if path:
        data[visual_name] = path
    else:
        data.pop(visual_name, None)
    _save_thumbnail_config(data)

def _create_modern_gradient(painter, rect, color1, color2):
    """Create modern gradient background."""
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, color1)
    gradient.setColorAt(1.0, color2)
    return QBrush(gradient)

def _create_wave_path(width, offset=0, frequency=0.15, amplitude=0.2):
    """Create modern wave path with smooth curves."""
    from PySide6.QtGui import QPainterPath
    path = QPainterPath()
    center_y = width // 2 + offset
    
    path.moveTo(0, center_y)
    for x in range(width):
        y = center_y + amplitude * width * math.sin(x * frequency)
        path.lineTo(x, y)
    return path

def _draw_modern_particles(painter, width, height, color, count=15):
    """Draw modern particle system with subtle glow."""
    painter.setPen(Qt.PenStyle.NoPen)
    
    # Create glow effect
    glow_color = QColor(color)
    glow_color.setAlpha(60)
    painter.setBrush(QBrush(glow_color))
    
    for i in range(count):
        x = (i * 37 + 15) % width  # Pseudo-random distribution
        y = (i * 47 + 20) % height
        size = 2 + (i % 4)
        
        # Draw subtle glow
        painter.drawEllipse(int(x-1), int(y-1), size+2, size+2)
        
        # Draw main particle
        painter.setBrush(QBrush(color))
        painter.drawEllipse(int(x), int(y), size, size)
        painter.setBrush(QBrush(glow_color))

def _draw_modern_lines(painter, width, height, color1, color2, count=8):
    """Draw modern geometric lines with gradient."""
    painter.setPen(QPen(color1, 1.5))
    
    spacing = height // (count + 1)
    for i in range(count):
        y = spacing * (i + 1)
        
        # Alternate colors for depth
        if i % 2 == 0:
            painter.setPen(QPen(color1, 2))
        else:
            painter.setPen(QPen(color2, 1))
            
        # Add slight curve to lines
        start_x = 4 + (i % 3) * 2
        end_x = width - 4 - (i % 3) * 2
        painter.drawLine(start_x, y, end_x, y)

def _draw_modern_geometric(painter, width, height, color1, color2):
    """Draw modern geometric shapes with subtle effects."""
    painter.setPen(Qt.PenStyle.NoPen)
    
    # Main rectangle with gradient
    rect = QRect(8, 12, 28, 28)
    gradient_brush = _create_modern_gradient(painter, rect, color1, 
                                           QColor(color1.red(), color1.green(), color1.blue(), 180))
    painter.setBrush(gradient_brush)
    painter.drawRoundedRect(rect, 3, 3)
    
    # Modern circle with subtle border
    painter.setBrush(QBrush(color2))
    painter.drawEllipse(45, 15, 24, 24)
    
    # Inner highlight circle
    highlight = QColor(255, 255, 255, 40)
    painter.setBrush(QBrush(highlight))
    painter.drawEllipse(48, 18, 18, 18)
    
    # Modern polygon with smooth edges
    polygon = QPolygon([
        QPoint(15, 42),
        QPoint(32, 47),
        QPoint(28, 55),
        QPoint(12, 52),
    ])
    painter.setBrush(QBrush(color1))
    painter.drawPolygon(polygon)

def _draw_modern_fluid(painter, width, height, color1, color2):
    """Draw modern fluid/flow patterns."""
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Multiple wave layers for depth
    painter.setPen(QPen(color1, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(_create_wave_path(width, 0, 0.12, 0.25))
    
    painter.setPen(QPen(color2, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(_create_wave_path(width, 12, 0.18, 0.15))
    
    # Add subtle glow effect
    glow_color = QColor(color1)
    glow_color.setAlpha(30)
    painter.setPen(QPen(glow_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(_create_wave_path(width, 6, 0.15, 0.2))

def generate_visual_thumbnail(visual_name: str, width: int = 80, height: int = 60) -> QPixmap:
    """Generate a modern thumbnail pixmap for a visual with professional styling."""
    # Check for custom thumbnail first
    custom_path = get_custom_thumbnail_path(visual_name)
    if custom_path:
        pixmap = QPixmap(custom_path)
        if not pixmap.isNull():
            return pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, 
                               Qt.TransformationMode.SmoothTransformation)

    # Create modern thumbnail
    pixmap = QPixmap(width, height)
    pixmap.fill(MODERN_THUMBNAIL_COLORS['background'])

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    # Generate colors based on visual name hash
    color_hash = hash(visual_name) % 360
    primary_hue = color_hash
    secondary_hue = (color_hash + 120) % 360
    
    # Create modern color scheme
    primary_color = QColor.fromHsv(primary_hue, 200, 240)  # More vibrant
    secondary_color = QColor.fromHsv(secondary_hue, 150, 200)  # Complementary
    
    # Add subtle gradient background
    bg_rect = QRect(0, 0, width, height)
    bg_gradient = QLinearGradient(bg_rect.topLeft(), bg_rect.bottomRight())
    bg_gradient.setColorAt(0.0, QColor(15, 15, 15))
    bg_gradient.setColorAt(1.0, QColor(25, 25, 25))
    painter.fillRect(bg_rect, QBrush(bg_gradient))

    # Generate pattern based on visual name
    lower = visual_name.lower()
    
    if "particle" in lower or "spark" in lower or "dot" in lower:
        _draw_modern_particles(painter, width, height, primary_color)
        
    elif "line" in lower or "wire" in lower or "trace" in lower:
        _draw_modern_lines(painter, width, height, primary_color, secondary_color)
        
    elif "geometric" in lower or "abstract" in lower or "shape" in lower:
        _draw_modern_geometric(painter, width, height, primary_color, secondary_color)
        
    elif "fluid" in lower or "flow" in lower or "wave" in lower or "liquid" in lower:
        _draw_modern_fluid(painter, width, height, primary_color, secondary_color)
        
    elif "tunnel" in lower or "vortex" in lower or "spiral" in lower:
        # Modern tunnel/spiral effect
        painter.setPen(Qt.PenStyle.NoPen)
        center_x, center_y = width // 2, height // 2
        for i in range(8):
            radius = 5 + i * 4
            alpha = max(20, 180 - i * 20)
            color = QColor(primary_color)
            color.setAlpha(alpha)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(center_x - radius//2, center_y - radius//2, radius, radius)
            
    elif "terrain" in lower or "landscape" in lower or "mountain" in lower:
        # Modern terrain silhouette
        painter.setPen(QPen(primary_color, 2))
        painter.setBrush(QBrush(secondary_color))
        
        # Create mountain-like shape
        points = [
            QPoint(0, height - 5),
            QPoint(15, height - 25),
            QPoint(30, height - 15),
            QPoint(50, height - 35),
            QPoint(70, height - 20),
            QPoint(width, height - 10),
            QPoint(width, height),
            QPoint(0, height)
        ]
        mountain = QPolygon(points)
        painter.drawPolygon(mountain)
        
    else:
        # Default modern pattern - clean geometric design
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Main shape with gradient
        main_rect = QRect(int(width * 0.15), int(height * 0.2), 
                         int(width * 0.7), int(height * 0.6))
        gradient_brush = _create_modern_gradient(painter, main_rect, primary_color, secondary_color)
        painter.setBrush(gradient_brush)
        painter.drawRoundedRect(main_rect, 4, 4)
        
        # Overlay accent
        accent_color = QColor(255, 255, 255, 60)
        painter.setBrush(QBrush(accent_color))
        accent_rect = QRect(int(width * 0.25), int(height * 0.3), 
                           int(width * 0.5), int(height * 0.4))
        painter.drawRoundedRect(accent_rect, 2, 2)

    # Add subtle border highlight
    border_color = QColor(255, 255, 255, 40)
    painter.setPen(QPen(border_color, 1))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(1, 1, width-2, height-2, 2, 2)

    painter.end()
    return pixmap