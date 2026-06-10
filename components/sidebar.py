# components/sidebar.py
"""
Ultra-premium futuristic AI sidebar – SignBridge Neural Translation Core.
Style: Apple VisionOS × Linear × Arc Browser × OpenAI Desktop.
Dark navy/black glassmorphism, cyan-blue accents, minimal neon.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGraphicsDropShadowEffect, QFrame,
)
from PySide6.QtCore import (
    Qt, Signal,
    QSize, QPoint,
)
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath,
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import QByteArray

# ── Dimensions ────────────────────────────────────────────────────────────────
EXPANDED_WIDTH    = 260
# Collapse/expand feature removed — sidebar is fixed-width

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG_DARK    = "#060912"       # deepest navy
C_SIDEBAR    = "#0A0E1F"       # sidebar surface
C_BORDER     = "rgba(100, 160, 255, 0.10)"
C_CYAN       = "#38BDF8"
C_BLUE       = "#6EA8FE"
C_VIOLET     = "#A78BFA"
C_TEXT_PRI   = "#EEF2FF"
C_TEXT_SEC   = "#7888AA"
C_TEXT_MUTED = "#3D4A62"
C_HOVER      = "rgba(110, 168, 254, 0.07)"
C_ACTIVE_BG  = "rgba(56, 189, 248, 0.09)"
C_ACTIVE_BD  = "rgba(56, 189, 248, 0.22)"
C_STATUS     = "#34D399"

# ── Logo SVG (abstract: bridge arch + neural nodes + hand gesture) ────────────
LOGO_SVG = b"""
<svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="lg1" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="100%" stop-color="#6EA8FE"/>
    </linearGradient>
    <linearGradient id="lg2" x1="40" y1="0" x2="0" y2="40" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#A78BFA"/>
      <stop offset="100%" stop-color="#38BDF8"/>
    </linearGradient>
  </defs>
  <!-- Bridge arch -->
  <path d="M4 28 Q20 6 36 28" stroke="url(#lg1)" stroke-width="2.2"
        fill="none" stroke-linecap="round"/>
  <!-- Neural nodes -->
  <circle cx="20" cy="11.5" r="2.8" fill="url(#lg1)"/>
  <circle cx="9"  cy="24"   r="1.8" fill="url(#lg2)" opacity="0.85"/>
  <circle cx="31" cy="24"   r="1.8" fill="url(#lg2)" opacity="0.85"/>
  <!-- Neural connection lines -->
  <line x1="20" y1="11.5" x2="9"  y2="24" stroke="url(#lg2)"
        stroke-width="1" opacity="0.45" stroke-dasharray="2 2"/>
  <line x1="20" y1="11.5" x2="31" y2="24" stroke="url(#lg2)"
        stroke-width="1" opacity="0.45" stroke-dasharray="2 2"/>
  <line x1="9"  y1="24"   x2="31" y2="24" stroke="url(#lg1)"
        stroke-width="1" opacity="0.30"/>
  <!-- Hand / sign-language gesture hint -->
  <path d="M17 33 C17 31 19 30 20 30 C21 30 23 31 23 33"
        stroke="url(#lg1)" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <line x1="18" y1="30" x2="18" y2="27" stroke="url(#lg1)"
        stroke-width="1.4" stroke-linecap="round" opacity="0.65"/>
  <line x1="20" y1="30" x2="20" y2="26.5" stroke="url(#lg1)"
        stroke-width="1.4" stroke-linecap="round" opacity="0.65"/>
  <line x1="22" y1="30" x2="22" y2="27" stroke="url(#lg1)"
        stroke-width="1.4" stroke-linecap="round" opacity="0.65"/>
</svg>
"""

# ── Icon SVGs (thin outline, Lucide-inspired) ─────────────────────────────────
ICONS: dict[str, bytes] = {
    "home": b"""
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"
        stroke="%COLOR%" stroke-width="1.6" stroke-linejoin="round" fill="none"/>
  <path d="M9 21V12h6v9" stroke="%COLOR%" stroke-width="1.6"
        stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>""",

    "translation": b"""
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M5 5h6m0 0h4M11 5V3m0 2v3M5.5 8A5.5 5.5 0 0011 13.5"
        stroke="%COLOR%" stroke-width="1.6" stroke-linecap="round" fill="none"/>
  <path d="M8 13l3 6m0 0l3-6m-3 6v0" stroke="%COLOR%" stroke-width="1.6"
        stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M14 9h6m-3-3v3m0 0a6 6 0 01-4 5.6"
        stroke="%COLOR%" stroke-width="1.6" stroke-linecap="round" fill="none"/>
  <path d="M17 12l2.5 5.5M14 17.5h5" stroke="%COLOR%" stroke-width="1.6"
        stroke-linecap="round" fill="none"/>
</svg>""",

    "learn": b"""
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M2 7l10-4 10 4-10 4L2 7z" stroke="%COLOR%" stroke-width="1.6"
        stroke-linejoin="round" fill="none"/>
  <path d="M6 9.5V16l6 2.5 6-2.5V9.5" stroke="%COLOR%" stroke-width="1.6"
        stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <line x1="22" y1="7" x2="22" y2="14" stroke="%COLOR%" stroke-width="1.6"
        stroke-linecap="round"/>
</svg>""",

    "quiz": b"""
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="12" cy="12" r="9" stroke="%COLOR%" stroke-width="1.6" fill="none"/>
  <path d="M9.5 9.5a2.5 2.5 0 015 .5c0 2-2.5 2.5-2.5 4"
        stroke="%COLOR%" stroke-width="1.6" stroke-linecap="round" fill="none"/>
  <circle cx="12" cy="17.5" r="0.8" fill="%COLOR%"/>
</svg>""",

    "training": b"""
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 3C7 3 3 7 3 12s4 9 9 9 9-4 9-9" stroke="%COLOR%"
        stroke-width="1.6" stroke-linecap="round" fill="none"/>
  <path d="M12 7v5l3 3" stroke="%COLOR%" stroke-width="1.6"
        stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M17 3l4 0 0 4" stroke="%COLOR%" stroke-width="1.6"
        stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <line x1="21" y1="3" x2="16" y2="8" stroke="%COLOR%" stroke-width="1.6"
        stroke-linecap="round"/>
</svg>""",

    "diagnostics": b"""
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <polyline points="2,12 6,12 8,5 10,19 12,9 14,15 16,12 22,12"
            stroke="%COLOR%" stroke-width="1.6"
            stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>""",

    "settings": b"""
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="12" cy="12" r="3" stroke="%COLOR%" stroke-width="1.6" fill="none"/>
  <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0
           l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0
           v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83
           l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09
           A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83
           l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09
           a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83
           l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09
           a1.65 1.65 0 00-1.51 1z"
        stroke="%COLOR%" stroke-width="1.6" fill="none"/>
</svg>""",
}

# ── Stylesheet ─────────────────────────────────────────────────────────────────
STYLES = f"""
    QWidget#SidebarContainer {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #0A0E1F,
            stop:1 #060912
        );
        border: none;
        border-right: 1px solid rgba(100,160,255,0.10);
        border-radius: 18px;
    }}

    QPushButton {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 12px;
        color: {C_TEXT_SEC};
        font-family: "SF Pro Text", "DM Sans", "Inter", "Segoe UI", sans-serif;
        font-size: 13px;
        font-weight: 400;
        text-align: left;
        padding: 10px 12px;
    }}
    QPushButton:hover {{
        background: {C_HOVER};
        border-color: rgba(100,160,255,0.08);
        color: {C_TEXT_PRI};
    }}

    #NavIcon {{
        background: transparent;
        min-width: 30px;
    }}
    #NavText {{
        color: {C_TEXT_SEC};
        font-size: 13px;
        font-weight: 400;
        letter-spacing: -0.1px;
        background: transparent;
    }}

    #LogoName {{
        color: {C_TEXT_PRI};
        font-family: "SF Pro Display", "Syne", "DM Sans", system-ui;
        font-size: 16px;
        font-weight: 700;
        letter-spacing: -0.4px;
        background: transparent;
        border: none;
    }}
    #LogoSub {{
        color: {C_TEXT_MUTED};
        font-family: "SF Pro Text", "DM Sans", system-ui;
        font-size: 9px;
        font-weight: 400;
        letter-spacing: 0.9px;
        background: transparent;
        border: none;
    }}

    #SectionLabel {{
        color: {C_TEXT_MUTED};
        font-size: 9px;
        font-weight: 500;
        letter-spacing: 1.2px;
        background: transparent;
        border: none;
        padding: 0 10px;
    }}

    #Divider {{
        background: rgba(100,160,255,0.08);
        max-height: 1px;
        border: none;
    }}

    #StatusBadge {{
        background: rgba(52,211,153,0.07);
        border: 1px solid rgba(52,211,153,0.15);
        border-radius: 10px;
        padding: 8px 12px;
    }}
    #StatusText {{
        color: rgba(52,211,153,0.85);
        font-size: 11px;
        font-weight: 400;
        background: transparent;
        border: none;
        letter-spacing: 0.1px;
    }}
    #StatusDot {{
        color: {C_STATUS};
        font-size: 9px;
        background: transparent;
        border: none;
    }}

"""

# Active-state button style (applied per-button)
ACTIVE_STYLE = f"""
    QPushButton {{
        background: {C_ACTIVE_BG};
        border: 1px solid {C_ACTIVE_BD};
        border-radius: 12px;
        color: {C_TEXT_PRI};
        font-weight: 500;
    }}
    QPushButton:hover {{
        background: rgba(56,189,248,0.13);
        border-color: rgba(56,189,248,0.30);
    }}
"""


# ── Helper: build colored SVG widget ─────────────────────────────────────────
def _svg_widget(key: str, color: str, size: int = 20) -> QSvgWidget:
    svg_bytes = ICONS[key].replace(b"%COLOR%", color.encode())
    w = QSvgWidget()
    w.load(QByteArray(svg_bytes))
    w.setFixedSize(QSize(size, size))
    w.setStyleSheet("background: transparent;")
    return w


# ── Left-indicator overlay widget ────────────────────────────────────────────
class ActiveIndicator(QWidget):
    """Thin glowing vertical bar painted on the left edge of the active button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(3)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(C_CYAN))
        grad.setColorAt(1.0, QColor(C_BLUE))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        path = QPainterPath()
        path.addRoundedRect(0, self.height() * 0.2, 3, self.height() * 0.6, 2, 2)
        p.drawPath(path)
        # glow
        glow = QRadialGradient(1.5, self.height() / 2, 14)
        glow.setColorAt(0.0, QColor(56, 189, 248, 60))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(glow))
        p.drawRect(-12, 0, 28, self.height())


# ══════════════════════════════════════════════════════════════════════════════
class Sidebar(QWidget):
    navigation_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_id = "translation"   # default active

        self.setFixedWidth(EXPANDED_WIDTH)  # Fixed width — no collapse
        self.setObjectName("SidebarContainer")
        self.setStyleSheet(STYLES)

        # Soft outer shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(60)
        shadow.setOffset(8, 0)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.setGraphicsEffect(shadow)

        self._setup_ui()
        self._create_buttons()

        # Hover-expand removed — sidebar is fixed-width

    # ── UI Setup ─────────────────────────────────────────────────────────────
    def _setup_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(10, 24, 10, 16)
        self._main_layout.setSpacing(0)

        # ── Logo section ──
        self._logo_widget = QWidget()
        self._logo_widget.setStyleSheet("background: transparent;")
        logo_row = QHBoxLayout(self._logo_widget)
        logo_row.setContentsMargins(8, 0, 8, 0)
        logo_row.setSpacing(10)

        # SVG logo mark
        self._logo_svg = QSvgWidget()
        self._logo_svg.load(QByteArray(LOGO_SVG))
        self._logo_svg.setFixedSize(QSize(36, 36))
        self._logo_svg.setStyleSheet("background: transparent;")

        # Text group
        self._logo_text_widget = QWidget()
        self._logo_text_widget.setStyleSheet("background: transparent;")
        text_col = QVBoxLayout(self._logo_text_widget)
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        logo_name = QLabel("SignBridge")
        logo_name.setObjectName("LogoName")

        logo_sub = QLabel("NEURAL TRANSLATION CORE")
        logo_sub.setObjectName("LogoSub")

        text_col.addWidget(logo_name)
        text_col.addWidget(logo_sub)

        logo_row.addWidget(self._logo_svg)
        logo_row.addWidget(self._logo_text_widget)
        logo_row.addStretch()

        self._main_layout.addWidget(self._logo_widget)
        self._main_layout.addSpacing(20)

        # ── Divider ──
        self._main_layout.addWidget(self._make_divider())
        self._main_layout.addSpacing(14)

        # ── Section label ──
        self._nav_label = QLabel("NAVIGATION")
        self._nav_label.setObjectName("SectionLabel")
        self._main_layout.addWidget(self._nav_label)
        self._main_layout.addSpacing(8)

        # ── Button container ──
        self._btn_container = QWidget()
        self._btn_container.setStyleSheet("background: transparent;")
        self._btn_layout = QVBoxLayout(self._btn_container)
        self._btn_layout.setSpacing(4)
        self._btn_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addWidget(self._btn_container)

        self._main_layout.addStretch()

        # ── Bottom divider ──
        self._main_layout.addWidget(self._make_divider())
        self._main_layout.addSpacing(10)

        # ── Settings button placeholder (added in _create_buttons) ──
        self._settings_container = QWidget()
        self._settings_container.setStyleSheet("background: transparent;")
        self._settings_layout = QVBoxLayout(self._settings_container)
        self._settings_layout.setContentsMargins(0, 0, 0, 0)
        self._settings_layout.setSpacing(0)
        self._main_layout.addWidget(self._settings_container)

        self._main_layout.addSpacing(10)

        # ── Status badge ──
        self._status_widget = QWidget()
        self._status_widget.setObjectName("StatusBadge")
        status_row = QHBoxLayout(self._status_widget)
        status_row.setContentsMargins(10, 0, 10, 0)
        status_row.setSpacing(7)

        dot = QLabel("●")
        dot.setObjectName("StatusDot")
        dot.setFixedWidth(14)

        status_text = QLabel("System Status: <b>Optimal</b>")
        status_text.setObjectName("StatusText")
        status_text.setTextFormat(Qt.TextFormat.RichText)

        status_row.addWidget(dot)
        status_row.addWidget(status_text)
        status_row.addStretch()

        self._main_layout.addWidget(self._status_widget)
        self._main_layout.addSpacing(12)

        # ── Collapse button removed — sidebar is fixed-width ──

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setObjectName("Divider")
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        return line

    # ── Navigation buttons ────────────────────────────────────────────────────
    def _create_buttons(self):
        nav_items = [
            ("home",        "Home"),
            ("translation", "Live Translation"),
            ("learn",       "Learning"),
            ("quiz",        "Quiz"),
            ("training",    "Training"),
            ("diagnostics", "Diagnostics"),
        ]

        self._btns: dict[str, QPushButton]  = {}
        self._text_labels: dict[str, QLabel] = {}
        self._icon_widgets: dict[str, QSvgWidget] = {}
        self._indicators: dict[str, ActiveIndicator] = {}

        for nav_id, label_text in nav_items:
            btn = QPushButton()
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("nav_id", nav_id)
            btn.setFixedHeight(44)

            inner = QHBoxLayout(btn)
            inner.setContentsMargins(12, 0, 12, 0)
            inner.setSpacing(12)

            icon_w = _svg_widget(nav_id, C_TEXT_SEC, 18)

            text_lbl = QLabel(label_text)
            text_lbl.setObjectName("NavText")
            text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            inner.addWidget(icon_w)
            inner.addWidget(text_lbl)
            inner.addStretch()

            # Left-edge active indicator (parented to btn, positioned after show)
            indicator = ActiveIndicator(btn)
            indicator.setFixedHeight(44)
            indicator.hide()

            btn.clicked.connect(lambda checked, nid=nav_id: self._on_click(nid))

            self._btns[nav_id]         = btn
            self._text_labels[nav_id]  = text_lbl
            self._icon_widgets[nav_id] = icon_w
            self._indicators[nav_id]   = indicator

            self._btn_layout.addWidget(btn)

        # Settings button (bottom)
        settings_btn = QPushButton()
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setProperty("nav_id", "settings")
        settings_btn.setFixedHeight(44)

        s_inner = QHBoxLayout(settings_btn)
        s_inner.setContentsMargins(12, 0, 12, 0)
        s_inner.setSpacing(12)

        s_icon = _svg_widget("settings", C_TEXT_SEC, 18)
        s_text = QLabel("Settings")
        s_text.setObjectName("NavText")
        s_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        s_inner.addWidget(s_icon)
        s_inner.addWidget(s_text)
        s_inner.addStretch()

        s_indicator = ActiveIndicator(settings_btn)
        s_indicator.setFixedHeight(44)
        s_indicator.hide()

        settings_btn.clicked.connect(lambda: self._on_click("settings"))

        self._btns["settings"]         = settings_btn
        self._text_labels["settings"]  = s_text
        self._icon_widgets["settings"] = s_icon
        self._indicators["settings"]   = s_indicator

        self._settings_layout.addWidget(settings_btn)

        # Set default active
        self.set_active(self._active_id)

    # ── Collapse / Expand ─────────────────────────────────────────────────────
    # ── Collapse/expand removed — sidebar is fixed-width ────────────────────
    def _update_ui_for_width(self):
        # Always expanded mode
        self._logo_text_widget.setVisible(True)
        self._nav_label.setVisible(True)
        self._status_widget.setVisible(True)

        for nav_id, lbl in self._text_labels.items():
            lbl.setVisible(True)

        for nav_id, btn in self._btns.items():
            layout = btn.layout()
            layout.setContentsMargins(12, 0, 12, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._btn_container.updateGeometry()
        self._settings_container.updateGeometry()

    # ── Active state ──────────────────────────────────────────────────────────
    def _on_click(self, nav_id: str):
        self.set_active(nav_id)
        self.navigation_changed.emit(nav_id)

    def set_active(self, nav_id: str):
        self._active_id = nav_id
        for nid, btn in self._btns.items():
            is_active = nid == nav_id
            btn.setStyleSheet(ACTIVE_STYLE if is_active else "")

            # Icon color
            color = C_CYAN if is_active else C_TEXT_SEC
            svg_bytes = ICONS.get(nid, ICONS["home"]).replace(b"%COLOR%", color.encode())
            self._icon_widgets[nid].load(QByteArray(svg_bytes))

            # Nav text color
            self._text_labels[nid].setStyleSheet(
                f"color: {C_TEXT_PRI}; font-weight: 500;" if is_active
                else f"color: {C_TEXT_SEC}; font-weight: 400;"
            )

            # Active indicator bar
            ind = self._indicators[nid]
            ind.setVisible(is_active)
            if is_active:
                ind.move(QPoint(0, 0))
                ind.raise_()

    # ── Tooltips ──────────────────────────────────────────────────────────────
    def _update_tooltips(self):
        # Sidebar is fixed-width; tooltips not needed
        pass


# ── Standalone preview ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = QMainWindow()
    win.setWindowTitle("SignBridge – Sidebar Preview")
    win.resize(900, 680)

    # Dark window background
    central = QWidget()
    central.setStyleSheet("background: #060912;")
    h = QHBoxLayout(central)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(0)

    sidebar = Sidebar()
    sidebar.navigation_changed.connect(lambda nid: print(f"[nav] → {nid}"))

    # Placeholder content area
    content = QLabel("Content Area")
    content.setAlignment(Qt.AlignmentFlag.AlignCenter)
    content.setStyleSheet(
        "color: #3D4A62; font-family: 'SF Pro Display', sans-serif;"
        "font-size: 18px; font-weight: 300; background: #070B1A;"
    )

    h.addWidget(sidebar)
    h.addWidget(content, 1)

    win.setCentralWidget(central)
    win.show()
    sys.exit(app.exec())