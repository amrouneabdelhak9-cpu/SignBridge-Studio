# backend/alphabet_inference_engine.py
"""Alphabet Inference Engine — PySide6/QThread integration for SignBridge Studio."""
import sys
import os

# [CHANGED] Block problematic modules BEFORE any other import
sys.modules['jax'] = None
sys.modules['sklearn'] = None

# Add project root to path so we can import model.hand_detector
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import cv2
import numpy as np
import json
import math
import threading
from collections import deque
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Slot, QTimer, QThread
from model.hand_detector import HandDetector

# ─── paths ────────────────────────────────────────────────────────────────────
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(_PROJECT_DIR, "model")
MODEL_FILE    = "asl_alphabet_model_fixed.h5"
METADATA_FILE = "metadata.json"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILE)
METADATA_PATH = os.path.join(MODEL_DIR, METADATA_FILE)


# ─── helpers ──────────────────────────────────────────────────────────────────
def normalize_landmarks(landmarks):
    arr = np.array(landmarks, dtype=np.float32)
    arr -= arr[0]
    mv = np.max(np.abs(arr))
    if mv > 0:
        arr /= mv
    return arr.flatten()


# ─── NLP (optional) — SAFE import, no scikit-learn dependency ─────────────────
NLTK_AVAILABLE = False
NLPProcessor = None

try:
    # Block scikit-learn from loading via nltk
    import importlib

    sys.modules['sklearn'] = None
    sys.modules['sklearn.feature_extraction'] = None

    import nltk
    from nltk.corpus import words as nltk_words

    NLTK_AVAILABLE = True


    class NLPProcessor:
        def __init__(self):
            self.word_list = set()
            self.enabled = NLTK_AVAILABLE
            if NLTK_AVAILABLE:
                try:
                    try:
                        nltk.data.find("corpora/words")
                    except LookupError:
                        nltk.download("words", quiet=True)
                    self.word_list = set(w.lower() for w in nltk_words.words())
                except Exception:
                    self.enabled = False

        def get_suggestions(self, partial: str, max_n: int = 3):
            if not self.enabled or not partial:
                return []
            p = partial.lower()
            return sorted((w for w in self.word_list if w.startswith(p)), key=len)[:max_n]

        def autocorrect(self, word: str) -> str:
            if not self.enabled or not word:
                return word
            w = word.lower()
            if w in self.word_list:
                return word
            closest = self._closest(w)
            return closest.upper() if closest else word

        def _closest(self, word, max_dist=2):
            best, bdist = None, float("inf")
            for c in self.word_list:
                if abs(len(c) - len(word)) > max_dist:
                    continue
                d = self._edit(word, c)
                if d < bdist:
                    bdist, best = d, c
                if bdist == 0:
                    break
            return best if bdist <= max_dist else None

        @staticmethod
        def _edit(s1, s2):
            if len(s1) < len(s2): s1, s2 = s2, s1
            if not s2: return len(s1)
            prev = list(range(len(s2) + 1))
            for c1 in s1:
                cur = [prev[0] + 1]
                for j, c2 in enumerate(s2):
                    cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (c1 != c2)))
                prev = cur
            return prev[-1]

except Exception:
    # If nltk fails completely, create a dummy NLPProcessor
    class NLPProcessor:
        def __init__(self):
            self.word_list = set()
            self.enabled = False

        def get_suggestions(self, partial, max_n=3):
            return []

        def autocorrect(self, word):
            return word

# ─── TTS (optional) ───────────────────────────────────────────────────────────
try:
    import pyttsx3

    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class TextToSpeech:
    def __init__(self):
        self.enabled = TTS_AVAILABLE
        self._lock = threading.Lock()
        self._busy = False

    def speak(self, text: str, interrupt: bool = False):
        if not self.enabled or not text:
            return
        if self._busy and not interrupt:
            return

        def _run():
            with self._lock:
                self._busy = True
                try:
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 165)
                    engine.setProperty("volume", 0.9)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                    del engine
                except Exception:
                    pass
                finally:
                    self._busy = False

        threading.Thread(target=_run, daemon=True).start()


# ─── Worker (runs in QThread) ─────────────────────────────────────────────────
class AlphabetWorker(QObject):
    frame_ready = Signal(object)  # np.ndarray BGR
    sign_predicted = Signal(str, float)  # sign, confidence
    sentence_updated = Signal(str)  # current full text
    word_completed = Signal(str)  # word finished on SPACE
    status_changed = Signal(str)  # running | standby | error
    fps_updated = Signal(float)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.detector = HandDetector()
        self.nlp = NLPProcessor()
        self.tts = TextToSpeech()

        # Load model + metadata
        if not os.path.exists(METADATA_PATH):
            raise FileNotFoundError(f"Metadata not found: {METADATA_PATH}")
        with open(METADATA_PATH) as f:
            meta = json.load(f)
        self.class_names = meta["class_names"]
        self.num_classes = meta["num_classes"]
        self.seq_len = meta["sequence_length"]
        self.landmark_dim = meta["landmark_dim"]
        self.test_acc = meta["test_results"]["compile_metrics"]

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

        # [CHANGED] Use tensorflow.keras directly
        import tensorflow as tf
        self.model = tf.keras.models.load_model(MODEL_PATH, compile=False)

        # Settings
        self.speak_letters = True
        self.speak_words = True
        self.auto_correct = True
        self.show_suggestions = True

        # Buffers
        self.frame_buf = deque(maxlen=self.seq_len)
        self.pred_buf = deque(maxlen=9)

        # Text state
        self.current_word = ""
        self.word_history = []
        self.max_history = 8
        self.suggestions = []

        # Hold state
        self.last_sign = None
        self.hold_count = 0
        self.hold_threshold = 28

        # Runtime
        self.current_sign = "—"
        self.confidence = 0.0
        self._cam = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_frame)
        self._running = False

    # ── slots ──────────────────────────────────────────────────────────────
    @Slot()
    def start(self):
        try:
            self._cam = cv2.VideoCapture(0)
            if not self._cam.isOpened():
                self.error_occurred.emit("Cannot open camera")
                self.status_changed.emit("error")
                return
            self._running = True
            self.status_changed.emit("running")
            self._timer.start(5)
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.status_changed.emit("error")

    @Slot()
    def stop(self):
        self._running = False
        self._timer.stop()
        if self._cam:
            self._cam.release()
            self._cam = None
        self.frame_buf.clear()
        self.pred_buf.clear()
        self.last_sign = None
        self.hold_count = 0
        self.status_changed.emit("standby")

    @Slot()
    def clear_text(self):
        self.current_word = ""
        self.word_history = []
        self.suggestions = []
        self.sentence_updated.emit("")

    @Slot()
    def trigger_space(self):
        self._apply("space")

    @Slot()
    def trigger_delete(self):
        self._apply("del")

    @Slot(int)
    def use_suggestion(self, idx: int):
        if 0 <= idx < len(self.suggestions):
            self.current_word = self.suggestions[idx].upper()
            self._apply("space")

    @Slot()
    def speak_all(self):
        words = self.word_history + ([self.current_word] if self.current_word else [])
        txt = " ".join(words).strip()
        if txt:
            self.tts.speak(txt, interrupt=True)

    @Slot()
    def save_text(self):
        words = self.word_history + ([self.current_word] if self.current_word else [])
        txt = " ".join(words).strip()
        if txt:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"asl_output_{ts}.txt"
            with open(path, "w") as f:
                f.write(txt)
            self.status_changed.emit(f"saved:{path}")

    # ── core logic ───────────────────────────────────────────────────────────
    def _predict(self, seq: np.ndarray):
        probs = self.model.predict(seq[np.newaxis], verbose=0)[0]
        idx = int(np.argmax(probs))
        return self.class_names[idx], float(probs[idx])

    def _apply(self, sign: str):
        s = sign.lower()
        if s == "del":
            if self.current_word:
                self.current_word = self.current_word[:-1]
                self._update_suggestions()
                self.tts.speak("delete")
            elif self.word_history:
                removed = self.word_history.pop()
                self.tts.speak(f"removed {removed}")
            self.sentence_updated.emit(self._full_text())

        elif s == "space":
            if self.current_word:
                word = self.current_word
                if self.auto_correct and self.nlp.enabled:
                    corrected = self.nlp.autocorrect(word)
                    if corrected.upper() != word.upper():
                        word = corrected.upper()
                self.word_history.append(word)
                if len(self.word_history) > self.max_history:
                    self.word_history.pop(0)
                if self.speak_words:
                    self.tts.speak(word, interrupt=True)
                self.word_completed.emit(word)
                self.current_word = ""
                self.suggestions = []
                self.sentence_updated.emit(self._full_text())


        else:

            letter = sign.upper()

            self.current_word += letter

            self._update_suggestions()

            self.tts.speak(letter, interrupt=True)  # always speak, interrupt previous

            self.sentence_updated.emit(self._full_text())

    def _update_suggestions(self):
        if self.show_suggestions and self.nlp.enabled:
            self.suggestions = self.nlp.get_suggestions(self.current_word, 3)
        else:
            self.suggestions = []

    def _full_text(self):
        words = self.word_history + ([self.current_word] if self.current_word else [])
        return " ".join(words)

    def _process_frame(self):
        if not self._running or not self._cam:
            return

        ret, frame = self._cam.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        frame, results = self.detector.find_hands(frame)
        landmarks = self.detector.get_landmarks(results)
        hand_present = bool(landmarks)

        final_sign = self.current_sign
        conf = self.confidence

        if hand_present:
            normed = normalize_landmarks(landmarks[0])
            self.frame_buf.append(normed)

            if len(self.frame_buf) == self.seq_len:
                sign, c = self._predict(np.array(self.frame_buf, dtype=np.float32))
                self.pred_buf.append(sign)
                self.confidence = c
                self.current_sign = sign

                if len(self.pred_buf) >= 5:
                    votes = {}
                    for s in self.pred_buf:
                        votes[s] = votes.get(s, 0) + 1
                    final_sign = max(votes, key=votes.get)
                    conf = self.confidence

                    if conf >= 0.55:
                        if final_sign == self.last_sign:
                            self.hold_count += 1
                            if self.hold_count >= self.hold_threshold:
                                self._apply(final_sign)
                                self.hold_count = 0
                        else:
                            self.last_sign = final_sign
                            self.hold_count = 0
        else:
            self.frame_buf.clear()
            self.pred_buf.clear()
            self.last_sign = None
            self.hold_count = 0
            final_sign = "—"
            conf = 0.0

        self.frame_ready.emit(frame)
        self.sign_predicted.emit(final_sign, conf)


# ─── Public wrapper ───────────────────────────────────────────────────────────
class AlphabetInferenceEngine(QObject):
    frame_ready = Signal(object)
    sign_predicted = Signal(str, float)
    sentence_updated = Signal(str)
    word_completed = Signal(str)
    status_changed = Signal(str)
    fps_updated = Signal(float)
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = AlphabetWorker()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        # Forward signals
        self.worker.frame_ready.connect(self.frame_ready)
        self.worker.sign_predicted.connect(self.sign_predicted)
        self.worker.sentence_updated.connect(self.sentence_updated)
        self.worker.word_completed.connect(self.word_completed)
        self.worker.status_changed.connect(self.status_changed)
        self.worker.fps_updated.connect(self.fps_updated)
        self.worker.error_occurred.connect(self.error_occurred)

        self.thread.started.connect(self.worker.start)

    def start(self):
        if not self.thread.isRunning():
            self.thread.start()

    def stop(self):
        self.worker.stop()
        self.thread.quit()
        self.thread.wait(3000)

    def is_running(self):
        return self.worker._running

    def clear_text(self):
        self.worker.clear_text()

    def trigger_space(self):
        self.worker.trigger_space()

    def trigger_delete(self):
        self.worker.trigger_delete()

    def use_suggestion(self, idx: int):
        self.worker.use_suggestion(idx)

    def speak_all(self):
        self.worker.speak_all()

    def save_text(self):
        self.worker.save_text()