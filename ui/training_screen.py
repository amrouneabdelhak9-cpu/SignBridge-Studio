# ui/training_screen.py
"""
SignBridge Studio — Training Screen  (World-Class Futuristic AI Dashboard)
==========================================================================
Ultra-modern, cinematic dark luxury interface.
Glassmorphism · Ambient glow · Premium SaaS aesthetic.

Dependencies: PySide6
"""

from __future__ import annotations

import math

from PySide6.QtCore import (
    QEasingCurve, QPoint, QPropertyAnimation, QRect, QRectF,
    QSequentialAnimationGroup, QSize, Qt, QTimer, Signal,
    Property, QObject,
)
from PySide6.QtGui import (
    QBrush, QColor, QConicalGradient, QFont, QFontDatabase,
    QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication, QDialog, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)

# ─────────────────────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────────────────────
BG_VOID       = "#050816"      # deepest background
BG_PANEL      = "#07111F"      # panel background
BG_INNER      = "#0A1628"      # inner card background
BG_CANVAS     = "#060D1A"      # camera canvas
BORDER_GLOW   = "rgba(0, 224, 255, 0.12)"
BORDER_FAINT  = "rgba(255, 255, 255, 0.04)"

CYAN          = "#00E0FF"
CYAN_BRIGHT   = "#40EEFF"
CYAN_DIM      = "#00B8D9"
TEAL          = "#00C9B1"
GREEN_LIVE    = "#00E676"
AMBER         = "#FF6B35"
AMBER_HOT     = "#FF3D00"

TEXT_PRIME    = "#EFF6FF"
TEXT_SEC      = "#7A99BC"
TEXT_MUTED    = "#3D5470"
TEXT_LABEL    = "#4A6880"

FONT_HEAD     = "SF Pro Display, Helvetica Neue, Arial, sans-serif"
FONT_BODY     = "SF Pro Text, Helvetica Neue, Arial, sans-serif"
FONT_MONO     = "JetBrains Mono, Fira Code, monospace"


# ─────────────────────────────────────────────────────────────
#  UTILITIES
# ─────────────────────────────────────────────────────────────
def _shadow(widget: QWidget,
            color: QColor,
            blur: int = 32,
            dx: int = 0,
            dy: int = 0) -> QGraphicsDropShadowEffect:
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(blur)
    fx.setColor(color)
    fx.setOffset(dx, dy)
    widget.setGraphicsEffect(fx)
    return fx


def _label(text: str,
           size: int = 13,
           color: str = TEXT_SEC,
           weight: int = 400,
           spacing: float = 0.3) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {color};"
        f"font-size: {size}px;"
        f"font-weight: {weight};"
        f"letter-spacing: {spacing}px;"
        f"background: transparent;"
    )
    lbl.setWordWrap(True)
    return lbl


def _divider() -> QFrame:
    d = QFrame()
    d.setFrameShape(QFrame.HLine)
    d.setFixedHeight(1)
    d.setStyleSheet("background: rgba(0, 200, 255, 0.07); border: none;")
    return d


# ─────────────────────────────────────────────────────────────
#  ANIMATED PULSE CANVAS  (center empty-state visualization)
# ─────────────────────────────────────────────────────────────
class _PulseCanvas(QWidget):
    """
    Draws a layered ambient visualization:
    – Subtle dot-grid texture
    – Three slow-breathing radial rings
    – Rotating dual arc
    – Glowing hand icon at center
    """

    def set_pixmap(self, pixmap) -> None:
        """Store the camera frame and trigger a repaint."""
        self._camera_frame = pixmap
        self.update()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._camera_frame = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(320)
        self._angle: float = 0.0
        self._pulse: float = 0.0
        self._pulse_dir: int = 1

        tick = QTimer(self)
        tick.timeout.connect(self._tick)
        tick.start(28)   # ~36 fps — smooth but light

    def _tick(self) -> None:
        self._angle = (self._angle + 0.45) % 360
        self._pulse += 0.025 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse_dir = 1
        self.update()

    # ── painting ──────────────────────────────────────────────
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ── Define these FIRST so they exist for both paths ──
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # ── Camera frame path ──
        if self._camera_frame is not None:
            scaled = self._camera_frame.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
            p.end()
            return

        # ── Animation path (existing code unchanged) ──
        # 1. dot grid
        dot_color = QColor(0, 200, 255, 10)
        p.setPen(QPen(dot_color, 1.5))
        step = 28
        for gx in range(0, w, step):
            for gy in range(0, h, step):
                p.drawPoint(gx, gy)

        # 2. radial rings ...
        # ... rest of your existing code unchanged

        # 2. radial rings (breathing)
        for i, (base_r, base_a) in enumerate([(130, 18), (195, 10), (265, 5)]):
            alpha = int(base_a * (0.55 + 0.45 * self._pulse)) if i == 0 else base_a
            r = base_r + (6 * self._pulse if i == 0 else 0)
            pen = QPen(QColor(0, 224, 255, alpha), 1.0 if i else 1.5)
            pen.setStyle(Qt.DashLine if i == 2 else Qt.SolidLine)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # 3. rotating accent arc
        p.save()
        p.translate(cx, cy)
        p.rotate(self._angle)
        arc_r = 155
        arc_rect = QRectF(-arc_r, -arc_r, arc_r * 2, arc_r * 2)
        arc_pen = QPen(QColor(0, 224, 255, 80), 1.5)
        arc_pen.setCapStyle(Qt.RoundCap)
        p.setPen(arc_pen)
        p.drawArc(arc_rect, 0, 80 * 16)
        p.drawArc(arc_rect, 180 * 16, 60 * 16)

        p.rotate(-self._angle * 2)
        arc2_r = 180
        arc2_rect = QRectF(-arc2_r, -arc2_r, arc2_r * 2, arc2_r * 2)
        p.setPen(QPen(QColor(0, 180, 200, 35), 1.0))
        p.drawArc(arc2_rect, 30 * 16, 40 * 16)
        p.drawArc(arc2_rect, 200 * 16, 55 * 16)
        p.restore()

        # 4. center glow
        glow = QRadialGradient(cx, cy, 80)
        glow.setColorAt(0.0, QColor(0, 224, 255, int(28 + 14 * self._pulse)))
        glow.setColorAt(1.0, QColor(0, 224, 255, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(cx - 80, cy - 80, 160, 160))

        # 5. hand icon
        self._draw_hand(p, int(cx), int(cy))

        # 6. status text below icon
        p.setPen(QColor(TEXT_PRIME))
        f = QFont("Helvetica Neue, Arial", 18)
        f.setWeight(QFont.Weight.DemiBold)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        p.setFont(f)
        p.drawText(QRect(int(cx - 180), int(cy + 56), 360, 32),
                   Qt.AlignCenter, "Stream Ready")

        p.setPen(QColor(TEXT_SEC))
        f2 = QFont("Helvetica Neue, Arial", 12)
        p.setFont(f2)
        p.drawText(QRect(int(cx - 200), int(cy + 92), 400, 22),
                   Qt.AlignCenter, "The system is ready to record a new stream.")

        p.end()

    @staticmethod
    def _draw_hand(p: QPainter, cx: int, cy: int) -> None:
        """Minimal vector hand outline — centered at (cx, cy-12)."""
        s = 52
        ox, oy = cx - s // 2, cy - s // 2 - 12

        pen = QPen(QColor(CYAN), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        fw = int(s * 0.11)
        fh_map = [
            (int(s * 0.28), int(s * 0.18), fw, int(s * 0.30)),
            (int(s * 0.40), int(s * 0.10), fw, int(s * 0.36)),
            (int(s * 0.52), int(s * 0.18), fw, int(s * 0.30)),
            (int(s * 0.63), int(s * 0.26), int(fw * 0.9), int(s * 0.22)),
        ]
        for (fx, fy, fw2, fh) in fh_map:
            p.drawRoundedRect(ox + fx, oy + fy, fw2, fh, 3, 3)

        # palm
        p.drawRoundedRect(ox + int(s * 0.22), oy + int(s * 0.46),
                          int(s * 0.52), int(s * 0.40), 6, 6)
        # thumb
        p.drawRoundedRect(ox + int(s * 0.08), oy + int(s * 0.50),
                          int(s * 0.14), int(s * 0.16), 3, 3)


# ─────────────────────────────────────────────────────────────
#  STAT DOCK ITEM
# ─────────────────────────────────────────────────────────────
class _StatItem(QWidget):
    def __init__(self, icon_char: str, label: str, value: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)

        top = QHBoxLayout()
        top.setSpacing(6)

        ico = QLabel(icon_char)
        ico.setStyleSheet(f"color: {CYAN_DIM}; font-size: 11px;")
        top.addWidget(ico)

        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"color: {TEXT_LABEL}; font-size: 9px; font-weight: 700;"
            f"letter-spacing: 1.2px; background: transparent;"
        )
        top.addWidget(lbl)
        lay.addLayout(top)

        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(
            f"color: {TEXT_PRIME}; font-size: 14px; font-weight: 600;"
            f"letter-spacing: 0.2px; background: transparent;"
        )
        lay.addWidget(self.val_lbl)

    def set_value(self, v: str) -> None:
        self.val_lbl.setText(v)


# ─────────────────────────────────────────────────────────────
#  BOTTOM STATS DOCK
# ─────────────────────────────────────────────────────────────
class _StatsDock(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(72)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(5, 14, 28, 0.75);
                border: 1px solid {BORDER_GLOW};
                border-radius: 16px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 12, 24, 12)
        lay.setSpacing(0)

        self._frames = _StatItem("⬡", "Frames Stacked", "0 / 100")
        self._target = _StatItem("◎", "Active Target", "—")

        lay.addWidget(self._frames, 1)
        lay.addWidget(_StatItem._vline(), 0)
        lay.addWidget(self._target, 1)

    @property
    def frames_stat(self) -> _StatItem:
        return self._frames

    @property
    def target_stat(self) -> _StatItem:
        return self._target

    # thin vertical divider helper (reused here)
    @staticmethod
    def _vline_widget() -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.VLine)
        f.setFixedWidth(1)
        f.setStyleSheet("background: rgba(0,200,255,0.08); border: none;")
        return f


# patch the vertical line back onto _StatItem for dock usage
_StatItem._vline = _StatsDock._vline_widget  # type: ignore[attr-defined]


# ─────────────────────────────────────────────────────────────
#  PREMIUM BUTTON  (primary cyan fill)
# ─────────────────────────────────────────────────────────────
class _PrimaryBtn(QPushButton):
    _STYLE_IDLE = f"""
        QPushButton {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {CYAN_DIM}, stop:1 {TEAL}
            );
            color: #010D16;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.4px;
            border: none;
            border-radius: 14px;
            padding: 0 24px;
        }}
        QPushButton:hover {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {CYAN_BRIGHT}, stop:1 {CYAN}
            );
        }}
        QPushButton:pressed {{
            background: {CYAN_DIM};
        }}
    """
    _STYLE_ACTIVE = f"""
        QPushButton {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {AMBER_HOT}, stop:1 {AMBER}
            );
            color: #fff;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.4px;
            border: none;
            border-radius: 14px;
            padding: 0 24px;
        }}
        QPushButton:hover {{
            background: {AMBER_HOT};
        }}
    """

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setFixedHeight(52)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self._STYLE_IDLE)
        _shadow(self, QColor(0, 200, 200, 90), blur=28, dy=6)

    def set_active(self, active: bool, label: str) -> None:
        self.setText(label)
        self.setStyleSheet(self._STYLE_ACTIVE if active else self._STYLE_IDLE)


# ─────────────────────────────────────────────────────────────
#  SECONDARY BUTTON  (outline teal)
# ─────────────────────────────────────────────────────────────
class _SecondaryBtn(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setFixedHeight(52)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEAL};
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 0.4px;
                border: 1.5px solid {TEAL};
                border-radius: 14px;
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background: rgba(0, 201, 177, 0.08);
                border-color: {CYAN};
                color: {CYAN};
            }}
            QPushButton:pressed {{
                background: rgba(0, 201, 177, 0.14);
            }}
        """)


# ─────────────────────────────────────────────────────────────
#  SIDEBAR CARD  (glassmorphic)
# ─────────────────────────────────────────────────────────────
class _SideCard(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(7, 17, 31, 0.55);
                border: none;
                border-radius: 20px;
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(22, 20, 22, 20)
        self._layout.setSpacing(22)

    def add(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_layout(self, lay) -> None:
        self._layout.addLayout(lay)

    def add_stretch(self) -> None:
        self._layout.addStretch()


# ─────────────────────────────────────────────────────────────
#  SIGN NAMING DIALOG
# ─────────────────────────────────────────────────────────────
class SignNamingDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(420)
        self.setStyleSheet(f"""
            QDialog {{
                background: {BG_INNER};
                border: 1px solid rgba(0, 224, 255, 0.25);
                border-radius: 20px;
            }}
        """)
        _shadow(self, QColor(0, 224, 255, 40), blur=60)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(20)

        # header row
        hdr_row = QHBoxLayout()
        badge = QLabel("◈")
        badge.setStyleSheet(f"color: {CYAN}; font-size: 14px;")
        hdr_row.addWidget(badge)
        title = QLabel("Name Active Target")
        title.setStyleSheet(f"color: {TEXT_PRIME}; font-size: 16px; font-weight: 700; letter-spacing: 0.3px;")
        hdr_row.addWidget(title)
        hdr_row.addStretch()
        lay.addLayout(hdr_row)

        sub = QLabel("Enter a label for this sign recording sequence.")
        sub.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; letter-spacing: 0.2px;")
        lay.addWidget(sub)

        self._input = QLineEdit()
        self._input.setPlaceholderText("e.g.,  Hello · Thank You · Dynamic Gesture")
        self._input.setFixedHeight(46)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(5, 8, 22, 0.80);
                color: {TEXT_PRIME};
                border: 1px solid rgba(0, 224, 255, 0.18);
                border-radius: 10px;
                padding: 0 16px;
                font-size: 14px;
                letter-spacing: 0.2px;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(0, 224, 255, 0.55);
            }}
        """)
        lay.addWidget(self._input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(42)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SEC};
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.04);
                color: {TEXT_PRIME};
            }}
        """)
        cancel.clicked.connect(self.reject)

        save = QPushButton("Confirm Label")
        save.setFixedHeight(42)
        save.setCursor(Qt.PointingHandCursor)
        save.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {CYAN_DIM}, stop:1 {TEAL});
                color: #010D16;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{
                background: {CYAN_BRIGHT};
            }}
        """)
        save.clicked.connect(self.accept)

        btn_row.addWidget(cancel, 1)
        btn_row.addWidget(save, 1)
        lay.addLayout(btn_row)

    def get_input_text(self) -> str:
        return self._input.text()


# ─────────────────────────────────────────────────────────────
#  STATUS INDICATOR ROW  (live dot + text)
# ─────────────────────────────────────────────────────────────
class _StatusBadge(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self._dot = QLabel("●")
        self._dot.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: transparent; border: none;")
        lay.addWidget(self._dot)

        self._text = QLabel("SYSTEM IDLE")
        self._text.setStyleSheet(
            f"color: {TEXT_PRIME}; font-size: 13px; font-weight: 700;"
            f"letter-spacing: 1.8px; background: transparent; border: none;"
        )
        lay.addWidget(self._text)
        lay.addStretch()

    def set_idle(self) -> None:
        self._dot.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: transparent; border: none;")
        self._text.setText("SYSTEM IDLE")
        self._text.setStyleSheet(
            f"color: {TEXT_PRIME}; font-size: 13px; font-weight: 700;"
            f"letter-spacing: 1.8px; background: transparent; border: none;"
        )

    def set_recording(self) -> None:
        self._dot.setStyleSheet(f"color: {AMBER}; font-size: 11px; background: transparent; border: none;")
        self._text.setText("RECORDING INSTANCE")
        self._text.setStyleSheet(
            f"color: {AMBER}; font-size: 13px; font-weight: 700;"
            f"letter-spacing: 1.8px; background: transparent; border: none;"
        )


# ─────────────────────────────────────────────────────────────
#  SIDEBAR GLOWING STATUS DOT
# ─────────────────────────────────────────────────────────────
class _GlowDot(QWidget):
    def __init__(self, color: str = GREEN_LIVE,
                 size: int = 8,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.width() / 2
        grad = QRadialGradient(r, r, r)
        grad.setColorAt(0.0, self._color)
        grad.setColorAt(1.0, QColor(self._color.red(),
                                    self._color.green(),
                                    self._color.blue(), 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, self.width(), self.height())
        p.end()


# ─────────────────────────────────────────────────────────────
#  SIDEBAR SECTION HEADER
# ─────────────────────────────────────────────────────────────
def _section_header(title: str,
                    dot_color: str = CYAN,
                    show_dot: bool = True) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(8)
    if show_dot:
        d = _GlowDot(dot_color, size=7)
        row.addWidget(d, 0, Qt.AlignVCenter)
    lbl = QLabel(title.upper())
    lbl.setStyleSheet(
        f"color: {TEXT_PRIME}; font-size: 14px; font-weight: 700;"
        f"letter-spacing: 1.4px; background: transparent;"
    )
    row.addWidget(lbl)
    row.addStretch()
    return row


# ─────────────────────────────────────────────────────────────
#  SIDEBAR STATUS ROW
# ─────────────────────────────────────────────────────────────
def _status_row(key: str, value: str) -> QWidget:
    w = QWidget()
    w.setAttribute(Qt.WA_StyledBackground, True)
    w.setStyleSheet("background: transparent;")
    row = QHBoxLayout(w)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(8)

    k = QLabel(key)
    k.setStyleSheet(
        f"color: {TEXT_SEC}; font-size: 14px; font-weight: 500;"
        f"letter-spacing: 0.4px; background: transparent;"
    )
    row.addWidget(k)
    row.addStretch()

    v = QLabel(value)
    v.setStyleSheet(
        f"color: {TEXT_PRIME}; font-size: 14px; font-weight: 600;"
        f"letter-spacing: 0.2px; background: transparent;"
    )
    row.addWidget(v)
    return w


# ─────────────────────────────────────────────────────────────
#  MAIN TRAINING SCREEN
# ─────────────────────────────────────────────────────────────
class TrainingScreen(QWidget):
    data_capture_toggled = Signal(bool)
    training_triggered   = Signal()
    sign_label_assigned = Signal(str)
    camera_stop_requested = Signal()   # ← NEW

    def set_live_frame(self, pixmap) -> None:
        """Display live camera feed on the canvas."""
        self._canvas.set_pixmap(pixmap)
        # Show stop-camera button as soon as the first frame arrives
        if pixmap is not None and hasattr(self, 'btn_stop_cam') and self.btn_stop_cam.isHidden():
            self.btn_stop_cam.show()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("training_screen")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(f"""
            QWidget#training_screen {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BG_VOID}, stop:1 #050E1A
                );
            }}
        """)
        self._capturing       = False
        self._frames_captured = 0
        self._target_label    = "—"
        self._build()

    # ── build layout ──────────────────────────────────────────
    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)

        root.addLayout(self._build_left(), 70)
        root.addLayout(self._build_right(), 30)

    # ── LEFT COLUMN ───────────────────────────────────────────
    def _build_left(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(16)

        # ── main camera frame ──────────────────────────────
        cam_frame = QFrame()
        cam_frame.setAttribute(Qt.WA_StyledBackground, True)
        cam_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cam_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(7, 15, 30, 0.72);
                border: 1px solid {BORDER_GLOW};
                border-radius: 24px;
            }}
        """)
        _shadow(cam_frame, QColor(0, 200, 255, 18), blur=48, dy=8)

        cam_lay = QVBoxLayout(cam_frame)
        cam_lay.setContentsMargins(22, 18, 22, 18)
        cam_lay.setSpacing(14)

        # top header row
        hdr = QHBoxLayout()
        self._status_badge = _StatusBadge()
        hdr.addWidget(self._status_badge)
        hdr.addStretch()

        self._target_pill_lbl = QLabel("No Active Target")
        self._target_pill_lbl.setStyleSheet(
            f"color: {TEXT_SEC}; font-size: 13px; font-weight: 600;"
            f"letter-spacing: 0.4px; background: transparent; border: none;"
        )
        hdr.addWidget(self._target_pill_lbl)
        cam_lay.addLayout(hdr)

        # pulse canvas (main center visualization)
        self._canvas = _PulseCanvas()
        cam_lay.addWidget(self._canvas, 1)

        # bottom stats dock
        self._dock = _StatsDock()
        cam_lay.addWidget(self._dock)

        col.addWidget(cam_frame, 1)

        # ── action buttons ─────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        self.btn_record = _PrimaryBtn("Start Recording")
        self.btn_record.clicked.connect(self._toggle_capture)
        btn_row.addWidget(self.btn_record, 1)

        self.btn_train = _SecondaryBtn("Train Dataset Model")
        self.btn_train.clicked.connect(self._start_training)
        btn_row.addWidget(self.btn_train, 1)

        # ═══════════════════════════════════════════════════════════════════════
        # NEW: Stop Camera button — force release camera immediately
        # ═══════════════════════════════════════════════════════════════════════
        self.btn_stop_cam = _SecondaryBtn("⏹ Stop Camera")
        self.btn_stop_cam.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: #ff5252;
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 0.4px;
                border: 1.5px solid #ff5252;
                border-radius: 14px;
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background: rgba(255, 82, 82, 0.08);
                border-color: #ff784e;
                color: #ff784e;
            }}
        """)
        self.btn_stop_cam.clicked.connect(self._force_stop_camera)
        self.btn_stop_cam.hide()  # Hidden until camera starts
        btn_row.addWidget(self.btn_stop_cam, 1)
        # ═══════════════════════════════════════════════════════════════════════

        col.addLayout(btn_row)
        return col

    # ── RIGHT SIDEBAR ─────────────────────────────────────────
    def _build_right(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(16)

        # ── Dataset Profile card ───────────────────────────
        ds_card = _SideCard()
        _shadow(ds_card, QColor(0, 200, 255, 12), blur=30, dy=4)

        ds_card.add_layout(_section_header("Dataset Profile", dot_color=GREEN_LIVE))
        ds_card.add(_divider())

        self._ds_content = _label(
            "Awaiting live stream capture sequence.",
            size=15, color=TEXT_PRIME
        )
        ds_card.add(self._ds_content)

        # status rows
        ds_card.add(_status_row("Sequences",   "0"))
        ds_card.add(_status_row("Token Classes", "—"))
        ds_card.add(_status_row("Last Capture", "—"))
        ds_card.add_stretch()
        col.addWidget(ds_card)

        # ── Model Engine Status card ───────────────────────
        eng_card = _SideCard()
        _shadow(eng_card, QColor(0, 160, 255, 10), blur=30, dy=4)

        eng_card.add_layout(_section_header("Model Engine Status", dot_color=CYAN_DIM))
        eng_card.add(_divider())

        self._eng_content = _label(
            "Pipeline resting. Provide custom vector parameters to execute optimization algorithms.",
            size=15, color=TEXT_PRIME
        )
        eng_card.add(self._eng_content)

        eng_card.add(_status_row("Runtime",       "—"))
        eng_card.add(_status_row("Architecture",  "CNN · LSTM"))
        eng_card.add(_status_row("Accuracy",      "—"))
        eng_card.add(_status_row("Optimizer",     "Adam"))
        eng_card.add(_status_row("Learning Rate", "1e-3"))

        eng_card.add_stretch()
        col.addWidget(eng_card, 1)

        return col

    # ── INTERACTIONS ──────────────────────────────────────────
    def _toggle_capture(self) -> None:
        self._capturing = not self._capturing

        if self._capturing:
            self.btn_record.set_active(True, "Stop Sequence")
            self._status_badge.set_recording()
            self.data_capture_toggled.emit(True)
        else:
            self.btn_record.set_active(False, "Start Recording")
            self._status_badge.set_idle()
            self.data_capture_toggled.emit(False)

            dlg = SignNamingDialog(self)
            if dlg.exec() == QDialog.Accepted:
                name = dlg.get_input_text().strip()
                if name:
                    self._add_sign(name)
                else:
                    self._ds_content.setText("Sequence aborted: label cannot be blank.")
                    self._ds_content.setStyleSheet(
                        f"color: {AMBER}; font-size: 15px; word-wrap: true;"
                    )

    def _start_training(self) -> None:
        self._eng_content.setText(
            "Executing deep learning epochs. Analyzing compiled array vectors…"
        )
        self._eng_content.setStyleSheet(
            f"color: {CYAN}; font-size: 15px; word-wrap: true;"
        )
        self.training_triggered.emit()

    def _add_sign(self, sign_name: str) -> None:
        self._target_label = sign_name
        self._target_pill_lbl.setText(sign_name)
        self._target_pill_lbl.setStyleSheet(
            f"color: {CYAN}; font-size: 13px; font-weight: 600;"
            f"letter-spacing: 0.4px; background: transparent; border: none;"
        )
        self._dock.target_stat.set_value(sign_name)
        self._ds_content.setText(
            f"Successfully registered pattern vector class: '{sign_name}'"
        )
        self._ds_content.setStyleSheet(
            f"color: {GREEN_LIVE}; font-size: 15px;"
        )
        self.sign_label_assigned.emit(sign_name)

    # ── NEW: Force stop camera ────────────────────────────────
    def _force_stop_camera(self) -> None:
        """Force-stop the camera, abort recording if active, and reset UI."""
        if self._capturing:
            self._capturing = False
            self.btn_record.set_active(False, "Start Recording")
            self._status_badge.set_idle()
            self.data_capture_toggled.emit(False)

        self.camera_stop_requested.emit()
        self.btn_stop_cam.hide()

        # Reset canvas to animated placeholder
        self._canvas.set_pixmap(None)

        # Reset dock stats
        self._dock.frames_stat.set_value("0 / 100")
        self._dock.target_stat.set_value("—")
        self._target_pill_lbl.setText("No Active Target")
        self._target_pill_lbl.setStyleSheet(
            f"color: {TEXT_SEC}; font-size: 13px; font-weight: 600;"
            f"letter-spacing: 0.4px; background: transparent; border: none;"
        )

    # ── PUBLIC API ────────────────────────────────────────────
    def add_captured_frame(self, count: int, label: str) -> None:
        self._frames_captured = count
        self._target_label    = label
        self._dock.frames_stat.set_value(f"{count} / 100")
        self._dock.target_stat.set_value(label)
        self._ds_content.setText(
            f"Buffering stream matrix: {count} frame structures for token '{label}'."
        )

    def set_training_complete(self, accuracy: str) -> None:
        self._eng_content.setText(
            f"Model optimization terminated. Validation accuracy: {accuracy}"
        )
        self._eng_content.setStyleSheet(
            f"color: {GREEN_LIVE}; font-size: 15px;"
        )

    def refresh(self) -> None:
        self._capturing       = False
        self._frames_captured = 0
        self._target_label    = "—"
        self.btn_record.set_active(False, "Start Recording")
        self._status_badge.set_idle()
        self.btn_stop_cam.hide()           # ← NEW
        self._canvas.set_pixmap(None)      # ← NEW
        self._dock.frames_stat.set_value("0 / 100")
        self._dock.target_stat.set_value("—")
        self._target_pill_lbl.setText("No Active Target")
        self._target_pill_lbl.setStyleSheet(
            f"color: {TEXT_SEC}; font-size: 13px; font-weight: 600;"
            f"letter-spacing: 0.4px; background: transparent; border: none;"
        )
        self._ds_content.setText("Awaiting live stream capture sequence.")
        self._ds_content.setStyleSheet(f"color: {TEXT_PRIME}; font-size: 15px;")
        self._eng_content.setText(
            "Pipeline resting. Provide custom vector parameters to execute optimization algorithms."
        )
        self._eng_content.setStyleSheet(f"color: {TEXT_PRIME}; font-size: 15px;")


# ─────────────────────────────────────────────────────────────
#  STANDALONE PREVIEW ENTRY-POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = QWidget()
    win.setWindowTitle("SignBridge Studio — Training Screen")
    win.setMinimumSize(1280, 780)
    win.setStyleSheet(f"QWidget {{ background: {BG_VOID}; }}")

    lay = QVBoxLayout(win)
    lay.setContentsMargins(0, 0, 0, 0)

    screen = TrainingScreen()
    lay.addWidget(screen)

    win.show()
    sys.exit(app.exec())