"""
backend/capture_worker.py
==========================
Production-ready MediaPipe Tasks camera pipeline
(no mp.solutions dependency)
"""

from __future__ import annotations

import sys
import time
import dataclasses
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage, QPixmap


# ─────────────────────────────────────────────────────────────
# MediaPipe Tasks API
# ─────────────────────────────────────────────────────────────
try:
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python.vision import (
        HandLandmarker,
        HandLandmarkerOptions,
        FaceLandmarker,
        FaceLandmarkerOptions,
        RunningMode,
    )

    MEDIAPIPE_OK = True
except ImportError:
    MEDIAPIPE_OK = False
    print("⚠️ MediaPipe Tasks not installed")


# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

TARGET_FPS = 30

_CYAN = (0, 224, 255)
_GREEN = (0, 230, 118)

# Fully manual hand skeleton (NO mp.solutions)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
]


# ─────────────────────────────────────────────────────────────
# FRAME DATA
# ─────────────────────────────────────────────────────────────

@dataclasses.dataclass
class FrameData:
    frame_id: int
    timestamp: float

    left_hand: Optional[List[dict]] = None
    right_hand: Optional[List[dict]] = None
    face_landmarks: Optional[List[dict]] = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


# ─────────────────────────────────────────────────────────────
# WORKER
# ─────────────────────────────────────────────────────────────

class CaptureWorker(QThread):

    frame_ready = Signal(QPixmap)
    landmarks_ready = Signal(object)
    frame_count_changed = Signal(int)
    fps_updated = Signal(float)
    error_occurred = Signal(str)

    def __init__(
        self,
        camera_index: int = 0,
        enable_face: bool = False,
        target_fps: int = TARGET_FPS,
        parent=None,
    ):
        super().__init__(parent)

        self._cam_index = camera_index
        self._face_on = enable_face
        self._target_fps = target_fps

        self._running = False
        self._frame_id = 0

        self._cap: Optional[cv2.VideoCapture] = None

        self._hand_landmarker = None
        self._face_landmarker = None

        self._hand_model = str(Path("models/hand_landmarker.task"))
        self._face_model = str(Path("models/face_landmarker.task"))

    # ─────────────────────────────────────────────────────────────
    # CAMERA
    # ─────────────────────────────────────────────────────────────

    def _open_camera(self):
        backends = [
            (cv2.CAP_DSHOW, "DirectShow"),
            (cv2.CAP_MSMF, "MSMF"),
            (cv2.CAP_V4L2, "V4L2"),
            (cv2.CAP_ANY, "Default"),
        ]

        for backend, name in backends:
            cap = cv2.VideoCapture(self._cam_index, backend)

            if not cap.isOpened():
                continue

            for _ in range(3):
                ret, _ = cap.read()
                if ret:
                    print(f"[Camera] OK: {name}")
                    return cap

            cap.release()

        return None

    # ─────────────────────────────────────────────────────────────
    # MEDIA PIPE INIT
    # ─────────────────────────────────────────────────────────────

    def _init_mediapipe(self):

        if not MEDIAPIPE_OK:
            return

        hand_options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self._hand_model),
            running_mode=RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_tracking_confidence=0.4,
        )

        self._hand_landmarker = HandLandmarker.create_from_options(hand_options)

        if self._face_on:
            face_options = FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=self._face_model),
                running_mode=RunningMode.VIDEO,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_tracking_confidence=0.4,
            )

            self._face_landmarker = FaceLandmarker.create_from_options(face_options)

        print("[MediaPipe] Tasks initialized")

    # ─────────────────────────────────────────────────────────────
    # DRAW HAND (NO mp.solutions)
    # ─────────────────────────────────────────────────────────────

    def _draw_hand(self, frame, landmarks):

        h, w = frame.shape[:2]

        pts = []
        for lm in landmarks:
            x, y = int(lm.x * w), int(lm.y * h)
            pts.append((x, y))

        # draw points
        for x, y in pts:
            cv2.circle(frame, (x, y), 2, _CYAN, -1)

        # draw connections
        for a, b in HAND_CONNECTIONS:
            if a < len(pts) and b < len(pts):
                cv2.line(frame, pts[a], pts[b], _GREEN, 1)

    # ─────────────────────────────────────────────────────────────
    # MAIN LOOP
    # ─────────────────────────────────────────────────────────────

    def run(self):

        if not MEDIAPIPE_OK:
            self.error_occurred.emit("MediaPipe not installed")
            return

        self._running = True
        self._frame_id = 0

        cap = self._open_camera()
        self._cap = cap

        if cap is None:
            self.error_occurred.emit("Cannot open camera")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, self._target_fps)

        self._init_mediapipe()

        frame_interval = 1.0 / self._target_fps

        last = time.perf_counter()
        fps_window = []

        while self._running:

            start = time.perf_counter()

            ret, frame = cap.read()
            if not ret:
                self.msleep(10)
                continue

            frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            ts = int(time.time() * 1000)

            left = right = None
            face = None

            # ─── HANDS ─────────────────────────────
            if self._hand_landmarker:

                res = self._hand_landmarker.detect_for_video(mp_image, ts)

                if res.hand_landmarks:

                    for i, hand in enumerate(res.hand_landmarks):
                        label = res.handedness[i][0].category_name

                        pts = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in hand]

                        if label == "Left":
                            left = pts
                        else:
                            right = pts

                        self._draw_hand(frame, hand)

            # ─── FACE ─────────────────────────────
            if self._face_landmarker:

                fres = self._face_landmarker.detect_for_video(mp_image, ts)

                if fres.face_landmarks:
                    fl = fres.face_landmarks[0]
                    face = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in fl]

            # ─── FPS ─────────────────────────────
            now = time.perf_counter()
            fps_window.append(now - last)
            last = now

            if len(fps_window) > 30:
                fps_window.pop(0)

            fps = 1.0 / (sum(fps_window) / len(fps_window) + 1e-9)

            cv2.putText(frame, f"FPS {fps:.1f}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, _CYAN, 2)

            # ─── EMIT DATA ─────────────────────────
            fd = FrameData(
                frame_id=self._frame_id,
                timestamp=time.perf_counter(),
                left_hand=left,
                right_hand=right,
                face_landmarks=face,
            )

            self._frame_id += 1

            self.landmarks_ready.emit(fd)
            self.frame_count_changed.emit(self._frame_id)
            self.fps_updated.emit(fps)

            # ─── QT IMAGE ─────────────────────────
            frame = np.ascontiguousarray(frame)
            h, w, ch = frame.shape

            qt = QImage(frame.data, w, h, ch * w, QImage.Format_BGR888)
            self.frame_ready.emit(QPixmap.fromImage(qt).copy())

            # ─── FPS LIMIT ────────────────────────
            elapsed = time.perf_counter() - start
            sleep = frame_interval - elapsed

            if sleep > 0:
                self.msleep(int(sleep * 1000))

        # cleanup
        if cap:
            cap.release()

        if self._hand_landmarker:
            self._hand_landmarker.close()

        if self._face_landmarker:
            self._face_landmarker.close()

    def stop(self):
        self._running = False
        if self._cap:
            self._cap.release()
        self.wait(5000)