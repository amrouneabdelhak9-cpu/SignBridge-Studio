"""
SignBridge Studio — Neural Translation Core
Futuristic AI Learning Dashboard (Compact)
Built with PySide6
"""

import sys
import os

# ── Backend import ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from learning_backend import backend

import math
import random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QGridLayout, QScrollArea,
    QSizePolicy, QGraphicsDropShadowEffect, QSpacerItem, QStackedWidget
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint,
    QRectF, QPointF, Signal, QThread, QSize
)
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QLinearGradient, QRadialGradient,
    QFont, QPen, QBrush, QFontDatabase, QPixmap, QConicalGradient,
    QPalette, QIcon, QPolygonF, QMovie
)
from PySide6.QtSvg import QSvgRenderer

# ── Assets path ────────────────────────────────────────────────────────────────
# Looks for: signbridge_studio/assets/signs/<module_id>/<sign_name>.gif
ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'signs')
ICONS_DIR  = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')


def get_sign_asset_path(module_id: str, sign_name: str) -> str:
    """
    Returns the full path to a sign GIF.
    sign_name like 'Good Morning' → 'good_morning.gif'
    """
    filename = sign_name.lower().replace(" ", "_").replace("'", "") + ".gif"
    return os.path.join(ASSETS_DIR, module_id, filename)


# ── Colour System ──────────────────────────────────────────────────────────────
C = {
    "bg":           "#050810",
    "surface":      "#080d1a",
    "card":         "#0b1120",
    "card2":        "#0d1526",
    "sidebar":      "#060a14",
    "border":       "#1a2540",
    "border_glow":  "#1e3a5f",
    "cyan":         "#00d4ff",
    "cyan_dim":     "#007a99",
    "cyan_glow":    "#00d4ff44",
    "teal":         "#00ffcc",
    "violet":       "#7c3aed",
    "violet_light": "#a855f7",
    "violet_glow":  "#7c3aed44",
    "magenta":      "#e040fb",
    "text_primary": "#e8f0fe",
    "text_sec":     "#6b7a99",
    "text_muted":   "#3a4a6a",
    "active_bg":    "#0d2035",
    "green":        "#00ff88",
    "amber":        "#ffaa00",
}

CARD_COLORS = [
    ("#00d4ff", "#00ffcc"),
    ("#7c3aed", "#a855f7"),
    ("#e040fb", "#7c3aed"),
    ("#00ffcc", "#00d4ff"),
    ("#f59e0b", "#ef4444"),
    ("#00d4ff", "#7c3aed"),
]

# ── Isolated Page Data Mapping (6 Category Tiles) ──────────────────────────────
CATEGORY_DATA = {
    "Greetings":  ["hello", "bye", "yes", "talk", "listen"],
    "Courtesy":   ["please", "gift", "pretty", "kiss", "think"],
    "Emergency":  ["police", "fireman", "cry", "help", "find"],
    "Basic Need": ["water", "food", "drink", "hungry", "taste"],
    "Important":  ["who", "find", "make", "finish", "go"],
    "Family":     ["mom", "brother", "uncle", "aunt", "grandpa"],
}

MODULE_ID_MAP = {
    "Greetings":  "greetings",
    "Courtesy":   "courtesy",
    "Emergency":  "emergency",
    "Basic Need": "basic_need",
    "Important":  "important",
    "Family":     "family",
}

ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


# ── Utility helpers ────────────────────────────────────────────────────────────
def hex_color(h: str) -> QColor:
    return QColor(h)


def glow_effect(widget, color: str = "#00d4ff", radius: int = 20, strength: int = 4):
    eff = QGraphicsDropShadowEffect()
    eff.setBlurRadius(radius)
    eff.setColor(QColor(color))
    eff.setOffset(0, 0)
    widget.setGraphicsEffect(eff)
    return eff


def label(text, size=11, bold=False, color=C["text_primary"], letter_spacing=0):
    lbl = QLabel(text)
    font = QFont("SF Pro Display", size)
    font.setBold(bold)
    if letter_spacing:
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, letter_spacing)
    lbl.setFont(font)
    lbl.setStyleSheet(f"color: {color}; background: transparent;")
    return lbl


# ── Animated particle background ───────────────────────────────────────────────
class ParticleCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.particles = [self._new_particle() for _ in range(40)]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)
        self._t = 0

    def _new_particle(self):
        return {
            "x": random.uniform(0, 1200),
            "y": random.uniform(0, 700),
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-0.4, -0.05),
            "r": random.uniform(0.8, 2),
            "alpha": random.uniform(0.1, 0.4),
            "color": random.choice([C["cyan"], C["violet_light"], C["teal"]]),
        }

    def _tick(self):
        self._t += 1
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["alpha"] -= 0.002
            if p["alpha"] <= 0 or p["y"] < -10:
                p.update(self._new_particle())
                p["y"] = self.height() + 10
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for p in self.particles:
            c = QColor(p["color"])
            c.setAlphaF(max(0.0, min(1.0, p["alpha"])))
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(p["x"], p["y"]), p["r"], p["r"])

        grid_color = QColor("#0a1628")
        painter.setPen(QPen(grid_color, 0.5))
        step = 50
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)

        grad = QRadialGradient(self.width() / 2, self.height() / 2,
                               max(self.width(), self.height()) * 0.7)
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(1, QColor(5, 8, 16, 180))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())


# ── Glowing animated orb ───────────────────────────────────────────────────────
class AIOrb(QWidget):
    def __init__(self, size=56, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._t = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def _tick(self):
        self._t += 1
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._size
        cx, cy = s / 2, s / 2
        t = self._t * 0.04

        ring_r = s * 0.46 + math.sin(t) * 2
        for i in range(3):
            rr = ring_r - i * 4
            alpha = int(60 - i * 15 + math.sin(t + i) * 20)
            c = QColor(C["cyan"])
            c.setAlpha(max(0, alpha))
            p.setPen(QPen(c, 1.2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), rr, rr)

        g = QRadialGradient(cx, cy, s * 0.35)
        g.setColorAt(0.0, QColor("#00d4ff"))
        g.setColorAt(0.4, QColor("#0080cc"))
        g.setColorAt(0.7, QColor("#7c3aed"))
        g.setColorAt(1.0, QColor("#050810"))
        p.setBrush(QBrush(g))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), s * 0.33, s * 0.33)

        g2 = QRadialGradient(cx - s * 0.08, cy - s * 0.08, s * 0.15)
        g2.setColorAt(0, QColor(255, 255, 255, 100))
        g2.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(g2))
        p.drawEllipse(QPointF(cx, cy), s * 0.33, s * 0.33)

        p.setPen(QPen(QColor("#00ffcc"), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        angle = int(t * 180 / math.pi * 3) % 360
        p.drawArc(
            int(cx - s * 0.38), int(cy - s * 0.38),
            int(s * 0.76), int(s * 0.76),
            angle * 16, 120 * 16
        )


# ── Glass card ─────────────────────────────────────────────────────────────────
class GlassCard(QWidget):
    def __init__(self, accent1="#00d4ff", accent2="#00ffcc", parent=None):
        super().__init__(parent)
        self._a1 = QColor(accent1)
        self._a2 = QColor(accent2)
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def _tick(self):
        target = 1.0 if self._hovered else 0.0
        self._anim += (target - self._anim) * 0.15
        self.update()
        if abs(self._anim - target) < 0.01:
            self._timer.stop()

    def enterEvent(self, e):
        self._hovered = True
        self._timer.start(16)

    def leaveEvent(self, e):
        self._hovered = False
        self._timer.start(16)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = 12

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)

        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, QColor("#0d1526"))
        bg.setColorAt(1, QColor("#08101e"))
        p.fillPath(path, QBrush(bg))

        if self._anim > 0.01:
            ov = QColor(self._a1)
            ov.setAlphaF(self._anim * 0.06)
            p.fillPath(path, QBrush(ov))

        a1 = QColor(self._a1); a1.setAlphaF(0.25 + self._anim * 0.4)
        a2 = QColor(self._a2); a2.setAlphaF(0.15 + self._anim * 0.25)
        border_g = QLinearGradient(0, 0, w, h)
        border_g.setColorAt(0, a1)
        border_g.setColorAt(1, a2)
        p.setPen(QPen(QBrush(border_g), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        shine_g = QLinearGradient(0, 0, w, 0)
        shine_c = QColor(255, 255, 255, int(25 + self._anim * 20))
        shine_g.setColorAt(0, QColor(255, 255, 255, 0))
        shine_g.setColorAt(0.5, shine_c)
        shine_g.setColorAt(1, QColor(255, 255, 255, 0))
        shine_path = QPainterPath()
        shine_path.addRoundedRect(QRectF(0, 0, w, 1.2), 0.5, 0.5)
        p.fillPath(shine_path, QBrush(shine_g))


# ── Sign category card ─────────────────────────────────────────────────────────
class SignCard(GlassCard):
    ICONS = {
        "Greetings":  os.path.join(ICONS_DIR, "person.svg"),
        "Courtesy":   os.path.join(ICONS_DIR, "courtesy.svg"),
        "Emergency":  os.path.join(ICONS_DIR, "emergency.svg"),
        "Basic Need": os.path.join(ICONS_DIR, "need.svg"),
        "Important":  os.path.join(ICONS_DIR, "important.svg"),
        "Family":     os.path.join(ICONS_DIR, "family.svg"),
    }
    COUNTS = {
        "Greetings": 5, "Courtesy": 5, "Emergency": 5,
        "Basic Need": 5, "Important": 5, "Family": 5,
    }

    clicked = Signal(str)

    def __init__(self, category, accent1, accent2, parent=None):
        super().__init__(accent1, accent2, parent)
        self._cat = category
        self._accent1 = accent1
        self.setMinimumSize(160, 140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 10)
        layout.setSpacing(6)

        # ── Category title (tag) with per-color glow ─────────────────────────
        tag = label(category.upper(), 13, color=accent1, letter_spacing=1.2)
        tag.setStyleSheet(
            f"color: {accent1}; background: transparent; letter-spacing: 1.5px;"
        )
        tag.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # Glow effect matching the tile's accent color
        glow = QGraphicsDropShadowEffect(tag)
        glow.setBlurRadius(18)
        glow.setColor(QColor(accent1))
        glow.setOffset(0, 0)
        tag.setGraphicsEffect(glow)

        # ── Icon ───────────────────────────────────────────────────────────────
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        svg_path = self.ICONS.get(category, "")
        if os.path.exists(svg_path):
            renderer = QSvgRenderer(svg_path)
            pixmap = QPixmap(40, 40)
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            icon_lbl.setPixmap(pixmap)
        else:
            icon_lbl.setText("○")
            icon_lbl.setStyleSheet(f"color: {accent1}; font-size: 20px; background: transparent;")
            icon_lbl.setFont(QFont("SF Pro Display", 20))

        # ── Words contained in this category ──────────────────────────────────
        words = CATEGORY_DATA.get(category, [])
        words_text = " · ".join(words)
        words_lbl = label(words_text, 11, color=C["text_sec"])
        words_lbl.setWordWrap(True)
        words_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        words_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # ── Sign count ────────────────────────────────────────────────────────
        count_row = QHBoxLayout()
        count_row.addStretch()
        count_lbl = label(str(self.COUNTS.get(category, 5)), 22, bold=True, color=C["text_primary"])
        count_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        count_unit = label(" signs", 12, color=C["text_sec"])
        count_unit.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        count_row.addWidget(count_lbl)
        count_row.addWidget(count_unit)
        count_row.addStretch()

        # ══ Center everything vertically ══════════════════════════════════════
        layout.addStretch()
        layout.addWidget(tag,      alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(words_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(count_row)
        layout.addStretch()

    def mousePressEvent(self, e):
        self.clicked.emit(self._cat)
        e.accept()


# ── Alphabet letter tile ───────────────────────────────────────────────────────
class LetterTile(GlassCard):
    clicked = Signal(str)

    def __init__(self, letter, accent1, accent2, parent=None):
        super().__init__(accent1, accent2, parent)
        self._letter = letter
        self.setMinimumSize(60, 60)
        self.setFixedHeight(60)

    def mousePressEvent(self, e):
        self.clicked.emit(self._letter)
        e.accept()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setFont(QFont("SF Pro Display", 28, QFont.Weight.Bold))
        p.setPen(QColor(C["text_primary"]))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self._letter)


# ══════════════════════════════════════════════════════════════════════════════
#  SIGN VIEWER — shows GIF if available, falls back to animated skeleton
# ══════════════════════════════════════════════════════════════════════════════
class SignViewer(QWidget):
    """
    Camera panel replacement that shows:
      • A GIF/image when the file exists in assets/signs/<module>/<name>.gif
      • The animated hand skeleton when no image is found (fallback)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(320)

        self._module_id  = "greetings"
        self._sign_name  = ""
        self._movie      = None   # QMovie for animated GIF

        # ── Layout: stacked so GIF and skeleton share the same space ──────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget(self)

        # Page 0 — GIF viewer ──────────────────────────────────────────────────
        self._gif_page = QWidget()
        gif_layout = QVBoxLayout(self._gif_page)
        gif_layout.setContentsMargins(8, 8, 8, 8)
        gif_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._gif_label = QLabel()
        self._gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._gif_label.setStyleSheet("background: transparent;")
        self._gif_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        gif_layout.addWidget(self._gif_label)

        # Page 1 — Fallback skeleton ───────────────────────────────────────────
        self._skeleton_page = _SkeletonFallback()

        self._stack.addWidget(self._gif_page)      # index 0
        self._stack.addWidget(self._skeleton_page) # index 1

        layout.addWidget(self._stack)

        # Corner brackets drawn on top via paintEvent
        self._t = 0
        self._scan_y = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def _tick(self):
        self._t += 1
        self._scan_y = (self._scan_y + 0.005) % 1.0
        self.update()

    def load_sign(self, module_id: str, sign_name: str):
        """Load GIF for the given sign. Falls back to skeleton if not found."""
        self._module_id = module_id
        self._sign_name = sign_name

        gif_path = get_sign_asset_path(module_id, sign_name)

        if os.path.exists(gif_path):
            # ── Stop previous movie ────────────────────────────────────────────
            if self._movie:
                self._movie.stop()
                self._movie = None

            self._movie = QMovie(gif_path)
            self._movie.setCacheMode(QMovie.CacheMode.CacheAll)
            self._gif_label.setMovie(self._movie)
            self._movie.start()

            # Scale GIF nicely inside the label
            self._movie.frameChanged.connect(self._scale_gif_frame)

            self._stack.setCurrentIndex(0)  # show GIF page
        else:
            # ── No GIF found → show animated skeleton with sign name ───────────
            if self._movie:
                self._movie.stop()
                self._movie = None
            self._skeleton_page.set_sign_name(sign_name)
            self._stack.setCurrentIndex(1)  # show skeleton page

    def _scale_gif_frame(self):
        """Keep GIF scaled to fit the label while preserving aspect ratio."""
        if self._movie and self._movie.currentPixmap():
            px = self._movie.currentPixmap()
            scaled = px.scaled(
                self._gif_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._gif_label.setPixmap(scaled)

    def paintEvent(self, e):
        """Draw corner brackets and scan line overlay on top of GIF/skeleton."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Corner brackets
        blen, bt = 16, 2
        corners = [(8, 8), (w - 8, 8), (8, h - 8), (w - 8, h - 8)]
        dirs    = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
        for (cx, cy), (dx, dy) in zip(corners, dirs):
            c = QColor(C["cyan"]); c.setAlpha(200)
            p.setPen(QPen(c, bt, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
            p.drawLine(int(cx), int(cy), int(cx + dx * blen), int(cy))
            p.drawLine(int(cx), int(cy), int(cx), int(cy + dy * blen))

        # Scan line
        sy = int(self._scan_y * h)
        scan_g = QLinearGradient(0, sy - 6, 0, sy + 6)
        scan_g.setColorAt(0,   QColor(0, 212, 255, 0))
        scan_g.setColorAt(0.5, QColor(0, 212, 255, 60))
        scan_g.setColorAt(1,   QColor(0, 212, 255, 0))
        p.fillRect(0, sy - 6, w, 12, QBrush(scan_g))
        p.setPen(QPen(QColor(0, 212, 255, 120), 1))
        p.drawLine(0, sy, w, sy)

        # Status labels
        p.setPen(QColor(C["cyan"]))
        p.setFont(QFont("SF Pro Display", 7))
        p.drawText(QRectF(10, h - 18, 100, 14), Qt.AlignmentFlag.AlignLeft, "● DETECTING")
        fps_c = QColor(C["teal"]); fps_c.setAlpha(180)
        p.setPen(fps_c)
        p.drawText(QRectF(w - 80, h - 18, 70, 14), Qt.AlignmentFlag.AlignRight, "60FPS · HD")


def _open_hand():
    return [
        (0.50, 0.90),
        (0.38, 0.78), (0.30, 0.65), (0.25, 0.52), (0.22, 0.42),
        (0.44, 0.62), (0.42, 0.42), (0.41, 0.28), (0.40, 0.18),
        (0.51, 0.60), (0.50, 0.39), (0.50, 0.25), (0.50, 0.14),
        (0.58, 0.62), (0.58, 0.42), (0.58, 0.28), (0.58, 0.18),
        (0.66, 0.67), (0.67, 0.50), (0.67, 0.38), (0.67, 0.29),
    ]

def _fist():
    return [
        (0.50, 0.90),
        (0.38, 0.78), (0.33, 0.68), (0.32, 0.60), (0.35, 0.55),
        (0.44, 0.68), (0.44, 0.60), (0.45, 0.56), (0.46, 0.54),
        (0.51, 0.67), (0.51, 0.59), (0.51, 0.55), (0.51, 0.53),
        (0.58, 0.68), (0.58, 0.60), (0.57, 0.56), (0.57, 0.54),
        (0.64, 0.70), (0.64, 0.63), (0.63, 0.59), (0.63, 0.57),
    ]

def _pointing_up():
    return [
        (0.50, 0.90),
        (0.38, 0.78), (0.33, 0.68), (0.32, 0.60), (0.35, 0.55),
        (0.46, 0.65), (0.44, 0.44), (0.43, 0.28), (0.42, 0.16),
        (0.51, 0.67), (0.51, 0.59), (0.51, 0.55), (0.51, 0.53),
        (0.58, 0.68), (0.58, 0.60), (0.57, 0.56), (0.57, 0.54),
        (0.64, 0.70), (0.64, 0.63), (0.63, 0.59), (0.63, 0.57),
    ]

def _thumb_up():
    return [
        (0.50, 0.90),
        (0.36, 0.75), (0.28, 0.60), (0.23, 0.46), (0.20, 0.33),
        (0.48, 0.68), (0.47, 0.60), (0.47, 0.56), (0.48, 0.54),
        (0.53, 0.67), (0.53, 0.59), (0.53, 0.55), (0.53, 0.53),
        (0.59, 0.68), (0.59, 0.61), (0.58, 0.57), (0.58, 0.55),
        (0.64, 0.71), (0.64, 0.64), (0.63, 0.60), (0.63, 0.58),
    ]

def _two_fingers_up():
    return [
        (0.50, 0.90),
        (0.38, 0.78), (0.33, 0.68), (0.32, 0.60), (0.35, 0.55),
        (0.44, 0.64), (0.42, 0.43), (0.41, 0.28), (0.40, 0.16),
        (0.51, 0.62), (0.50, 0.40), (0.50, 0.25), (0.50, 0.13),
        (0.58, 0.68), (0.58, 0.60), (0.57, 0.56), (0.57, 0.54),
        (0.64, 0.70), (0.64, 0.63), (0.63, 0.59), (0.63, 0.57),
    ]

def _flat_hand_forward():
    return [
        (0.50, 0.88),
        (0.37, 0.76), (0.29, 0.64), (0.24, 0.53), (0.21, 0.44),
        (0.43, 0.62), (0.41, 0.44), (0.40, 0.31), (0.39, 0.21),
        (0.50, 0.61), (0.49, 0.42), (0.49, 0.29), (0.49, 0.19),
        (0.57, 0.63), (0.57, 0.44), (0.57, 0.31), (0.57, 0.21),
        (0.64, 0.67), (0.65, 0.51), (0.65, 0.39), (0.65, 0.30),
    ]

def _c_shape():
    return [
        (0.50, 0.88),
        (0.34, 0.72), (0.26, 0.58), (0.22, 0.45), (0.21, 0.36),
        (0.40, 0.60), (0.36, 0.45), (0.34, 0.35), (0.35, 0.27),
        (0.47, 0.57), (0.44, 0.43), (0.43, 0.33), (0.44, 0.26),
        (0.54, 0.59), (0.53, 0.45), (0.52, 0.36), (0.53, 0.28),
        (0.61, 0.64), (0.62, 0.52), (0.62, 0.43), (0.63, 0.36),
    ]

def _w_shape():
    return [
        (0.50, 0.90),
        (0.37, 0.76), (0.31, 0.66), (0.30, 0.58), (0.32, 0.53),
        (0.43, 0.63), (0.41, 0.43), (0.40, 0.28), (0.39, 0.17),
        (0.50, 0.61), (0.49, 0.41), (0.49, 0.26), (0.49, 0.15),
        (0.57, 0.63), (0.57, 0.43), (0.57, 0.28), (0.57, 0.17),
        (0.64, 0.68), (0.64, 0.61), (0.63, 0.57), (0.63, 0.55),
    ]

def _pinch():
    return [
        (0.50, 0.90),
        (0.38, 0.74), (0.31, 0.61), (0.28, 0.50), (0.33, 0.43),
        (0.44, 0.63), (0.41, 0.46), (0.39, 0.38), (0.37, 0.43),
        (0.51, 0.62), (0.51, 0.55), (0.51, 0.51), (0.51, 0.49),
        (0.58, 0.64), (0.58, 0.57), (0.57, 0.53), (0.57, 0.51),
        (0.64, 0.68), (0.64, 0.62), (0.63, 0.58), (0.63, 0.56),
    ]

def _hand_to_mouth():
    return [
        (0.50, 0.88),
        (0.37, 0.72), (0.30, 0.60), (0.27, 0.50), (0.30, 0.42),
        (0.42, 0.60), (0.40, 0.45), (0.39, 0.35), (0.40, 0.28),
        (0.49, 0.59), (0.48, 0.44), (0.48, 0.34), (0.49, 0.27),
        (0.56, 0.61), (0.56, 0.46), (0.56, 0.36), (0.56, 0.29),
        (0.63, 0.66), (0.64, 0.53), (0.64, 0.43), (0.64, 0.36),
    ]

def _index_pointing_side():
    return [
        (0.50, 0.88),
        (0.37, 0.76), (0.32, 0.66), (0.30, 0.58), (0.32, 0.52),
        (0.44, 0.64), (0.55, 0.52), (0.66, 0.45), (0.76, 0.40),
        (0.51, 0.67), (0.51, 0.59), (0.51, 0.55), (0.51, 0.53),
        (0.58, 0.68), (0.58, 0.60), (0.57, 0.56), (0.57, 0.54),
        (0.64, 0.70), (0.64, 0.63), (0.63, 0.59), (0.63, 0.57),
    ]

def _both_index_cross():
    return [
        (0.50, 0.90),
        (0.38, 0.78), (0.33, 0.68), (0.32, 0.60), (0.35, 0.55),
        (0.44, 0.63), (0.46, 0.44), (0.50, 0.32), (0.53, 0.22),
        (0.51, 0.67), (0.51, 0.59), (0.51, 0.55), (0.51, 0.53),
        (0.58, 0.68), (0.58, 0.60), (0.57, 0.56), (0.57, 0.54),
        (0.64, 0.70), (0.64, 0.63), (0.63, 0.59), (0.63, 0.57),
    ]

def _hand_on_chin():
    return [
        (0.50, 0.86),
        (0.37, 0.73), (0.29, 0.61), (0.24, 0.50), (0.21, 0.41),
        (0.42, 0.60), (0.40, 0.42), (0.39, 0.29), (0.38, 0.19),
        (0.50, 0.59), (0.49, 0.41), (0.49, 0.27), (0.49, 0.17),
        (0.57, 0.61), (0.57, 0.43), (0.57, 0.30), (0.57, 0.20),
        (0.64, 0.65), (0.65, 0.49), (0.65, 0.37), (0.65, 0.28),
    ]

def _flat_b():
    return [
        (0.50, 0.90),
        (0.42, 0.76), (0.38, 0.68), (0.37, 0.62), (0.39, 0.58),
        (0.43, 0.62), (0.41, 0.42), (0.40, 0.28), (0.39, 0.17),
        (0.50, 0.61), (0.49, 0.40), (0.49, 0.26), (0.49, 0.15),
        (0.57, 0.63), (0.57, 0.42), (0.57, 0.28), (0.57, 0.17),
        (0.64, 0.67), (0.65, 0.50), (0.65, 0.38), (0.65, 0.29),
    ]

def _gift_shape():
    return [
        (0.50, 0.88),
        (0.37, 0.75), (0.31, 0.65), (0.29, 0.56), (0.31, 0.49),
        (0.42, 0.62), (0.44, 0.49), (0.47, 0.41), (0.48, 0.35),
        (0.51, 0.66), (0.51, 0.58), (0.51, 0.54), (0.51, 0.52),
        (0.58, 0.67), (0.58, 0.60), (0.57, 0.56), (0.57, 0.54),
        (0.64, 0.70), (0.64, 0.63), (0.63, 0.59), (0.63, 0.57),
    ]

def _make_shape():
    return [
        (0.50, 0.88),
        (0.38, 0.74), (0.33, 0.65), (0.32, 0.58), (0.36, 0.53),
        (0.44, 0.66), (0.44, 0.58), (0.45, 0.53), (0.46, 0.50),
        (0.51, 0.65), (0.51, 0.57), (0.51, 0.52), (0.51, 0.50),
        (0.58, 0.66), (0.58, 0.58), (0.57, 0.53), (0.57, 0.51),
        (0.64, 0.69), (0.64, 0.62), (0.63, 0.58), (0.63, 0.56),
    ]

def _grandpa_shape():
    return [
        (0.50, 0.87),
        (0.36, 0.73), (0.28, 0.60), (0.23, 0.48), (0.20, 0.38),
        (0.42, 0.59), (0.40, 0.40), (0.39, 0.27), (0.38, 0.17),
        (0.50, 0.58), (0.49, 0.38), (0.49, 0.24), (0.49, 0.13),
        (0.57, 0.60), (0.57, 0.41), (0.57, 0.27), (0.57, 0.17),
        (0.64, 0.64), (0.65, 0.48), (0.65, 0.36), (0.65, 0.27),
    ]

def _aunt_shape():
    return [
        (0.50, 0.88),
        (0.38, 0.73), (0.31, 0.62), (0.29, 0.54), (0.32, 0.48),
        (0.44, 0.65), (0.44, 0.57), (0.45, 0.52), (0.46, 0.50),
        (0.51, 0.64), (0.51, 0.56), (0.51, 0.52), (0.51, 0.50),
        (0.58, 0.65), (0.58, 0.57), (0.57, 0.53), (0.57, 0.51),
        (0.64, 0.68), (0.64, 0.61), (0.63, 0.57), (0.63, 0.55),
    ]

def _index_thumb_l():
    return [
        (0.50, 0.90),
        (0.36, 0.75), (0.27, 0.62), (0.22, 0.50), (0.19, 0.40),
        (0.44, 0.64), (0.42, 0.44), (0.41, 0.29), (0.40, 0.17),
        (0.51, 0.67), (0.51, 0.60), (0.51, 0.56), (0.51, 0.54),
        (0.58, 0.68), (0.58, 0.61), (0.57, 0.57), (0.57, 0.55),
        (0.64, 0.71), (0.64, 0.64), (0.63, 0.60), (0.63, 0.58),
    ]

def _wiping_eye():
    return [
        (0.50, 0.87),
        (0.37, 0.74), (0.31, 0.63), (0.29, 0.53), (0.31, 0.45),
        (0.43, 0.62), (0.42, 0.45), (0.41, 0.33), (0.41, 0.23),
        (0.51, 0.66), (0.51, 0.58), (0.51, 0.54), (0.51, 0.52),
        (0.58, 0.67), (0.58, 0.60), (0.57, 0.56), (0.57, 0.54),
        (0.64, 0.70), (0.64, 0.63), (0.63, 0.59), (0.63, 0.57),
    ]

def _fireman_shape():
    return [
        (0.50, 0.90),
        (0.38, 0.73), (0.32, 0.61), (0.30, 0.51), (0.35, 0.44),
        (0.44, 0.62), (0.42, 0.45), (0.40, 0.35), (0.38, 0.44),
        (0.51, 0.60), (0.50, 0.40), (0.50, 0.25), (0.50, 0.15),
        (0.57, 0.62), (0.57, 0.43), (0.57, 0.29), (0.57, 0.19),
        (0.64, 0.67), (0.65, 0.51), (0.65, 0.39), (0.65, 0.30),
    ]

def _pretty_shape():
    return [
        (0.50, 0.86),
        (0.35, 0.71), (0.27, 0.58), (0.22, 0.46), (0.19, 0.37),
        (0.41, 0.58), (0.38, 0.40), (0.37, 0.27), (0.36, 0.17),
        (0.49, 0.57), (0.48, 0.38), (0.48, 0.24), (0.48, 0.14),
        (0.56, 0.59), (0.56, 0.40), (0.56, 0.27), (0.56, 0.17),
        (0.63, 0.63), (0.64, 0.48), (0.64, 0.36), (0.65, 0.27),
    ]

def _kiss_shape():
    return [
        (0.50, 0.87),
        (0.37, 0.72), (0.30, 0.60), (0.27, 0.50), (0.31, 0.43),
        (0.43, 0.60), (0.40, 0.46), (0.38, 0.37), (0.39, 0.31),
        (0.50, 0.59), (0.48, 0.46), (0.47, 0.37), (0.48, 0.31),
        (0.57, 0.61), (0.56, 0.48), (0.55, 0.39), (0.56, 0.33),
        (0.64, 0.66), (0.64, 0.55), (0.63, 0.47), (0.64, 0.41),
    ]

# ── Master lookup ──────────────────────────────────────────────────────────────
_SIGN_POSES = {
    "hello": _open_hand,    "bye": _flat_b,          "yes": _thumb_up,
    "talk": _two_fingers_up,"listen": _pointing_up,  "please": _flat_hand_forward,
    "gift": _gift_shape,    "pretty": _pretty_shape, "kiss": _kiss_shape,
    "think": _hand_on_chin, "police": _index_thumb_l,"fireman": _fireman_shape,
    "cry": _wiping_eye,     "help": _thumb_up,       "find": _two_fingers_up,
    "water": _w_shape,      "food": _hand_to_mouth,  "drink": _c_shape,
    "hungry": _hand_to_mouth,"taste": _pinch,         "who": _pointing_up,
    "make": _make_shape,    "finish": _flat_b,       "go": _index_pointing_side,
    "mom": _hand_on_chin,   "brother": _both_index_cross, "uncle": _index_thumb_l,
    "aunt": _aunt_shape,    "grandpa": _grandpa_shape,
}

_FINGER_CONNECTIONS = [
    [0, 1, 2, 3, 4],
    [0, 5, 6, 7, 8],
    [0, 9, 10, 11, 12],
    [0, 13, 14, 15, 16],
    [0, 17, 18, 19, 20],
    [5, 9, 13, 17],
]
_TIPS = {4, 8, 12, 16, 20}


class _SkeletonFallback(QWidget):
    """Animated hand skeleton with unique per-sign poses."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._t         = 0
        self._sign_name = ""
        self._pts       = _open_hand()
        self._disp_pts  = list(self._pts)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def set_sign_name(self, name: str):
        self._sign_name = name.upper()
        pose_fn = _SIGN_POSES.get(name.lower().strip(), _open_hand)
        self._pts = pose_fn()
        self.update()

    def _tick(self):
        self._t += 1
        alpha = 0.12
        self._disp_pts = [
            (d[0] + (t[0] - d[0]) * alpha,
             d[1] + (t[1] - d[1]) * alpha)
            for d, t in zip(self._disp_pts, self._pts)
        ]
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        t = self._t * 0.04

        # Background
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor("#06101c"))
        bg.setColorAt(1, QColor("#030810"))
        p.fillRect(0, 0, w, h, QBrush(bg))

        # Grid
        p.setPen(QPen(QColor(0, 212, 255, 8), 0.5))
        for x in range(0, w, 24): p.drawLine(x, 0, x, h)
        for y in range(0, h, 24): p.drawLine(0, y, w, y)

        # Map normalised → pixels with sway/bob
        margin  = 0.10
        scale_x = w * (1 - 2 * margin)
        scale_y = h * (1 - 2 * margin)
        ox, oy  = w * margin, h * margin
        sway = math.sin(t * 0.6) * 3
        bob  = math.cos(t * 0.45) * 2

        def pt(i):
            x = ox + self._disp_pts[i][0] * scale_x + sway
            y = oy + self._disp_pts[i][1] * scale_y + bob
            return QPointF(x, y)

        # Connections
        for finger in _FINGER_CONNECTIONS:
            for j in range(len(finger) - 1):
                a, b = finger[j], finger[j + 1]
                if a >= len(self._disp_pts) or b >= len(self._disp_pts):
                    continue
                p1, p2 = pt(a), pt(b)
                seg = QLinearGradient(p1, p2)
                seg.setColorAt(0, QColor(0, 212, 255, 200))
                seg.setColorAt(1, QColor(168, 85, 247, 180))
                pen = QPen(QBrush(seg), 2.0)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.setPen(pen)
                p.drawLine(p1, p2)

        # Joints
        for i in range(min(21, len(self._disp_pts))):
            pp      = pt(i)
            is_tip  = i in _TIPS
            is_wrist = i == 0
            r       = 5.0 if is_tip else (4.0 if is_wrist else 3.0)
            color   = QColor(C["cyan"] if is_tip else (C["teal"] if is_wrist else "#7dd3fc"))
            color.setAlpha(230)
            glow = QColor(color); glow.setAlpha(40)
            p.setBrush(QBrush(glow)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(pp, r + 4, r + 4)
            p.setBrush(QBrush(color)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(pp, r, r)
            if is_tip:
                hi = QColor(255, 255, 255, 160)
                p.setBrush(QBrush(hi)); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(pp, r * 0.4, r * 0.4)

        # Sign name
        if self._sign_name:
            p.setFont(QFont("SF Pro Display", 12, QFont.Weight.Bold))
            tc = QColor(C["cyan"]); tc.setAlpha(50)
            p.setPen(tc)
            p.drawText(QRectF(0, h - 38, w, 28),
                       Qt.AlignmentFlag.AlignHCenter, self._sign_name)


# ── Gesture display (bottom info bar under camera) ─────────────────────────────
class GestureDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._t           = 0
        self._sign_name   = "HELLO"
        self._instruction = "Extend hand forward · Open palm · Wave gently"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)
        self.setFixedHeight(110)

    def update_sign(self, name: str, instruction: str):
        self._sign_name   = name.upper()
        self._instruction = instruction
        self.update()

    def _tick(self):
        self._t += 1
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        t = self._t * 0.04

        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor("#0d1a2e"))
        bg.setColorAt(1, QColor("#080f1e"))
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 12, 12)
        p.fillPath(path, QBrush(bg))
        p.setPen(QPen(QColor("#1a3050"), 1))
        p.drawPath(path)

        font = QFont("SF Pro Display", 32, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
        p.setFont(font)
        p.setPen(QColor(C["cyan"]))
        p.drawText(QRectF(0, 8, w, 48), Qt.AlignmentFlag.AlignHCenter, self._sign_name)

        p.setFont(QFont("SF Pro Display", 10))
        p.setPen(QColor(C["text_sec"]))
        p.drawText(QRectF(0, 60, w, 22), Qt.AlignmentFlag.AlignHCenter, self._instruction)

        conf  = 0.87 + math.sin(t * 1.3) * 0.05
        bar_w = w * 0.55
        bar_x = (w - bar_w) / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#0d1a2e"))
        p.drawRoundedRect(QRectF(bar_x, 88, bar_w, 6), 3, 3)
        bar_g = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
        bar_g.setColorAt(0, QColor(C["cyan"]))
        bar_g.setColorAt(1, QColor(C["violet_light"]))
        p.setBrush(QBrush(bar_g))
        p.drawRoundedRect(QRectF(bar_x, 88, bar_w * conf, 6), 3, 3)

        p.setFont(QFont("SF Pro Display", 9))
        p.setPen(QColor(C["text_sec"]))
        p.drawText(QRectF(bar_x + bar_w + 8, 82, 50, 16),
                   Qt.AlignmentFlag.AlignLeft, f"{int(conf * 100)}%")


# ── Metric pill ────────────────────────────────────────────────────────────────
class MetricPill(GlassCard):
    def __init__(self, value, label_text, color=C["cyan"], parent=None):
        super().__init__(color, C["teal"], parent)
        self._value = value
        self._label = label_text
        self._color = color
        self.setMinimumHeight(52)

    def set_value(self, value: str):
        self._value = value
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        p.setPen(QColor(self._color))
        p.drawText(QRectF(0, 4, w, 28), Qt.AlignmentFlag.AlignHCenter, self._value)
        p.setFont(QFont("SF Pro Display", 8))
        p.setPen(QColor(C["text_sec"]))
        p.drawText(QRectF(0, 32, w, 16), Qt.AlignmentFlag.AlignHCenter, self._label)


# ── Pipeline-style button (matches pipeline_test_screen.py Start/Pause) ──────────
class PipelineButton(QPushButton):
    """
    Styled QPushButton matching the Start/Pause buttons from pipeline_test_screen.py.

    variant="start"  → green gradient (like Start Detection)
    variant="pause"  → purple gradient (like Pause Stream)
    """
    def __init__(self, text, variant="start", parent=None):
        super().__init__(text, parent)
        self._variant = variant
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        self._apply_style()
        self._add_glow()

    def _apply_style(self):
        if self._variant == "start":
            self.setStyleSheet(
                "QPushButton {"
                "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "    stop:0 #00D68F, stop:1 #00FFB2);"
                "  color: #030712; border: none; border-radius: 21px;"
                "  font-size: 13px; font-weight:800; padding: 0 20px;"
                "}"
                "QPushButton:hover {"
                "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "    stop:0 #00FFB2, stop:1 #7FFFD4);"
                "}"
            )
        elif self._variant == "pause":
            self.setStyleSheet(
                "QPushButton {"
                "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "    stop:0 #6D28D9, stop:1 #9333EA);"
                "  color: white; border: none; border-radius: 21px;"
                "  font-size: 13px; font-weight:700; padding: 0 20px;"
                "}"
                "QPushButton:hover {"
                "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "    stop:0 #9333EA, stop:1 #C084FC);"
                "}"
            )
        else:
            # fallback / secondary style (cyan outline)
            self.setStyleSheet(
                f"QPushButton {{"
                f"  background:rgba(0,229,255,0.08); color:{C['cyan']};"
                f"  border:1px solid rgba(0,229,255,0.26); border-radius:21px;"
                f"  font-size:12px; font-weight:600; padding:0 14px; }}"
                f"QPushButton:hover {{"
                f"  background:rgba(0,229,255,0.17);"
                f"  border:1px solid {C['cyan']}; }}"
            )

    def _add_glow(self):
        if self._variant == "start":
            glow = QGraphicsDropShadowEffect(self)
            glow.setBlurRadius(32)
            glow.setColor(QColor(0, 255, 178, 120))
            glow.setOffset(0, 4)
            self.setGraphicsEffect(glow)
        elif self._variant == "pause":
            glow = QGraphicsDropShadowEffect(self)
            glow.setBlurRadius(32)
            glow.setColor(QColor(147, 51, 234, 120))
            glow.setOffset(0, 4)
            self.setGraphicsEffect(glow)

    def set_variant(self, variant: str):
        self._variant = variant
        self._apply_style()
        self._add_glow()


# ── Profile avatar ─────────────────────────────────────────────────────────────
class ProfileAvatar(QWidget):
    def __init__(self, size=28, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._s = size
        self._t = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: (setattr(self, '_t', self._t + 1), self.update()))
        self._timer.start(50)

    def paintEvent(self, e):
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s  = self._s
        cx, cy = s / 2, s / 2
        t  = self._t * 0.06

        ring_c = QColor(C["cyan"]); ring_c.setAlpha(150)
        p.setPen(QPen(ring_c, 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        angle = int(t * 180 / math.pi * 2) % 360
        p.drawArc(int(cx - s * 0.47), int(cy - s * 0.47),
                  int(s * 0.94), int(s * 0.94), angle * 16, 200 * 16)

        g = QRadialGradient(cx, cy, s * 0.4)
        g.setColorAt(0, QColor("#1a3050"))
        g.setColorAt(1, QColor("#0a1828"))
        p.setBrush(QBrush(g))
        p.setPen(QPen(QColor(C["cyan"]), 1))
        p.drawEllipse(QPointF(cx, cy), s * 0.38, s * 0.38)

        p.setFont(QFont("SF Pro Display", int(s * 0.28), QFont.Weight.Bold))
        p.setPen(QColor(C["text_primary"]))
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, "SB")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class LearningScreen(QMainWindow):
    sign_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SignBridge Studio — Neural Translation Core")
        self.setMinimumSize(1000, 620)
        self.resize(1200, 720)

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(C["bg"]))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(C["text_primary"]))
        self.setPalette(pal)

        # ── Localised page state ─────────────────────────────────────────────
        self._active_category = "Greetings"
        self._word_index = 0

        # ── Backend state ──────────────────────────────────────────────────────
        self._current_module = MODULE_ID_MAP[self._active_category]
        backend.start_session(self._current_module)

        # Pre-initialise pill refs so _refresh_stats is safe during UI build
        self._pill_total    = None
        self._pill_accuracy = None
        self._pill_sessions = None
        self._pill_streak   = None
        self._word_counter  = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._particles = ParticleCanvas(central)
        self._particles.lower()

        root.addWidget(self._build_main(), stretch=1)

        # ── Load first sign on startup ─────────────────────────────────────────
        self._load_current_sign()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._particles.setGeometry(self.centralWidget().rect())

    def closeEvent(self, e):
        backend.end_session(self._current_module, accuracy=0.90)
        super().closeEvent(e)

    # ── Local state & display helpers ────────────────────────────────────────

    def _refresh_display(self):
        """Update avatar, gesture bar and counter to match local category/index."""
        category = self._active_category
        words = CATEGORY_DATA[category]
        word = words[self._word_index]
        module_id = MODULE_ID_MAP[category]

        self._gesture.update_sign(word.upper(), f"Practice the sign for '{word}'")
        self._sign_viewer.load_sign(module_id, word)

        if self._word_counter is not None:
            self._word_counter.setText(f"{self._word_index + 1} / {len(words)}")

    def _on_prev_word(self):
        """Step C: decrement index with wrap-around."""
        words = CATEGORY_DATA[self._active_category]
        self._word_index = (self._word_index - 1) % len(words)
        self._refresh_display()

    def _on_next_word(self):
        """Step B: increment index with wrap-around."""
        words = CATEGORY_DATA[self._active_category]
        self._word_index = (self._word_index + 1) % len(words)
        self._refresh_display()

    def _on_alphabet_letter_clicked(self, letter: str):
        """Handle alphabet tile click — show letter in the avatar panel."""
        self._gesture.update_sign(letter, f"Practice the sign for letter '{letter}'")
        self._sign_viewer.load_sign("alphabet", letter.lower())

    def _on_essential_clicked(self):
        """Show the Essential Signs (category tiles) page."""
        self._library_stack.setCurrentIndex(0)

    def _on_alphabet_clicked(self):
        """Show the Alphabet Grid page."""
        self._library_stack.setCurrentIndex(1)

    def _show_alphabet_grid(self):
        """Switch the Sign Library panel to show the alphabet grid."""
        self._library_stack.setCurrentIndex(1)

    def _show_category_grid(self):
        """Switch the Sign Library panel back to the category grid."""
        self._library_stack.setCurrentIndex(0)

    # ── Backend helpers ────────────────────────────────────────────────────────

    def _load_current_sign(self):
        self._refresh_display()

    def _on_module_selected(self, category: str):
        """Step A: tile click updates category and resets word index to 0."""
        module_id = MODULE_ID_MAP.get(category, "greetings")
        backend.end_session(self._current_module, accuracy=0.90)

        self._current_module = module_id
        self._active_category = category
        self._word_index = 0

        backend.start_session(self._current_module)
        self._refresh_display()
        self._refresh_stats()

    def _on_next_step(self):
        """Advance to next sign using local isolated data."""
        words = CATEGORY_DATA[self._active_category]
        next_index = (self._word_index + 1) % len(words)
        self._word_index = next_index
        self._refresh_display()
        self._refresh_stats()
        if next_index == 0:
            self._gesture.update_sign("COMPLETE!", "All signs in this module learned!")

    def _on_relearn(self):
        """Reset progress for the current module and restart from the first word."""
        self._word_index = 0
        self._refresh_display()

    def _refresh_stats(self):
        if self._pill_total is None:
            return  # UI not fully built yet
        stats = backend.get_stats()
        self._pill_total.set_value(str(stats["total_signs_learned"]))
        self._pill_accuracy.set_value(f"{stats['accuracy_rate']}%")
        self._pill_sessions.set_value(str(stats["sessions_completed"]))
        self._pill_streak.set_value(f"{stats['streak']}🔥")

    # ── UI builders ────────────────────────────────────────────────────────────

    def _build_main(self):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_content(), stretch=1)
        return container

    def _build_header(self):
        hdr = QWidget()
        hdr.setFixedHeight(60)
        hdr.setStyleSheet(f"background: rgba(6,10,20,0.92); border-bottom: 1px solid {C['border']};")
        row = QHBoxLayout(hdr)
        row.setContentsMargins(20, 0, 20, 0)
        row.setSpacing(6)

        # ── Vibrant title — larger, cyan, glowing, no subtitle ───────────────
        title = QLabel("LEARNING STUDIO")
        font = QFont("SF Pro Display", 22, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        title.setFont(font)
        title.setStyleSheet(f"color: {C['cyan']}; background: transparent;")
        glow_effect(title, color=C["cyan"], radius=28, strength=5)
        row.addWidget(title)

        row.addStretch()
        row.addWidget(ProfileAvatar(32))
        return hdr

    def _build_content(self):
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        row = QHBoxLayout(content)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)
        row.addWidget(self._build_sign_library(), stretch=5)
        row.addWidget(self._build_camera_panel(), stretch=4)
        return content

    def _build_sign_library(self):
        panel = GlassCard(C["cyan"], C["teal"])
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # ── Stacked widget: Page 0 = categories, Page 1 = alphabet ────────────
        self._library_stack = QStackedWidget()
        self._library_stack.addWidget(self._build_category_page())
        self._library_stack.addWidget(self._build_alphabet_page())
        layout.addWidget(self._library_stack, stretch=1)

        # ── Bottom toggle buttons (pipeline_test_screen.py style) ─────────────
        brow = QHBoxLayout()
        brow.setSpacing(10)
        self._essential_btn = PipelineButton("Essential Signs", variant="start")
        self._alphabet_btn = PipelineButton("Alphabet Grid", variant="pause")
        self._essential_btn.clicked.connect(self._on_essential_clicked)
        self._alphabet_btn.clicked.connect(self._on_alphabet_clicked)
        brow.addWidget(self._essential_btn, stretch=1)
        brow.addWidget(self._alphabet_btn, stretch=1)
        layout.addLayout(brow)

        return panel

    def _build_category_page(self):
        """Page 0: The original 6 category tiles."""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        vlayout = QVBoxLayout(page)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(8)

        hrow = QHBoxLayout()
        title = label("Sign Library", 13, bold=True, color=C["text_primary"])
        title.setFont(QFont("SF Pro Display", 13, QFont.Weight.Bold))
        hrow.addWidget(title)
        hrow.addStretch()
        vlayout.addLayout(hrow)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        categories = ["Greetings", "Courtesy", "Emergency", "Basic Need", "Important", "Family"]
        for i, (cat, (c1, c2)) in enumerate(zip(categories, CARD_COLORS)):
            card = SignCard(cat, c1, c2)
            card.clicked.connect(self.sign_selected.emit)
            card.clicked.connect(self._on_module_selected)
            grid.addWidget(card, i // 3, i % 3)

        scroll.setWidget(grid_widget)
        vlayout.addWidget(scroll, stretch=1)

        return page

    def _build_alphabet_page(self):
        """Page 1: A-Z letter tiles with a back button."""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        vlayout = QVBoxLayout(page)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(8)

        # Header with back button
        hrow = QHBoxLayout()
        back_btn = PipelineButton("← Back", variant="secondary")
        back_btn.setFixedWidth(80)
        back_btn.clicked.connect(self._show_category_grid)
        title = label("Alphabet Grid", 13, bold=True, color=C["text_primary"])
        title.setFont(QFont("SF Pro Display", 13, QFont.Weight.Bold))
        hrow.addWidget(back_btn)
        hrow.addWidget(title)
        hrow.addStretch()
        vlayout.addLayout(hrow)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        # Cycle through accent colors for visual variety
        for i, letter in enumerate(ALPHABET):
            c1, c2 = CARD_COLORS[i % len(CARD_COLORS)]
            tile = LetterTile(letter, c1, c2)
            tile.clicked.connect(self._on_alphabet_letter_clicked)
            grid.addWidget(tile, i // 4, i % 4)

        scroll.setWidget(grid_widget)
        vlayout.addWidget(scroll, stretch=1)

        return page

    def _build_camera_panel(self):
        panel = GlassCard(C["violet"], C["cyan"])
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header
        hrow = QHBoxLayout()
        cam_lbl = label("Active Sign", 12, bold=True, color=C["text_primary"])
        cam_lbl.setFont(QFont("SF Pro Display", 12, QFont.Weight.Bold))
        fs_btn = QLabel("⛶")
        fs_btn.setFont(QFont("SF Pro Display", 12))
        fs_btn.setStyleSheet(f"color:{C['text_sec']}; background:transparent;")
        fs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        hrow.addWidget(cam_lbl)
        hrow.addStretch()
        hrow.addWidget(fs_btn)
        layout.addLayout(hrow)

        # ── Avatar Visual Box ─────────────────────────────────────────────────
        self._sign_viewer = SignViewer()
        viewer_frame = QWidget()
        viewer_frame.setStyleSheet(f"background:#04080f; border:1px solid {C['border_glow']}; border-radius:10px;")
        vf_layout = QVBoxLayout(viewer_frame)
        vf_layout.setContentsMargins(0, 0, 0, 0)
        vf_layout.addWidget(self._sign_viewer)
        layout.addWidget(viewer_frame, stretch=1)

        # ── Navigation Controls (Left / Right Arrows) ─────────────────────────
        nav_row = QHBoxLayout()
        nav_row.setSpacing(10)

        self._prev_btn = PipelineButton("<", variant="secondary")
        self._prev_btn.setFixedWidth(44)
        self._prev_btn.clicked.connect(self._on_prev_word)

        self._word_counter = QLabel("1 / 5")
        self._word_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._word_counter.setFont(QFont("SF Pro Display", 9, QFont.Weight.Medium))
        self._word_counter.setStyleSheet(f"color:{C['text_sec']}; background:transparent;")

        self._next_btn = PipelineButton(">", variant="secondary")
        self._next_btn.setFixedWidth(44)
        self._next_btn.clicked.connect(self._on_next_word)

        nav_row.addStretch()
        nav_row.addWidget(self._prev_btn)
        nav_row.addWidget(self._word_counter)
        nav_row.addWidget(self._next_btn)
        nav_row.addStretch()
        layout.addLayout(nav_row)

        # ── Gesture info bar ──────────────────────────────────────────────────
        self._gesture = GestureDisplay()
        layout.addWidget(self._gesture)

        # Status indicators
        ind_row = QHBoxLayout()
        for txt, col in [("◉ ACTIVE", C["cyan"]), ("HD", C["teal"]), ("READY", C["green"])]:
            lbl = QLabel(txt)
            lbl.setFont(QFont("SF Pro Display", 7, QFont.Weight.Medium))
            lbl.setStyleSheet(f"color:{col}; background:transparent; border:1px solid {col}40; border-radius:3px; padding:2px 6px;")
            ind_row.addWidget(lbl)
        ind_row.addStretch()
        layout.addLayout(ind_row)

        return panel


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SignBridge Studio")
    app.setStyle("Fusion")

    dark = QPalette()
    dark.setColor(QPalette.ColorRole.Window,          QColor(C["bg"]))
    dark.setColor(QPalette.ColorRole.WindowText,      QColor(C["text_primary"]))
    dark.setColor(QPalette.ColorRole.Base,            QColor(C["surface"]))
    dark.setColor(QPalette.ColorRole.AlternateBase,   QColor(C["card"]))
    dark.setColor(QPalette.ColorRole.Text,            QColor(C["text_primary"]))
    dark.setColor(QPalette.ColorRole.Button,          QColor(C["card"]))
    dark.setColor(QPalette.ColorRole.ButtonText,      QColor(C["text_primary"]))
    dark.setColor(QPalette.ColorRole.Highlight,       QColor(C["cyan"]))
    dark.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
    app.setPalette(dark)

    win = LearningScreen()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()