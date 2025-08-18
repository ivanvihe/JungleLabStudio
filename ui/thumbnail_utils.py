from PyQt6.QtGui import QPixmap, QColor, QPainter, QPen, QBrush, QPolygon
from PyQt6.QtCore import QPoint, Qt
import math
from pathlib import Path
import json

THUMBNAIL_CONFIG = Path("config/custom_thumbnails.json")


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


def _create_wave_path(width, offset=0):
    from PyQt6.QtGui import QPainterPath
    path = QPainterPath()
    path.moveTo(0, width // 2 + offset)
    for x in range(width):
        y = width // 2 + offset + 0.25 * width * math.sin(x * 0.1)
        path.lineTo(x, y)
    return path


def generate_visual_thumbnail(visual_name: str, width: int = 80, height: int = 60) -> QPixmap:
    """Generate a thumbnail pixmap for a visual."""
    custom_path = get_custom_thumbnail_path(visual_name)
    if custom_path:
        pixmap = QPixmap(custom_path)
        if not pixmap.isNull():
            return pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    color_hash = hash(visual_name) % 360
    primary_color = QColor.fromHsv(color_hash, 180, 220)
    secondary_color = QColor.fromHsv((color_hash + 120) % 360, 120, 180)

    lower = visual_name.lower()
    if "particle" in lower:
        painter.setBrush(QBrush(primary_color))
        for i in range(12):
            x = (i % 4) * (width // 4) + width * 0.1
            y = (i // 4) * (height // 3) + height * 0.1
            size = 4 + (i % 3) * 2
            painter.drawEllipse(int(x), int(y), size, size)
    elif "line" in lower or "wire" in lower:
        painter.setPen(QPen(primary_color, 2))
        for i in range(6):
            y = int(i * (height / 6) + 5)
            painter.drawLine(5, y, width - 5, y)
            if i % 2 == 0:
                painter.setPen(QPen(secondary_color, 1))
            else:
                painter.setPen(QPen(primary_color, 2))
    elif "geometric" in lower or "abstract" in lower:
        painter.setBrush(QBrush(primary_color))
        painter.drawRect(10, 10, 25, 25)
        painter.setBrush(QBrush(secondary_color))
        painter.drawEllipse(45, 15, 20, 20)
        painter.setBrush(QBrush(primary_color))
        polygon = QPolygon([
            QPoint(20, 40),
            QPoint(35, 45),
            QPoint(30, 55),
            QPoint(15, 50),
        ])
        painter.drawPolygon(polygon)
    elif "fluid" in lower or "flow" in lower:
        painter.setPen(QPen(primary_color, 3))
        painter.drawPath(_create_wave_path(width, 0))
        painter.setPen(QPen(secondary_color, 2))
        painter.drawPath(_create_wave_path(width, 10))
    else:
        painter.setBrush(QBrush(primary_color))
        painter.drawRect(int(width * 0.2), int(height * 0.25), int(width * 0.6), int(height * 0.5))
        painter.setBrush(QBrush(secondary_color))
        painter.drawEllipse(int(width * 0.3), int(height * 0.33), int(width * 0.4), int(height * 0.33))

    painter.end()
    return pixmap
