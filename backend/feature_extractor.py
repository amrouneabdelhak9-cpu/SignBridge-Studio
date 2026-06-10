"""
features/feature_extractor.py
==============================
Feature extractor updated for MediaPipe Tasks API output.
Now fully compatible with FrameData from CaptureWorker.
"""

from __future__ import annotations

from typing import List

import numpy as np

try:
    import torch
    TORCH_OK = True
except ImportError:
    TORCH_OK = False


# ── constants ─────────────────────────────────────────────────────────────────
HAND_PTS  = 21
XYZ       = 3

HAND_VEC  = HAND_PTS * XYZ          # 63
BASE_FEAT = HAND_VEC * 2 + 4        # 130
FACE_FEAT = 12
FULL_FEAT = BASE_FEAT + FACE_FEAT

DEFAULT_SEQ_LEN = 64


# ─────────────────────────────────────────────────────────────────────────────
class FeatureExtractor:
    """
    Converts MediaPipe Tasks landmarks → model-ready tensors.
    """

    def __init__(
        self,
        seq_len: int = DEFAULT_SEQ_LEN,
        face_features: bool = False,
    ) -> None:

        self.seq_len = seq_len
        self.face_features = face_features
        self.feature_dim = FULL_FEAT if face_features else BASE_FEAT

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def extract_sequence(self, frames: List[dict]) -> np.ndarray:
        """
        Convert list of FrameData dicts → [T, F]
        """
        if not frames:
            return np.zeros(
                (self.seq_len, self.feature_dim),
                dtype=np.float32,
            )

        seq = [self._frame_to_vec(f) for f in frames]
        arr = np.array(seq, dtype=np.float32)

        return self._pad_or_truncate(arr)

    def to_tensor(self, arr: np.ndarray):
        if not TORCH_OK:
            raise RuntimeError("PyTorch not installed")

        return torch.from_numpy(arr).unsqueeze(0)

    def extract_frame(self, frame: dict) -> np.ndarray:
        return self._frame_to_vec(frame)

    # ─────────────────────────────────────────────────────────────────────────
    # CORE CONVERSION
    # ─────────────────────────────────────────────────────────────────────────

    def _frame_to_vec(self, frame: dict) -> np.ndarray:

        vec = np.zeros(self.feature_dim, dtype=np.float32)

        right = frame.get("right_hand")
        left  = frame.get("left_hand")
        face  = frame.get("face_landmarks")

        # ── RIGHT HAND ───────────────────────────────────────────────────────
        if right:
            pts = self._to_array(right)
            pts = self._normalize(pts)

            vec[0:HAND_VEC] = pts.flatten()

            vec[HAND_VEC * 2] = 1.0  # right present

        # ── LEFT HAND ────────────────────────────────────────────────────────
        if left:
            pts = self._to_array(left)
            pts = self._normalize(pts)

            vec[HAND_VEC:HAND_VEC * 2] = pts.flatten()

            vec[HAND_VEC * 2 + 1] = 1.0  # left present

        # ── confidence proxy ────────────────────────────────────────────────
        vec[HAND_VEC * 2 + 2] = float(np.std(vec[0:HAND_VEC]))
        vec[HAND_VEC * 2 + 3] = float(np.std(vec[HAND_VEC:HAND_VEC * 2]))

        # ── FACE (optional) ────────────────────────────────────────────────
        if self.face_features and face:
            vec[BASE_FEAT:BASE_FEAT + FACE_FEAT] = self._face(face)

        return vec

    # ─────────────────────────────────────────────────────────────────────────
    # HAND HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _to_array(pts: List[dict]) -> np.ndarray:
        return np.array(
            [[p["x"], p["y"], p["z"]] for p in pts],
            dtype=np.float32,
        )

    @staticmethod
    def _normalize(pts: np.ndarray) -> np.ndarray:
        """
        Normalize relative to wrist + scale normalization.
        """
        pts = pts - pts[0]

        scale = float(np.linalg.norm(pts[9]))
        if scale < 1e-6:
            return pts

        return pts / scale

    # ─────────────────────────────────────────────────────────────────────────
    # FACE HELPERS (simplified safe version)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _face(face: List[dict]) -> np.ndarray:
        """
        Safe compact face embedding (12 values).
        Works even if landmarks are partial.
        """

        out = np.zeros(12, dtype=np.float32)

        if not face or len(face) < 10:
            return out

        def pt(i):
            if i >= len(face):
                return np.array([0.0, 0.0], dtype=np.float32)
            return np.array([face[i]["x"], face[i]["y"]], dtype=np.float32)

        nose = pt(1)

        leye = (pt(33) + pt(133)) * 0.5 - nose
        reye = (pt(362) + pt(263)) * 0.5 - nose

        lip_t = pt(13) - nose
        lip_b = pt(14) - nose
        lip_l = pt(61) - nose
        lip_r = pt(291) - nose

        scale = float(np.linalg.norm(leye - reye)) + 1e-6

        features = np.concatenate([
            leye, reye, lip_t, lip_b, lip_l, lip_r
        ]) / scale

        out[:min(12, len(features))] = features[:12]

        return out

    # ─────────────────────────────────────────────────────────────────────────
    # SEQUENCE HANDLING
    # ─────────────────────────────────────────────────────────────────────────

    def _pad_or_truncate(self, arr: np.ndarray) -> np.ndarray:

        T = arr.shape[0]

        if T == self.seq_len:
            return arr

        if T > self.seq_len:
            return arr[-self.seq_len:]

        pad = np.zeros(
            (self.seq_len - T, self.feature_dim),
            dtype=np.float32,
        )

        return np.vstack([arr, pad])

    # ─────────────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"<FeatureExtractor seq_len={self.seq_len} "
            f"feature_dim={self.feature_dim} "
            f"face={self.face_features}>"
        )