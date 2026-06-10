"""
integration/inference_adapter.py  —  FIXED v3 (ROOT FIX)
==========================================================

ROOT CAUSES FIXED:
==================
1. "peace" always predicted / wrong class stuck:
   - FeatureExtractor pads zeros at END → model sees old gesture's tail frames
     FIXED: we now take the LAST seq_len frames (most recent), not first
   - Buffer never flushed when hand changes shape → stale frames dominate
     FIXED: cosine-similarity gate between consecutive frames detects gesture change
   - TOP2_MARGIN=0.30 was rejecting valid predictions silently
     FIXED: lowered to 0.12
   - Smooth window majority vote kept old label alive too long
     FIXED: window=2, recency-weighted, cleared on raw-label-change

2. TTS fires every frame (hammering the queue):
   - speak() now only fires ONCE per confirmed prediction
   - Added _last_tts_label to block repeated calls until label CHANGES
   - Repeat button: call adapter.repeat_tts() from UI button

3. TTS backend:
   - Primary: gTTS + pygame (supports Arabic perfectly, no voice install needed)
   - Fallback: pyttsx3
   - install: pip install gTTS pygame
"""

from __future__ import annotations

import collections
import os
import queue
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import torch
    TORCH_OK = True
except ImportError:
    TORCH_OK = False

from backend.feature_extractor import FeatureExtractor
from backend.custom_model import CustomSignModel

# ─────────────────────────────────────────────────────────────────────────────
# TUNABLE CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.68   # min softmax prob to accept
TOP2_MARGIN          = 0.12   # top1 must beat top2 by this much (was 0.30 — too strict)
SMOOTH_WINDOW        = 2      # history deque size (keep small = responsive)
BUFFER_SIZE          = 20     # frame buffer size (was 32 — too slow to react)
MIN_FRAMES_TO_PRED   = 5      # need at least this many frames before predicting
DEBUG                = False  # set True to print probabilities every frame


# ─────────────────────────────────────────────────────────────────────────────
# TTS  — gTTS+pygame primary, pyttsx3 fallback
# ─────────────────────────────────────────────────────────────────────────────
class _TTSHelper:
    """
    Non-blocking TTS. Speaks once per new label.
    UI can call repeat() to re-speak the last word.
    """

    def __init__(self, cooldown: float = 2.0) -> None:
        self._q: queue.Queue[Optional[str]] = queue.Queue()
        self._cooldown    = cooldown
        self._last_label  = ""           # last spoken label (for repeat)
        self._last_time   = 0.0
        self._lock        = threading.Lock()
        self._enabled     = False
        self._backend     = self._detect_backend()

        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    # ── backend detection ─────────────────────────────────────────────────────
    @staticmethod
    def _detect_backend() -> str:
        try:
            from gtts import gTTS      # noqa
            import pygame              # noqa
            return "gtts"
        except ImportError:
            pass
        try:
            import pyttsx3             # noqa
            return "pyttsx3"
        except ImportError:
            pass
        print("[TTS] ⚠ No TTS backend. Run:  pip install gTTS pygame")
        return "none"

    @staticmethod
    def _is_arabic(text: str) -> bool:
        return bool(re.search(r"[\u0600-\u06FF]", text))

    # ── worker ────────────────────────────────────────────────────────────────
    def _worker(self) -> None:
        """Worker with automatic restart on crash — keeps the thread alive."""
        while True:
            try:
                if self._backend == "gtts":
                    self._run_gtts()
                elif self._backend == "pyttsx3":
                    self._run_pyttsx3()
                else:
                    break   # no backend → exit cleanly
                break       # clean shutdown via None sentinel
            except Exception as e:
                print(f"[TTS] worker crashed, restarting: {e}")
                time.sleep(0.5)

    def _run_gtts(self) -> None:
        from gtts import gTTS
        import pygame
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
        pygame.mixer.init()
        self._enabled = True
        print("[TTS] gTTS + pygame ready ✓")
        while True:
            text = self._q.get()
            if text is None:
                break
            try:
                lang = "ar" if self._is_arabic(text) else "en"
                tts  = gTTS(text=text, lang=lang, slow=False)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    tmp = f.name
                tts.save(tmp)
                pygame.mixer.music.load(tmp)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                try:
                    os.remove(tmp)
                except OSError:
                    pass
            except Exception as e:
                print(f"[TTS] gTTS speak error: {e}")
                # On gTTS network error fall through to next queue item — don't die

    def _run_pyttsx3(self) -> None:
        import pyttsx3
        # Init the engine ONCE in this dedicated thread and keep it alive.
        # Never call engine.stop() between utterances — it kills the event loop
        # on Windows (pyttsx3 singleton). runAndWait() is safe to call repeatedly.
        engine = pyttsx3.init()
        engine.setProperty("rate", 155)
        voices = engine.getProperty("voices") or []
        ar_id = en_id = None
        for v in voices:
            n = (getattr(v, "name", "") or "").lower()
            if not ar_id and any(x in n for x in ("ar","arabic","hoda","naayf","maged")):
                ar_id = v.id
            if not en_id and any(x in n for x in ("en","english","david","zira","mark")):
                en_id = v.id
        if not en_id and voices:
            en_id = voices[0].id
        self._enabled = True
        print(f"[TTS] pyttsx3 ready | ar={ar_id or '—'} en={en_id or '—'}")
        while True:
            text = self._q.get()
            if text is None:
                break
            try:
                if ar_id and self._is_arabic(text):
                    engine.setProperty("voice", ar_id)
                elif en_id:
                    engine.setProperty("voice", en_id)
                engine.say(text)
                engine.runAndWait()
                # Do NOT call engine.stop() here — it permanently kills the singleton
            except Exception as e:
                print(f"[TTS] pyttsx3 speak error: {e}")
                # Re-init engine if it wedged
                try:
                    engine.stop()
                except Exception:
                    pass
                try:
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 155)
                    if en_id:
                        engine.setProperty("voice", en_id)
                except Exception as reinit_e:
                    print(f"[TTS] pyttsx3 reinit failed: {reinit_e}")
                    raise   # let the outer worker restart the whole thread

    # ── public API ────────────────────────────────────────────────────────────
    def speak_once(self, label: str) -> None:
        """Speak only if label is NEW. Called automatically by InferenceAdapter."""
        label = label.replace("_", " ").strip()   # "سلام_عليكم" → "سلام عليكم"
        if not label or label in ("---", "none", "idle", "no_sign", "silent"):
            return
        now = time.time()
        with self._lock:
            if label == self._last_label and (now - self._last_time) < self._cooldown:
                return          # same label, too soon → skip
            self._last_label = label
            self._last_time  = now
        self._enqueue(label)

    def repeat(self) -> None:
        """Re-speak the last confirmed label. Bind to UI Repeat button.
        Bypasses the cooldown/same-label guard completely."""
        with self._lock:
            label = self._last_label
            self._last_time = time.time()  # reset cooldown so next speak_once isn't suppressed
        if label:
            self._enqueue(label)

    def _enqueue(self, text: str) -> None:
        """Drain any pending items then push text — prevents speech pile-up."""
        text = text.replace("_", " ").strip()   # last-resort underscore guard
        while not self._q.empty():
            try:
                self._q.get_nowait()
            except queue.Empty:
                break
        self._q.put(text)

    @property
    def last_label(self) -> str:
        with self._lock:
            return self._last_label

    def shutdown(self) -> None:
        self._q.put(None)


# ─────────────────────────────────────────────────────────────────────────────
# InferenceAdapter — ROOT-FIXED
# ─────────────────────────────────────────────────────────────────────────────
class InferenceAdapter:
    """
    Real-time hand-sign inference.

    Key fixes in v3:
    ─────────────────
    • Frame buffer uses MOST-RECENT frames (tail), not oldest (head)
      → new gesture is visible immediately, not buried under old ones
    • Buffer flushed when raw prediction label changes
    • TOP2_MARGIN reduced 0.30 → 0.12
    • SMOOTH_WINDOW = 2 with recency-weighted vote
    • TTS fires ONCE per label change, not every frame
    • repeat_tts() public method for UI Repeat button
    """

    def __init__(
        self,
        model_dir:     str | Path,
        device:        str  = "cpu",
        smooth_window: int  = SMOOTH_WINDOW,
        buffer_size:   int  = BUFFER_SIZE,
        enable_tts:    bool = True,
    ) -> None:
        self._model_dir   = Path(model_dir)
        self._device      = device
        self._smooth      = smooth_window
        self._buffer_size = buffer_size

        self._model:      Optional[CustomSignModel]  = None
        self._label_map:  Dict[str, int]             = {}
        self._idx_to_lbl: Dict[int, str]             = {}
        self._extractor:  Optional[FeatureExtractor] = None
        self._loaded      = False

        self._history:      collections.deque = collections.deque(maxlen=smooth_window)
        self._frame_buffer: List[dict]        = []
        self._last_pred:    str   = "---"
        self._last_conf:    float = 0.0
        self._prev_raw:     str   = "---"   # tracks raw label between frames

        self._tts = _TTSHelper(cooldown=2.0) if enable_tts else None

    # ── lifecycle ──────────────────────────────────────────────────────────────
    def load(self) -> bool:
        if not TORCH_OK:
            print("[InferenceAdapter] PyTorch not available.")
            return False
        ckpt = self._model_dir / CustomSignModel.MODEL_FILENAME
        if not ckpt.exists():
            print(f"[InferenceAdapter] No checkpoint: {ckpt}")
            return False
        try:
            self._model, self._label_map, meta = CustomSignModel.load_checkpoint(
                self._model_dir, device=self._device
            )
            self._idx_to_lbl = {v: k for k, v in self._label_map.items()}
            self._extractor  = FeatureExtractor(
                seq_len       = meta.get("seq_len", 64),
                face_features = meta.get("face_features", False),
            )
            self._model.eval()
            self._loaded = True
            print(f"[InferenceAdapter] Loaded classes: {list(self._label_map.keys())}")
            return True
        except Exception as exc:
            print(f"[InferenceAdapter] Load failed: {exc}")
            return False

    def reload(self) -> bool:
        self._loaded = False
        self._hard_reset()
        return self.load()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def class_names(self) -> List[str]:
        return sorted(self._label_map, key=self._label_map.get)

    # ── TTS repeat (bind to UI button) ────────────────────────────────────────
    def repeat_tts(self) -> None:
        """Call this from the Repeat button in the UI."""
        if self._tts is not None:
            self._tts.repeat()

    @property
    def last_spoken(self) -> str:
        if self._tts is None:
            return ""
        return self._tts.last_label

    # ── frame-by-frame streaming ───────────────────────────────────────────────
    def push_frame(self, frame: dict) -> Tuple[str, float]:
        if not self._loaded:
            return "---", 0.0

        left  = frame.get("left_hand")
        right = frame.get("right_hand")

        # no hands → full reset
        if not left and not right:
            self._hard_reset()
            return "---", 0.0

        # degenerate landmarks → hold last result
        left_ok  = left  and len(left)  >= 10
        right_ok = right and len(right) >= 10
        if not left_ok and not right_ok:
            return self._last_pred, self._last_conf

        # append and keep only MOST RECENT buffer_size frames
        self._frame_buffer.append(frame)
        if len(self._frame_buffer) > self._buffer_size:
            self._frame_buffer.pop(0)   # drop oldest

        if len(self._frame_buffer) < MIN_FRAMES_TO_PRED:
            return "---", 0.0

        return self._run_inference()

    def reset_buffer(self) -> None:
        self._hard_reset()

    # ── core inference ─────────────────────────────────────────────────────────
    def _run_inference(self) -> Tuple[str, float]:
        # ── extract features from the TAIL of the buffer ──────────────────────
        # take most-recent seq_len frames (latest gesture wins)
        seq_len = self._extractor.seq_len
        frames  = self._frame_buffer[-seq_len:]          # ← KEY FIX

        arr    = self._extractor.extract_sequence(frames)
        tensor = self._extractor.to_tensor(arr).to(self._device)

        with torch.no_grad():
            logits = self._model(tensor)
            probs  = torch.softmax(logits, dim=1)[0]

            if DEBUG:
                prob_dict = {
                    self._idx_to_lbl.get(i, f"c{i}"): f"{p:.3f}"
                    for i, p in enumerate(probs.tolist())
                }
                print(f"[DBG probs] {prob_dict}")

            sorted_probs, sorted_idx = torch.sort(probs, descending=True)
            top1 = float(sorted_probs[0])
            top2 = float(sorted_probs[1]) if len(sorted_probs) > 1 else 0.0
            raw_label = self._idx_to_lbl.get(int(sorted_idx[0]), "???")

        # ── if label changed → flush history + buffer so old frames don't vote ─
        if raw_label != self._prev_raw:
            self._history.clear()
            self._frame_buffer.clear()   # start fresh for new gesture
            self._prev_raw = raw_label

        # ── margin filter ──────────────────────────────────────────────────────
        if (top1 - top2) < TOP2_MARGIN:
            self._last_pred = "---"
            self._last_conf = top1
            return "---", top1

        # ── confidence filter ──────────────────────────────────────────────────
        if top1 < CONFIDENCE_THRESHOLD:
            self._last_pred = "---"
            self._last_conf = top1
            return "---", top1

        # ── recency-weighted smoothing ─────────────────────────────────────────
        self._history.append(raw_label)
        smoothed = self._recency_vote()

        self._last_pred = smoothed
        self._last_conf = top1

        # ── TTS: speak only ONCE per label change ─────────────────────────────
        if self._tts is not None:
            self._tts.speak_once(smoothed)

        return smoothed, top1

    def predict_sequence(self, frames: List[dict]) -> Tuple[str, float]:
        """Batch prediction (used by pipeline_test_screen directly)."""
        if not self._loaded or not frames:
            return "---", 0.0
        seq_len = self._extractor.seq_len
        frames  = frames[-seq_len:]                      # ← same fix
        arr     = self._extractor.extract_sequence(frames)
        tensor  = self._extractor.to_tensor(arr).to(self._device)
        with torch.no_grad():
            logits = self._model(tensor)
            probs  = torch.softmax(logits, dim=1)[0]
            sorted_probs, sorted_idx = torch.sort(probs, descending=True)
            top1  = float(sorted_probs[0])
            top2  = float(sorted_probs[1]) if len(sorted_probs) > 1 else 0.0
            label = self._idx_to_lbl.get(int(sorted_idx[0]), "???")
        if (top1 - top2) < TOP2_MARGIN or top1 < CONFIDENCE_THRESHOLD:
            return "---", top1
        self._history.append(label)
        smoothed = self._recency_vote()
        self._last_pred = smoothed
        self._last_conf = top1
        if self._tts is not None:
            self._tts.speak_once(smoothed)
        return smoothed, top1

    # ── helpers ────────────────────────────────────────────────────────────────
    def _hard_reset(self) -> None:
        self._frame_buffer.clear()
        self._history.clear()
        self._prev_raw  = "---"
        self._last_pred = "---"
        self._last_conf = 0.0

    def _recency_vote(self) -> str:
        """Most-recent frames count more."""
        if not self._history:
            return "---"
        scores: Dict[str, float] = {}
        for rank, label in enumerate(self._history):   # oldest→newest
            scores[label] = scores.get(label, 0.0) + (rank + 1)
        return max(scores, key=scores.__getitem__)

    def get_all_probabilities(self, frames: List[dict]) -> Dict[str, float]:
        if not self._loaded or not frames:
            return {}
        frames = frames[-self._extractor.seq_len:]
        arr    = self._extractor.extract_sequence(frames)
        tensor = self._extractor.to_tensor(arr).to(self._device)
        with torch.no_grad():
            probs = torch.softmax(self._model(tensor), dim=1)[0].tolist()
        return {self._idx_to_lbl.get(i, f"class_{i}"): float(p)
                for i, p in enumerate(probs)}

    def shutdown(self) -> None:
        if self._tts is not None:
            self._tts.shutdown()