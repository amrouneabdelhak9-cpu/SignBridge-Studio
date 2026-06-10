"""
SignBridge Studio — Camera Widget Component
=============================================
OpenCV camera feed display with placeholder states and overlay controls.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QImage, QPixmap, QColor, QPainter, QFont
import cv2
import numpy as np


class CameraWidget(QWidget):
    """Camera preview widget with OpenCV integration."""

    frame_captured = Signal(np.ndarray)  # Emits raw frame

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("camera_widget")
        self.setMinimumSize(480, 360)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._capture = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_frame)
        self._is_running = False
        self._current_frame = None

        self._init_ui()
        self._apply_glow()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stacked widget for states
        self._stack = QStackedWidget()

        # Placeholder state
        self._placeholder = self._create_placeholder()
        self._stack.addWidget(self._placeholder)

        # Active camera state
        self._camera_label = QLabel()
        self._camera_label.setAlignment(Qt.AlignCenter)
        self._camera_label.setStyleSheet("background-color: #08111F; border-radius: 16px;")
        self._camera_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._stack.addWidget(self._camera_label)

        layout.addWidget(self._stack)

        # Bottom overlay bar
        overlay = QWidget()
        overlay.setStyleSheet("background-color: transparent;")
        overlay_layout = QHBoxLayout(overlay)
        overlay_layout.setContentsMargins(16, 8, 16, 16)
        overlay_layout.setSpacing(8)

        self._status_label = QLabel("Camera stopped")
        self._status_label.setObjectName("small_meta")
        self._status_label.setStyleSheet("color: #64748B;")
        overlay_layout.addWidget(self._status_label)
        overlay_layout.addStretch()

        self._start_btn = QPushButton("▶ Start Camera")
        self._start_btn.setObjectName("glow_button")
        self._start_btn.setFixedHeight(36)
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.clicked.connect(self.toggle_camera)
        overlay_layout.addWidget(self._start_btn)

        layout.addWidget(overlay)

    def _create_placeholder(self):
        widget = QWidget()
        widget.setObjectName("camera_placeholder")
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("📷")
        icon.setStyleSheet("font-size: 48px; background-color: transparent; border: none;")
        icon.setAlignment(Qt.AlignCenter)

        text = QLabel("Camera stopped")
        text.setObjectName("body_text")
        text.setAlignment(Qt.AlignCenter)

        layout.addWidget(icon)
        layout.addWidget(text)
        return widget

    def _apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(37, 99, 235, 50))
        glow.setOffset(0, 4)
        self.setGraphicsEffect(glow)

    def toggle_camera(self):
        if self._is_running:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self, camera_id: int = 0):
        self._capture = cv2.VideoCapture(camera_id)
        if self._capture.isOpened():
            self._is_running = True
            self._stack.setCurrentIndex(1)
            self._status_label.setText("● Live")
            self._status_label.setStyleSheet("color: #22C55E; font-weight: 600;")
            self._start_btn.setText("⏹ Stop Camera")
            self._timer.start(33)  # ~30 FPS

    def stop_camera(self):
        self._is_running = False
        self._timer.stop()
        if self._capture:
            self._capture.release()
            self._capture = None
        self._stack.setCurrentIndex(0)
        self._status_label.setText("Camera stopped")
        self._status_label.setStyleSheet("color: #64748B;")
        self._start_btn.setText("▶ Start Camera")

    def _update_frame(self):
        if self._capture and self._capture.isOpened():
            ret, frame = self._capture.read()
            if ret:
                self._current_frame = frame
                self.frame_captured.emit(frame)

                # Convert to RGB and display
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)

                # Scale to fit while maintaining aspect ratio
                scaled = pixmap.scaled(
                    self._camera_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self._camera_label.setPixmap(scaled)

    def get_current_frame(self):
        return self._current_frame

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._is_running and self._camera_label.pixmap():
            self._update_frame()

    def set_overlay_text(self, text: str):
        """Add detection overlay text on camera feed."""
        if self._is_running:
            self._status_label.setText(f"● {text}")


class CameraPlaceholder(QWidget):
    """Simplified camera placeholder for layouts without live feed."""

    def __init__(self, label_text: str = "Waiting for signs...", parent=None):
        super().__init__(parent)
        self.setObjectName("camera_widget")
        self.setMinimumSize(320, 240)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("✋")
        icon.setStyleSheet("font-size: 56px; background-color: transparent; border: none;")
        icon.setAlignment(Qt.AlignCenter)

        text = QLabel(label_text)
        text.setObjectName("body_text")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet("color: #3B82F6; font-weight: 500;")

        layout.addWidget(icon)
        layout.addWidget(text)

        self._apply_glow()

    def _apply_glow(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(25)
        glow.setColor(QColor(37, 99, 235, 40))
        glow.setOffset(0, 4)
        self.setGraphicsEffect(glow)