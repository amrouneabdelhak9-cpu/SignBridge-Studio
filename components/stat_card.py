"""
SignBridge Studio — Stat Card Component
=========================================
Compact statistic display with number, label, and optional trend indicator.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class StatCard(QWidget):
    """Small stat card for dashboard metrics."""

    def __init__(self, value: str, label: str, trend: str = None,
                 accent: str = "#2563EB", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)

        # Value
        value_label = QLabel(value)
        value_label.setObjectName("stat_number")
        value_label.setStyleSheet(f"color: {accent};")
        layout.addWidget(value_label)

        # Label row
        label_row = QHBoxLayout()
        label_row.setSpacing(8)

        label_text = QLabel(label)
        label_text.setObjectName("stat_label")
        label_row.addWidget(label_text)

        if trend:
            trend_label = QLabel(trend)
            trend_label.setStyleSheet("""
                color: #22C55E;
                font-size: 11px;
                font-weight: 600;
                background-color: rgba(34,197,94,0.12);
                border-radius: 4px;
                padding: 2px 6px;
            """)
            label_row.addWidget(trend_label)

        label_row.addStretch()
        layout.addLayout(label_row)

        self._apply_glow(accent)

    def _apply_glow(self, accent: str):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(20)
        # Parse hex to RGB for glow
        if accent.startswith("#"):
            r = int(accent[1:3], 16)
            g = int(accent[3:5], 16)
            b = int(accent[5:7], 16)
            glow.setColor(QColor(r, g, b, 40))
        else:
            glow.setColor(QColor(37, 99, 235, 40))
        glow.setOffset(0, 3)
        self.setGraphicsEffect(glow)


class StatRow(QWidget):
    """Horizontal row of stat cards."""

    def __init__(self, stats: list, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        for stat in stats:
            card = StatCard(
                value=stat.get("value", "0"),
                label=stat.get("label", ""),
                trend=stat.get("trend"),
                accent=stat.get("accent", "#2563EB")
            )
            layout.addWidget(card)