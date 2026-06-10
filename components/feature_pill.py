"""
SignBridge Studio — Feature Pill Component
============================================
Small rounded badge/pill for feature highlights and tags.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class FeaturePill(QWidget):
    """Rounded pill badge with icon and text."""

    def __init__(self, icon: str, text: str, variant: str = "blue", parent=None):
        super().__init__(parent)

        variants = {
            "blue": ("feature_pill", "#2563EB"),
            "purple": ("feature_pill_alt", "#8B5CF6"),
            "cyan": ("feature_pill_cyan", "#06B6D4"),
        }
        obj_name, color = variants.get(variant, variants["blue"])
        self.setObjectName(obj_name)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 14, 6)
        layout.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 14px; color: {color}; background: transparent; border: none;")

        text_label = QLabel(text)
        text_label.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            background: transparent;
            border: none;
        """)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)

        self.setFixedHeight(layout.sizeHint().height())


class FeaturePillRow(QWidget):
    """Horizontal row of feature pills with spacing."""

    def __init__(self, pills: list, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        for pill_data in pills:
            pill = FeaturePill(
                icon=pill_data.get("icon", ""),
                text=pill_data.get("text", ""),
                variant=pill_data.get("variant", "blue")
            )
            layout.addWidget(pill)

        layout.addStretch()