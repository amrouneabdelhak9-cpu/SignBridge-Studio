# ui/dashboard_screen.py
"""
SignBridge Studio — Home Dashboard Screen (Futuristic)
=======================================================
Cinematic dashboard with glass cards, holographic gradients, and soft glows.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QFrame, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QLinearGradient

import math

# Futuristic theme
try:
    from ui.theme import FuturisticTheme
    BG = FuturisticTheme.BG_DEEP
    SURFACE = FuturisticTheme.GLASS_BG
    BLUE = FuturisticTheme.CYAN
    BLUE_DARK = FuturisticTheme.BLUE_AURORA
    PURPLE = FuturisticTheme.VIOLET_HOLO
    PURPLE_DARK = FuturisticTheme.PURPLE_NEON
    GREEN = FuturisticTheme.EMERALD
    GREEN_DARK = "#00D68F"
    AMBER = FuturisticTheme.MAGENTA
    AMBER_DARK = "#FF1A8C"
    CYAN = FuturisticTheme.CYAN
    TEXT_PRIM = FuturisticTheme.TEXT_PRIMARY
    TEXT_SEC = FuturisticTheme.TEXT_SECONDARY
    TEXT_MUTED = FuturisticTheme.TEXT_MUTED
except ImportError:
    BG = "#02040B"
    SURFACE = "rgba(12, 20, 32, 0.65)"
    BLUE = "#00E5FF"
    BLUE_DARK = "#33CFFF"
    PURPLE = "#7B61FF"
    PURPLE_DARK = "#A855F7"
    GREEN = "#00FFB2"
    GREEN_DARK = "#00D68F"
    AMBER = "#FF4DDB"
    AMBER_DARK = "#FF1A8C"
    CYAN = "#00E5FF"
    TEXT_PRIM = "#F5F7FF"
    TEXT_SEC = "#AAB3C5"
    TEXT_MUTED = "#6E7891"

FONT_SANS = "'Inter', 'SF Pro Display', sans-serif"
FONT_MONO = "'JetBrains Mono', monospace"


def _glow(widget: QWidget, color: QColor, blur: int = 30, dy: int = 6):
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(blur)
    fx.setColor(color)
    fx.setOffset(0, dy)
    widget.setGraphicsEffect(fx)
    return fx


def _title_glow(label: QLabel, accent: str, blur: int = 24, alpha: int = 160):
    fx = QGraphicsDropShadowEffect(label)
    fx.setBlurRadius(blur)
    r, g, b = [int(x) for x in _hex_to_rgb(accent).split(",")]
    fx.setColor(QColor(r, g, b, alpha))
    fx.setOffset(0, 2)
    label.setGraphicsEffect(fx)


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


def _adjust_hex(hex_color: str, factor: float) -> str:
    h = hex_color.lstrip("#")
    r = max(0, min(255, int(int(h[0:2],16)*factor)))
    g = max(0, min(255, int(int(h[2:4],16)*factor)))
    b = max(0, min(255, int(int(h[4:6],16)*factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _section_divider(label_text: str) -> QWidget:
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    label = QLabel(label_text)
    label.setStyleSheet(f"""
        color: {TEXT_MUTED};
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1.5px;
        font-family: {FONT_SANS};
        text-transform: uppercase;
    """)
    layout.addWidget(label)
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background-color: rgba(0,229,255,0.2); border: none;")
    layout.addWidget(line)
    return container


class _HeroCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("hero_card")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QWidget#hero_card {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 rgba(12,20,32,0.9), stop:1 rgba(20,30,50,0.7));
                border: 1px solid rgba(0,229,255,0.3);
                border-radius: 28px;
            }}
        """)
        _glow(self, QColor(0, 229, 255, 50), blur=40, dy=8)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(0)

        text_col = QVBoxLayout()
        text_col.setSpacing(12)
        title = QLabel("SignBridge")
        title.setStyleSheet(f"""
            color: #FFFFFF;
            font-size: 36px;
            font-weight: 800;
            font-family: {FONT_SANS};
            background: transparent;
        """)
        text_col.addWidget(title)

        subtitle = QLabel("AI-Powered Sign Language Translation & Learning Studio")
        subtitle.setStyleSheet(f"""
            color: {BLUE};
            font-size: 16px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        text_col.addWidget(subtitle)

        desc = QLabel(
            "Seamlessly bridge the gap between sign language and the hearing world. "
            "Our high-performance pipeline translates gestures into natural conversational "
            "English with instant voice synthesis."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 14px;
            line-height: 1.5;
        """)
        desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_col.addWidget(desc)
        text_col.addStretch()
        layout.addLayout(text_col, 1)


class _CardIcon(QWidget):
    def __init__(self, icon_type: str, accent: str, size: int = 32, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.accent = accent
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(self.accent))
        pen.setWidthF(1.5)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        w, h = self.width(), self.height()

        if self.icon_type == "aperture":
            m = 2
            arm = 7
            painter.drawLine(m, m+arm, m, m)
            painter.drawLine(m, m, m+arm, m)
            painter.drawLine(w-m, m+arm, w-m, m)
            painter.drawLine(w-m, m, w-m-arm, m)
            painter.drawLine(m, h-m-arm, m, h-m)
            painter.drawLine(m, h-m, m+arm, h-m)
            painter.drawLine(w-m, h-m-arm, w-m, h-m)
            painter.drawLine(w-m, h-m, w-m-arm, h-m)
            cx, cy = w//2, h//2
            painter.setBrush(QBrush(QColor(self.accent)))
            painter.drawEllipse(cx-2, cy-2, 4, 4)
        elif self.icon_type == "chip":
            cx, cy = w//2, h//2
            sz = 7
            painter.drawRect(cx-sz, cy-sz, sz*2, sz*2)
            offsets = [(0,-1),(1,0),(0,1),(-1,0)]
            for dx,dy in offsets:
                x1 = cx+dx*sz
                y1 = cy+dy*sz
                x2 = cx+dx*(sz+6)
                y2 = cy+dy*(sz+6)
                painter.drawLine(x1,y1,x2,y2)
                painter.drawEllipse(x2-2, y2-2, 4,4)
        elif self.icon_type == "speech":
            m=3
            body_w = w-2*m
            body_h = h-2*m-4
            painter.drawRoundedRect(m, m, body_w, body_h, 4,4)
            tail_cx = w//2
            tail_top = m+body_h
            painter.drawLine(tail_cx-2, tail_top, tail_cx, h-m)
            painter.drawLine(tail_cx, h-m, tail_cx+2, tail_top)
        elif self.icon_type == "cap":
            cx,cy = w//2, h//2
            painter.drawLine(4, cy-2, w-4, cy-2)
            painter.drawLine(4, cy-2, 8, cy+7)
            painter.drawLine(w-4, cy-2, w-8, cy+7)
            painter.drawLine(8, cy+7, w-8, cy+7)
            painter.drawLine(w-8, cy+2, w-3, cy+12)
            painter.drawEllipse(w-4, cy+11, 3,3)
        painter.end()


class _Card(QWidget):
    def __init__(self, accent: str = BLUE, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        rgb = _hex_to_rgb(accent)
        self.setStyleSheet(f"""
            _Card, QWidget#card {{
                background: rgba(12,20,32,0.75);
                border: 1px solid rgba({rgb},0.35);
                border-radius: 24px;
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20,20,20,20)
        self._layout.setSpacing(12)


class _FeatureCard(_Card):
    def __init__(self, title: str, subtitle: str, desc: str,
                 accent: str, icon_type: str,
                 btn_text: str = None,
                 gradient_start: str = None,
                 gradient_end: str = None,
                 parent=None):
        super().__init__(accent=accent, parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        top_zone = QHBoxLayout()
        top_zone.setSpacing(12)
        icon = _CardIcon(icon_type, accent, 32)
        top_zone.addWidget(icon, 0, Qt.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        t = QLabel(title)
        t.setWordWrap(True)
        t.setStyleSheet(f"color: #FFFFFF; font-size: 20px; font-weight: 700; font-family: {FONT_SANS};")
        title_col.addWidget(t)
        s = QLabel(subtitle)
        s.setWordWrap(True)
        s.setStyleSheet(f"color: {accent}; font-size: 14px; font-weight: 700; font-family: {FONT_MONO};")
        _title_glow(s, accent, blur=20, alpha=200)
        title_col.addWidget(s)
        top_zone.addLayout(title_col)
        top_zone.addStretch()
        self._layout.addLayout(top_zone)

        self._layout.addStretch(1)
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 14px; line-height: 1.5;")
        desc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._layout.addWidget(desc_lbl)
        self._layout.addStretch(1)

        if btn_text:
            bottom_zone = QHBoxLayout()
            bottom_zone.addStretch()
            grad_start = gradient_start if gradient_start else accent
            grad_end = gradient_end if gradient_end else BLUE
            btn = QPushButton(btn_text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(160, 44)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 {grad_start}, stop:1 {grad_end});
                    color: white;
                    border: none;
                    border-radius: 24px;
                    font-size: 13px;
                    font-weight: 700;
                    font-family: {FONT_SANS};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {grad_end}, stop:1 {_adjust_hex(grad_end,1.2)});
                }}
            """)
            self._btn = btn
            _glow(btn, QColor(0,229,255,80), blur=32, dy=4)
            bottom_zone.addWidget(btn)
            self._layout.addLayout(bottom_zone)
        else:
            self._layout.addStretch(1)

        _glow(self, QColor(*[int(x) for x in _hex_to_rgb(accent).split(",")], 40), blur=28, dy=6)


class _ModePanel(_Card):
    def __init__(self, title: str, subtitle: str,
                 desc: str, features: list, accent: str,
                 stat_value: str, stat_label: str,
                 icon_type: str,
                 gradient_start: str = None,
                 gradient_end: str = None,
                 subtitle_size: int = 14,
                 subtitle_weight: int = 700,
                 desc_size: int = 14,
                 desc_weight: int = 400,
                 desc_centered: bool = False,
                 btn_text: str = "→",
                 parent=None):
        super().__init__(accent=accent, parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        rgb = _hex_to_rgb(accent)

        top_zone = QHBoxLayout()
        top_zone.setSpacing(12)
        icon = _CardIcon(icon_type, accent, 32)
        top_zone.addWidget(icon, 0, Qt.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        t = QLabel(title)
        t.setWordWrap(True)
        t.setStyleSheet(f"color: #FFFFFF; font-size: 20px; font-weight: 700;")
        title_col.addWidget(t)
        s = QLabel(subtitle)
        s.setWordWrap(True)
        s.setStyleSheet(f"color: {accent}; font-size: {subtitle_size}px; font-weight: {subtitle_weight}; font-family: {FONT_MONO};")
        _title_glow(s, accent, blur=20, alpha=200)
        title_col.addWidget(s)
        top_zone.addLayout(title_col)
        top_zone.addStretch()


        self._layout.addLayout(top_zone)

        self._layout.addStretch(1)
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        desc_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: {desc_size}px; line-height: 1.5;")
        desc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._layout.addWidget(desc_lbl)

        if features and not desc_centered:
            self._layout.addSpacing(8)
            for feat in features:
                lbl = QLabel(f"•  {feat}")
                lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
                self._layout.addWidget(lbl)

        self._layout.addStretch(1)

        bottom_zone = QHBoxLayout()
        bottom_zone.addStretch()
        grad_start = gradient_start if gradient_start else accent
        grad_end = gradient_end if gradient_end else BLUE
        btn = QPushButton(btn_text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(160, 44)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {grad_start}, stop:1 {grad_end});
                color: white;
                border: none;
                border-radius: 24px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {grad_end}, stop:1 {_adjust_hex(grad_end,1.2)});
            }}
        """)
        self._btn = btn
        _glow(btn, QColor(0,229,255,80), blur=32, dy=4)
        bottom_zone.addWidget(btn)
        self._layout.addLayout(bottom_zone)

        _glow(self, QColor(*[int(x) for x in rgb.split(",")], 40), blur=28, dy=6)


class _MasterContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("master_container")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#master_container {{
                background: rgba(12,20,32,0.65);
                border: 1px solid rgba(0,229,255,0.2);
                border-radius: 32px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28,24,28,24)
        outer.setSpacing(0)

        outer.addWidget(_section_divider("01 — PLATFORM OVERVIEW"))
        outer.addSpacing(12)
        hero_card = _HeroCard()
        outer.addWidget(hero_card)
        outer.addSpacing(20)

        outer.addWidget(_section_divider("02 — APPLICATION CORE"))
        outer.addSpacing(16)

        grid = QVBoxLayout()
        grid.setSpacing(20)

        row1 = QHBoxLayout()
        row1.setSpacing(20)
        self._feat1 = _FeatureCard(
            title="Real-Time Detection",
            subtitle="< 50ms latency",
            desc="On-device computer vision pipeline processes your camera feed locally, detecting hand signs frame-by-frame with sub-second response.",
            accent=BLUE,
            icon_type="aperture",
            btn_text="Start Detection",
            gradient_start="#0066FF",
            gradient_end=BLUE,
        )
        self._train_panel = _ModePanel(
            title="Training Mode",
            subtitle="Custom sign training",
            desc="Capture custom hand gestures, train your local AI model, and seamlessly expand the vocabulary.",
            features=None,
            accent=PURPLE,
            stat_value="Local",
            stat_label="Pipeline",
            icon_type="chip",
            gradient_start=PURPLE_DARK,
            gradient_end=PURPLE,
            desc_centered=True,
            btn_text="Open Trainer",
        )
        row1.addWidget(self._feat1)
        row1.addWidget(self._train_panel)
        row1_container = QWidget()
        row1_container.setLayout(row1)
        grid.addWidget(row1_container, 1)

        row2 = QHBoxLayout()
        row2.setSpacing(20)
        self._trans_panel = _ModePanel(
            title="Translation Mode",
            subtitle="Sign → Text → Speech",
            desc="Hold a sign to the camera. AI detects, composes natural English, and speaks it aloud in real time.",
            features=None,
            accent=GREEN,
            stat_value="94%",
            stat_label="Accuracy",
            icon_type="speech",
            gradient_start=GREEN_DARK,
            gradient_end=GREEN,
            desc_centered=True,
            btn_text="Start Translation",
        )
        self._learn_panel = _ModePanel(
            title="Learning Mode",
            subtitle="Interactive lessons",
            desc="Study visual flashcards, take AI-generated quizzes, and practice in the framed camera area.",
            features=None,
            accent=AMBER,
            stat_value="12",
            stat_label="Lessons",
            icon_type="cap",
            gradient_start=AMBER_DARK,
            gradient_end=AMBER,
            desc_centered=True,
            btn_text="Start Learning",
        )
        row2.addWidget(self._trans_panel)
        row2.addWidget(self._learn_panel)
        row2_container = QWidget()
        row2_container.setLayout(row2)
        grid.addWidget(row2_container, 1)

        outer.addLayout(grid, 1)
        _glow(self, QColor(0, 229, 255, 40), blur=40, dy=8)


class DashboardScreen(QWidget):
    navigate_to = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboard_screen")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: transparent;")
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,229,255,0.3);
                border-radius: 2px;
                min-height: 40px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        page = QWidget()
        page.setStyleSheet("background: transparent;")
        content = QVBoxLayout(page)
        content.setContentsMargins(24, 20, 24, 24)
        content.setSpacing(0)

        self._master = _MasterContainer()
        content.addWidget(self._master, 1)

        self._master._feat1._btn.clicked.connect(lambda: self.navigate_to.emit("diagnostics"))
        self._master._trans_panel._btn.clicked.connect(lambda: self.navigate_to.emit("translation"))
        self._master._learn_panel._btn.clicked.connect(lambda: self.navigate_to.emit("learn"))
        self._master._train_panel._btn.clicked.connect(lambda: self.navigate_to.emit("training"))

        scroll.setWidget(page)
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.addWidget(scroll)