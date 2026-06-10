"""
SignBridge Studio — Reusable Card Components
==============================================
BaseCard, HeroCard, FeatureCard, ModeCard with glow effects.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor


class BaseCard(QFrame):
    """Base card with rounded corners, border, and optional glow."""

    def __init__(self, elevated=False, parent=None):
        super().__init__(parent)
        self.setObjectName("elevated_card" if elevated else "card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(12)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def add_widget(self, widget):
        self._layout.addWidget(widget)

    def add_layout(self, layout):
        self._layout.addLayout(layout)

    def set_glow(self, color: QColor = None, blur: int = 30, offset=(0, 4)):
        if color is None:
            color = QColor(37, 99, 235, 60)
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(blur)
        glow.setColor(color)
        glow.setOffset(*offset)
        self.setGraphicsEffect(glow)

    def fade_in(self, duration=400):
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)
        self._fade_anim = QPropertyAnimation(effect, b"opacity")
        self._fade_anim.setDuration(duration)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.finished.connect(lambda: self.setGraphicsEffect(None))
        self._fade_anim.start()


class HeroCard(BaseCard):
    """Large hero card for dashboard top section."""

    def __init__(self, title: str, subtitle: str = "", description: str = "", parent=None):
        super().__init__(elevated=True, parent=parent)
        self.setObjectName("hero_card")
        self.set_glow(QColor(37, 99, 235, 40), blur=40, offset=(0, 6))

        # Badge
        if subtitle:
            badge = QLabel(subtitle)
            badge.setObjectName("small_meta")
            badge.setStyleSheet("""
                color: #3B82F6;
                font-weight: 600;
                font-size: 11px;
                background-color: rgba(59,130,246,0.12);
                border-radius: 6px;
                padding: 4px 10px;
            """)
            badge.setFixedWidth(badge.sizeHint().width() + 20)
            self._layout.addWidget(badge)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("section_title")
        self._layout.addWidget(title_label)

        # Description
        if description:
            desc = QLabel(description)
            desc.setObjectName("body_text")
            desc.setWordWrap(True)
            self._layout.addWidget(desc)

        self._layout.addStretch()


class FeatureCard(BaseCard):
    """Feature highlight card with icon and description."""

    def __init__(self, icon_text: str, title: str, description: str,
                 accent_color: str = "#2563EB", parent=None):
        super().__init__(parent=parent)
        self.setObjectName("feature_card")
        self.set_glow(QColor(37, 99, 235, 30), blur=25, offset=(0, 4))

        # Icon
        icon_container = QWidget()
        icon_container.setFixedSize(48, 48)
        icon_container.setStyleSheet(f"""
            background-color: {accent_color}20;
            border-radius: 12px;
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon = QLabel(icon_text)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size: 20px; color: {accent_color};")
        icon_layout.addWidget(icon)

        self._layout.addWidget(icon_container)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("card_title")
        self._layout.addWidget(title_label)

        # Description
        desc = QLabel(description)
        desc.setObjectName("body_text")
        desc.setWordWrap(True)
        self._layout.addWidget(desc)

        self._layout.addStretch()


class ModeCard(BaseCard):
    """Mode selection card with icon, title, description, and action button."""

    def __init__(self, icon_text: str, title: str, subtitle: str,
                 description: str, accent_color: str = "#2563EB", parent=None):
        super().__init__(parent=parent)
        self.setObjectName("mode_card")
        self.set_glow(QColor(37, 99, 235, 25), blur=20, offset=(0, 4))

        # Header with icon and title — use a QWidget container so child
        # layouts are parented from the start, avoiding addChildLayout warnings
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header = QHBoxLayout(header_widget)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        icon_container = QWidget()
        icon_container.setFixedSize(44, 44)
        icon_container.setStyleSheet(f"""
            background-color: {accent_color}18;
            border-radius: 10px;
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon = QLabel(icon_text)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size: 18px; color: {accent_color};")
        icon_layout.addWidget(icon)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("card_title")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("small_meta")
        subtitle_label.setStyleSheet(f"color: {accent_color};")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header.addWidget(icon_container)
        header.addLayout(title_layout, 1)
        header.addStretch()

        self._layout.addWidget(header_widget)

        # Description
        desc = QLabel(description)
        desc.setObjectName("body_text")
        desc.setWordWrap(True)
        self._layout.addWidget(desc)

        self._layout.addStretch()