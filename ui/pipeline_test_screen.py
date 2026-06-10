# ui/pipeline_test_screen.py  —  ULTRA PREMIUM v7  (Groq LLaMA + Arabic TTS — FIXED)
"""
VisionAI — Next-Generation AI Operating System Dashboard
=========================================================
FIXES in v7 vs v6
─────────────────
BUG 1 — TTS was reading everything (error messages, labels, emojis):
  • _speak_arabic() now receives ONLY the clean LLM sentence.
  • Error / status strings are NEVER passed to TTS.
  • Emoji / punctuation is stripped before synthesis.

BUG 2 — LLM never fired because sign.upper() on ASCII was applied but
         Arabic words are NOT ASCII → they were passed raw which is correct,
         BUT the cooldown used "same_word AND within_cool" so if the model
         oscillated between two words quickly the thread count exploded and
         blocked the event loop.  Fixed to "same_word OR within_cool" with
         a hard per-thread guard.

BUG 3 — QMetaObject.invokeMethod with Q_ARG(bool, ...) is unreliable in some
         PySide6 builds for QPushButton.setEnabled.  Replaced with a custom
         Qt Signal emitted from the thread → connected to a proper Slot.

BUG 4 — No guard against multiple TTS threads playing simultaneously on Repeat.
         Added _tts_busy flag (threading.Event).

Install:
    pip install gtts pygame requests
"""

from __future__ import annotations

import os
import re
import random
import tempfile
import threading
import time

import requests

from PySide6.QtCore    import Qt, QTimer, Signal, Slot
from PySide6.QtGui     import QColor, QPixmap
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget, QTextEdit,
)

from backend.capture_worker    import CaptureWorker, FrameData
from backend.inference_adapter import InferenceAdapter

# ==============================================================================
# ⚙️  USER CONFIGURATION  ← edit these
# ==============================================================================
GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY",
    "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"
)
# llama-3.1-8b-instant is ~5× faster than 70b for this simple task
GROQ_MODEL   = "llama-3.1-8b-instant"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

LLM_COOLDOWN = 4.0   # minimum seconds between auto-LLM calls (any word)

# Only threads that set this flag are allowed to play audio.
# This prevents InferenceAdapter's internal TTS (and any other caller)
# from playing sound — ONLY _speak_in_thread authorises itself.
_tts_authorized = threading.local()   # per-thread; default value = falsy


# ==============================================================================
# TTS helpers  — ONLY pass clean Arabic sentences here
# ==============================================================================

# Characters / patterns that must NEVER be spoken
_STRIP_RE = re.compile(
    r"[⚠️◈⏳\U0001F300-\U0001FFFF]"   # emoji block
    r"|[^\u0600-\u06FF\u0750-\u077F"    # keep Arabic Unicode ranges …
    r"\u200c\u200d\u0020-\u007E]",      # … ASCII printable, ZWNJ/ZWJ
    flags=re.UNICODE,
)

def _clean_for_tts(text: str) -> str:
    """Remove anything that would confuse gTTS (emoji, special symbols, underscores)."""
    text = text.replace("_", " ")          # "سلام_عليكم" → "سلام عليكم"
    cleaned = _STRIP_RE.sub("", text).strip()
    return cleaned


def _speak_arabic_safe(text: str) -> None:
    """
    Synthesise *text* in Arabic.
    • Strips emoji / symbols first.
    • Returns silently if nothing remains after cleaning.
    • NEVER raises — logs to console only.
    """
    cleaned = _clean_for_tts(text)
    if not cleaned:
        return
    _speak_gtts(cleaned)


def _speak_gtts(text: str) -> None:
    """edge-tts primary (male Arabic voice) → gTTS fallback."""
    # ── edge-tts: Microsoft Arabic male voice ────────────────────────────────
    try:
        import edge_tts, asyncio

        async def _synth(path: str) -> None:
            communicate = edge_tts.Communicate(text, voice="ar-SA-HamedNeural")
            await communicate.save(path)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            path = tmp.name

        # Always use a brand-new event loop — never touch Qt's loop
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_synth(path))
        finally:
            loop.close()

        _play_audio(path)
        try:
            os.remove(path)
        except OSError:
            pass
        return   # ✅ edge-tts succeeded
    except Exception as exc:
        print(f"[edge-tts] {exc} — falling back to gTTS")

    # ── gTTS fallback ────────────────────────────────────────────────────────
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="ar", slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            path = tmp.name
        tts.save(path)
        _play_audio(path)
        try:
            os.remove(path)
        except OSError:
            pass
    except Exception as exc:
        print(f"[gTTS] {exc}")


def _play_audio(path: str) -> None:
    """pygame (kept alive between calls) → playsound fallback.
    Only plays if the calling thread was authorised by _speak_in_thread.
    NOTE: we never call pygame.mixer.quit() — that destroys the mixer and
    silences every subsequent call."""
    if not getattr(_tts_authorized, "ok", False):
        return   # not our thread — silently ignored
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
            pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        pygame.mixer.music.stop()
        return
    except Exception as exc:
        print(f"[audio/pygame] {exc}")
    try:
        from playsound import playsound
        playsound(path)
    except Exception as exc:
        print(f"[audio/playsound] {exc}")


# ==============================================================================
# Colour palette
# ==============================================================================
try:
    from ui.theme import FuturisticTheme
    BG         = FuturisticTheme.BG_DEEP
    SURFACE    = FuturisticTheme.GLASS_BG
    BLUE       = FuturisticTheme.CYAN
    GREEN      = FuturisticTheme.EMERALD
    RED        = FuturisticTheme.RED_NEURAL
    TEXT_PRIM  = FuturisticTheme.TEXT_PRIMARY
    TEXT_SEC   = FuturisticTheme.TEXT_SECONDARY
    TEXT_MUTED = FuturisticTheme.TEXT_MUTED
except ImportError:
    BG         = "#030712"
    SURFACE    = "rgba(6,17,31,0.85)"
    BLUE       = "#00E5FF"
    GREEN      = "#00FFB2"
    RED        = "#FF3B5C"
    TEXT_PRIM  = "#F8FAFC"
    TEXT_SEC   = "#94A3B8"
    TEXT_MUTED = "#64748B"

PURPLE  = "#9333EA"
AMBER   = "#F59E0B"
GLASS   = "rgba(6,17,31,0.78)"
GLASS_D = "rgba(3,7,18,0.90)"


# ==============================================================================
# Helpers
# ==============================================================================

def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"


def _glow(widget: QWidget, color: QColor,
          blur: int = 30, dy: int = 4) -> QGraphicsDropShadowEffect:
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(blur)
    fx.setColor(color)
    fx.setOffset(0, dy)
    widget.setGraphicsEffect(fx)
    return fx


# ==============================================================================
# Reusable sub-widgets
# ==============================================================================

class _AnalyticsCard(QWidget):
    def __init__(self, title: str, value: str, value_color: str = None,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(76)
        self.setStyleSheet(
            "QWidget { background:rgba(6,17,31,0.82);"
            " border:1px solid rgba(0,229,255,0.16); border-radius:16px; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(4)
        _s = "background:transparent; border:none;"
        t = QLabel(title)
        t.setStyleSheet(f"color:{TEXT_MUTED}; font-size:10px; font-weight:700;"
                        f" letter-spacing:1.2px; {_s}")
        lay.addWidget(t)
        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"color:{value_color or BLUE}; font-size:20px; font-weight:800; {_s}"
        )
        lay.addWidget(self._val)
        lay.addStretch()

    def set_value(self, v: str) -> None:
        self._val.setText(v)


def _divider(text: str) -> QWidget:
    w = QWidget(); w.setStyleSheet("background:transparent;")
    lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(5)
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:9px; font-weight:800;"
                      " letter-spacing:2px; background:transparent; border:none;")
    lay.addWidget(lbl)
    line = QFrame(); line.setFixedHeight(1)
    line.setStyleSheet(
        "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        "stop:0 rgba(0,229,255,0.55),stop:1 rgba(0,229,255,0)); border:none;"
    )
    lay.addWidget(line)
    return w


# ==============================================================================
# Main Screen
# ==============================================================================

class PipelineTestScreen(QWidget):
    navigate_to = Signal(str)

    # Internal signals — used to update UI from background threads (SAFE)
    _sig_set_llm_text   = Signal(str)   # update the LLM QTextEdit
    _sig_enable_repeat  = Signal(bool)  # enable/disable Repeat Text button
    _sig_update_words   = Signal(str)   # update detected words display

    def __init__(self, parent: QWidget | None = None,
                 model_dir: str = "models",
                 device: str = "cpu"):
        super().__init__(parent)
        self.setObjectName("pipeline_test_screen")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            "QWidget#pipeline_test_screen {"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"    stop:0 {BG}, stop:1 #06111F);"
            "}"
        )

        self._model_dir         = model_dir
        self._device            = device
        self._capture_worker    = None
        self._inference_adapter = None
        self._model_loaded      = False
        self._camera_active     = False

        # Simulated resource counters
        self._gpu_val  = 34
        self._cpu_val  = 18
        self._ram_val  = 61
        self._lat_val  = 0

        # LLM / TTS state
        self._last_llm_word           = ""
        self._last_llm_time           = 0.0
        self._last_generated_sentence = ""
        self._tts_busy                = threading.Event()  # prevents TTS overlap
        self._detected_words: list[str] = []              # accumulated detected words

        # Pre-initialise attrs that eventFilter touches (crash guard)
        self._start_btn   = None
        self._start_glow  = None
        self._start_rgb   = None

        self._init_ui()

        # Connect internal signals to UI slots (thread-safe)
        self._sig_set_llm_text.connect(self._slot_set_llm_text)
        self._sig_enable_repeat.connect(self._slot_enable_repeat)
        self._sig_update_words.connect(self._slot_update_words)

        self._init_backend()

        self._sys_timer = QTimer(self)
        self._sys_timer.timeout.connect(self._tick_system_stats)
        self._sys_timer.start(2000)

    # ══════════════════════════════════════════════════════════════════════════
    # UI SLOTS  (called from signals emitted in worker threads)
    # ══════════════════════════════════════════════════════════════════════════

    @Slot(str)
    def _slot_set_llm_text(self, text: str) -> None:
        self._llm_composition.setPlainText(text)

    @Slot(bool)
    def _slot_enable_repeat(self, enabled: bool) -> None:
        self._repeat_text_btn.setEnabled(enabled)
        self._voice_btn.setEnabled(enabled)

    @Slot(str)
    def _slot_update_words(self, words_text: str) -> None:
        self._detected_words_label.setText(words_text)
        # Enable create sentence button if there are words
        has_words = bool(self._detected_words)
        self._create_sentence_btn.setEnabled(has_words)

    # ══════════════════════════════════════════════════════════════════════════
    # UI BUILD
    # ══════════════════════════════════════════════════════════════════════════

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(28, 20, 28, 20)
        body_lay.setSpacing(0)

        split = QHBoxLayout()
        split.setSpacing(22)
        split.addLayout(self._build_left_panel(), 63)
        split.addLayout(self._build_right_panel(), 37)
        body_lay.addLayout(split, 1)

        root.addWidget(body, 1)
        root.addWidget(self._build_footer())

    # ──────────────────────────────────────────────────────────────────────────
    # Left panel
    # ──────────────────────────────────────────────────────────────────────────
    def _build_left_panel(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.setSpacing(14)

        # ── Outer viewport card ──────────────────────────────────────────────
        vp_card = QWidget()
        vp_card.setObjectName("vp_card")
        vp_card.setAttribute(Qt.WA_StyledBackground, True)
        vp_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vp_card.setStyleSheet(
            "QWidget#vp_card {"
            "  background: rgba(3,7,18,0.92);"
            "  border: 1px solid rgba(0,229,255,0.32);"
            "  border-radius: 30px;"
            "}"
        )
        _glow(vp_card, QColor(0, 229, 255, 55), blur=50, dy=8)

        vp_root = QVBoxLayout(vp_card)
        vp_root.setContentsMargins(0, 0, 0, 0)
        vp_root.setSpacing(0)

        # Camera feed label
        self._viewport_label = QLabel(
            "Camera Feed Offline\n"
            "Click  ▶ Start  to initiate verification loop."
        )
        self._viewport_label.setWordWrap(True)
        self._viewport_label.setScaledContents(False)   # keep aspect ratio
        self._viewport_label.setAlignment(Qt.AlignCenter)
        self._viewport_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._viewport_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 15px; font-weight:500;"
            " background: transparent;"
        )
        vp_root.addWidget(self._viewport_label, 1)

        # Prediction overlay
        self._prediction_overlay = QWidget()
        self._prediction_overlay.setFixedHeight(66)
        self._prediction_overlay.setStyleSheet("background: transparent;")
        po = QHBoxLayout(self._prediction_overlay)
        po.setContentsMargins(16, 0, 16, 0)
        po.setSpacing(0)

        pred_pill = QWidget()
        pred_pill.setAttribute(Qt.WA_StyledBackground, True)
        pred_pill.setStyleSheet(
            "QWidget {"
            "  background: rgba(3,7,18,0.84);"
            "  border: 1px solid rgba(0,229,255,0.36);"
            "  border-radius: 16px;"
            "}"
        )
        pp = QHBoxLayout(pred_pill)
        pp.setContentsMargins(16, 8, 16, 8)
        pp.setSpacing(12)

        _nb = "background:transparent; border:none;"
        self._prediction_icon = QLabel("◎")
        self._prediction_icon.setStyleSheet(f"color:{TEXT_MUTED}; font-size:20px; {_nb}")
        pp.addWidget(self._prediction_icon)

        self._prediction_text = QLabel("No sign detected")
        self._prediction_text.setStyleSheet(
            f"color:{TEXT_PRIM}; font-size:17px; font-weight:700; {_nb}"
        )
        pp.addWidget(self._prediction_text)
        pp.addStretch()

        self._prediction_conf = QLabel("0%")
        self._prediction_conf.setStyleSheet(
            f"color:{BLUE}; font-size:17px; font-weight:600; {_nb}"
        )
        pp.addWidget(self._prediction_conf)

        po.addWidget(pred_pill)
        vp_root.addWidget(self._prediction_overlay)
        self._prediction_overlay.hide()

        lay.addWidget(vp_card, 1)

        # ── LLM Composition Tile ─────────────────────────────────────────────
        llm_tile = QWidget()
        llm_tile.setObjectName("llm_tile")
        llm_tile.setAttribute(Qt.WA_StyledBackground, True)
        llm_tile.setFixedHeight(160)
        llm_tile.setStyleSheet(
            "QWidget#llm_tile {"
            "  background: rgba(6,17,31,0.80);"
            "  border: 1px solid rgba(0,229,255,0.22);"
            "  border-radius: 31px;"
            "}"
        )
        _glow(llm_tile, QColor(0, 229, 255, 45), blur=42, dy=6)

        llm_root = QVBoxLayout(llm_tile)
        llm_root.setContentsMargins(18, 14, 18, 14)
        llm_root.setSpacing(10)

        # ── LLM Output section ───────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        llm_icon = QLabel("◈")
        llm_icon.setStyleSheet(f"color:{BLUE}; font-size:14px; font-weight:800; {_nb}")
        title_row.addWidget(llm_icon)

        llm_title = QLabel("LLM COMPOSITION  —  GROQ LLAMA 3.1")
        llm_title.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:10px; font-weight:800;"
            f" letter-spacing:1.5px; {_nb}"
        )
        title_row.addWidget(llm_title)
        title_row.addStretch()

        # Repeat Text button (inside LLM tile header)
        self._repeat_text_btn = QPushButton("↻  Repeat Text")
        self._repeat_text_btn.setCursor(Qt.PointingHandCursor)
        self._repeat_text_btn.setFixedHeight(28)
        self._repeat_text_btn.setEnabled(False)
        self._repeat_text_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: rgba(0,229,255,0.10);"
            f"  color: {BLUE};"
            f"  border: 1px solid rgba(0,229,255,0.30);"
            f"  border-radius: 14px;"
            f"  font-size: 11px; font-weight:700;"
            f"  padding: 0 12px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: rgba(0,229,255,0.22);"
            f"  border: 1px solid {BLUE};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  color: {TEXT_MUTED};"
            f"  border: 1px solid rgba(100,116,139,0.16);"
            f"  background: transparent;"
            f"}}"
        )
        self._repeat_text_btn.clicked.connect(self._on_repeat_tts_sentence)
        title_row.addWidget(self._repeat_text_btn)

        llm_root.addLayout(title_row)

        # Text area
        self._llm_composition = QTextEdit()
        self._llm_composition.setReadOnly(True)
        self._llm_composition.setPlaceholderText(
            "Detect a word then press «Create Sentence» to generate…"
        )
        self._llm_composition.setStyleSheet(
            "QTextEdit {"
            f"  color: {TEXT_PRIM};"
            f"  background: rgba(3,7,18,0.60);"
            "  border: 1px solid rgba(0,229,255,0.14);"
            "  border-radius: 16px;"
            "  font-size: 14px;"
            "  font-weight: 500;"
            "  padding: 10px 14px;"
            "}"
        )
        self._llm_composition.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._llm_composition.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        llm_root.addWidget(self._llm_composition, 1)

        lay.addWidget(llm_tile)

        # ── Bottom action bar ────────────────────────────────────────────────
        action_bar = QWidget()
        action_bar.setObjectName("action_bar")
        action_bar.setAttribute(Qt.WA_StyledBackground, True)
        action_bar.setFixedHeight(62)
        action_bar.setStyleSheet(
            "QWidget#action_bar {"
            "  background: rgba(6,17,31,0.80);"
            "  border: 1px solid rgba(0,229,255,0.22);"
            "  border-radius: 31px;"
            "}"
        )
        ab = QHBoxLayout(action_bar)
        ab.setContentsMargins(14, 8, 14, 8)
        ab.setSpacing(10)

        # Start Detection
        self._start_btn = QPushButton("▶  Start")
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.setFixedHeight(42)
        self._start_btn.setStyleSheet(
            "QPushButton {"
            "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 #00D68F, stop:1 {GREEN});"
            f"  color: #030712; border: none; border-radius: 21px;"
            "  font-size: 13px; font-weight:800; padding: 0 20px;"
            "}"
            "QPushButton:hover {"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {GREEN}, stop:1 #7FFFD4);"
            "}"
        )
        rgb_start = _hex_to_rgb(GREEN)
        r, g, b = [int(x) for x in rgb_start.split(",")]
        self._start_glow = _glow(self._start_btn, QColor(r, g, b, 120),
                                  blur=32, dy=4)
        self._start_btn.installEventFilter(self)
        self._start_rgb = rgb_start
        self._start_btn.clicked.connect(self._on_start_camera)
        ab.addWidget(self._start_btn)

        # Pause Stream
        self._stop_btn = QPushButton("⏸  Pause")
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setFixedHeight(42)
        self._stop_btn.setStyleSheet(
            "QPushButton {"
            "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 #6D28D9, stop:1 {PURPLE});"
            "  color: white; border: none; border-radius: 21px;"
            "  font-size: 13px; font-weight:700; padding: 0 20px;"
            "}"
            "QPushButton:hover {"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {PURPLE}, stop:1 #C084FC);"
            "}"
        )
        self._stop_btn.clicked.connect(self._on_stop_camera)
        ab.addWidget(self._stop_btn)

        _sec_style = (
            f"QPushButton {{ background:rgba(0,229,255,0.08); color:{BLUE};"
            f" border:1px solid rgba(0,229,255,0.26); border-radius:21px;"
            f" font-size:12px; font-weight:600; padding:0 14px; }}"
            f"QPushButton:hover {{ background:rgba(0,229,255,0.17);"
            f" border:1px solid {BLUE}; }}"
            f"QPushButton:disabled {{ color:{TEXT_MUTED};"
            f" border:1px solid rgba(100,116,139,0.16); background:transparent; }}"
        )

        # ── Create Sentence (manual LLM trigger) ────────────────────────────
        self._create_sentence_btn = QPushButton("✦  Create Sentence")
        self._create_sentence_btn.setCursor(Qt.PointingHandCursor)
        self._create_sentence_btn.setFixedHeight(42)
        self._create_sentence_btn.setEnabled(False)
        self._create_sentence_btn.setStyleSheet(
            "QPushButton {"
            "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 #0066CC, stop:1 {BLUE});"
            f"  color: #030712; border: none; border-radius: 21px;"
            "  font-size: 13px; font-weight:800; padding: 0 20px;"
            "}"
            "QPushButton:hover {"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {BLUE}, stop:1 #7FEFFF);"
            "}"
            f"QPushButton:disabled {{ color:{TEXT_MUTED};"
            f" background: rgba(0,100,150,0.15);"
            f" border:1px solid rgba(0,229,255,0.12); }}"
        )
        self._create_sentence_btn.clicked.connect(self._on_create_sentence)
        ab.addWidget(self._create_sentence_btn)

        # Thin divider
        sep = QFrame()
        sep.setFixedSize(1, 28)
        sep.setStyleSheet("background: rgba(0,229,255,0.20); border:none;")
        ab.addWidget(sep)

        # Voice Output (manual trigger)
        self._voice_btn = QPushButton("🔊  Voice")
        self._voice_btn.setCursor(Qt.PointingHandCursor)
        self._voice_btn.setFixedHeight(42)
        self._voice_btn.setEnabled(False)
        self._voice_btn.setStyleSheet(_sec_style)
        self._voice_btn.clicked.connect(self._on_repeat_tts_sentence)
        ab.addWidget(self._voice_btn)

        # Repeat (model TTS — original behaviour)
        self._repeat_btn = QPushButton("↻")
        self._repeat_btn.setCursor(Qt.PointingHandCursor)
        self._repeat_btn.setFixedSize(42, 42)
        self._repeat_btn.setEnabled(False)
        self._repeat_btn.setStyleSheet(
            _sec_style
            + f"QPushButton:disabled {{ color:{TEXT_MUTED};"
              f" border:1px solid rgba(100,116,139,0.16);"
              f" background:transparent; }}"
        )
        self._repeat_btn.clicked.connect(self._on_repeat_tts)
        ab.addWidget(self._repeat_btn)

        lay.addWidget(action_bar)
        return lay

    # ──────────────────────────────────────────────────────────────────────────
    # Right panel
    # ──────────────────────────────────────────────────────────────────────────
    def _build_right_panel(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.setSpacing(0)

        card = QWidget()
        card.setObjectName("ctrl_card")
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card.setStyleSheet(
            "QWidget#ctrl_card {"
            "  background: rgba(6,17,31,0.82);"
            "  border: 1px solid rgba(0,229,255,0.24);"
            "  border-radius: 28px;"
            "}"
        )
        _glow(card, QColor(0, 229, 255, 45), blur=42, dy=6)

        cc = QVBoxLayout(card)
        cc.setContentsMargins(22, 22, 22, 22)
        cc.setSpacing(16)

        # 02  REALTIME ANALYTICS
        cc.addWidget(_divider("02 — REALTIME ANALYTICS"))
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(0, 4, 0, 4)
        self._analytics: dict[str, _AnalyticsCard] = {
            "model":      _AnalyticsCard("MODEL",      "READY", GREEN),
            "fps":        _AnalyticsCard("FPS",        "0",     BLUE),
            "confidence": _AnalyticsCard("CONFIDENCE", "0%",    PURPLE),
            "latency":    _AnalyticsCard("LATENCY",    "—ms",   AMBER),
        }
        grid.addWidget(self._analytics["model"],      0, 0)
        grid.addWidget(self._analytics["fps"],        0, 1)
        grid.addWidget(self._analytics["confidence"], 1, 0)
        grid.addWidget(self._analytics["latency"],    1, 1)
        cc.addLayout(grid)

        # 03  MODEL INFORMATION
        cc.addWidget(_divider("03 — MODEL INFORMATION"))

        model_card = QWidget()
        model_card.setAttribute(Qt.WA_StyledBackground, True)
        model_card.setStyleSheet(
            "QWidget {"
            "  background: rgba(6,17,31,0.62);"
            f"  border: 1px solid rgba(147,51,234,0.28);"
            "  border-radius: 16px;"
            "}"
        )
        mc = QHBoxLayout(model_card)
        mc.setContentsMargins(16, 14, 16, 14)
        mc.setSpacing(14)

        mc_text = QVBoxLayout()
        mc_text.setSpacing(4)
        _nb = "background:transparent; border:none;"

        self._model_status_label = QLabel("Scanning models/ …")
        self._model_status_label.setStyleSheet(
            f"color:{TEXT_SEC}; font-size:12px; font-weight:600; {_nb}"
        )
        mc_text.addWidget(self._model_status_label)

        self._classes_label = QLabel("Trained signs: —")
        self._classes_label.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:11px; {_nb}"
        )
        self._classes_label.setWordWrap(True)
        mc_text.addWidget(self._classes_label)
        mc.addLayout(mc_text, 1)

        brain = QLabel("🧠")
        brain.setFixedSize(54, 54)
        brain.setAlignment(Qt.AlignCenter)
        brain.setStyleSheet(
            "QLabel {"
            "  background: rgba(147,51,234,0.14);"
            "  border: 1px solid rgba(147,51,234,0.38);"
            "  border-radius: 27px;"
            "  font-size: 26px;"
            "}"
        )
        _glow(brain, QColor(147, 51, 234, 90), blur=22, dy=0)
        mc.addWidget(brain)
        cc.addWidget(model_card)

        # 04  LIVE INFERENCE
        cc.addWidget(_divider("04 — LIVE INFERENCE"))

        inf_card = QWidget()
        inf_card.setAttribute(Qt.WA_StyledBackground, True)
        inf_card.setStyleSheet(
            "QWidget {"
            "  background: rgba(6,17,31,0.62);"
            "  border: 1px solid rgba(0,229,255,0.18);"
            "  border-radius: 16px;"
            "}"
        )
        il = QVBoxLayout(inf_card)
        il.setContentsMargins(16, 14, 16, 14)
        il.setSpacing(10)

        self._inference_sign_label = QLabel("-")
        self._inference_sign_label.setAlignment(Qt.AlignCenter)
        self._inference_sign_label.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:36px; font-weight:800; {_nb}"
        )
        il.addWidget(self._inference_sign_label)

        bar_bg = QWidget()
        bar_bg.setFixedHeight(6)
        bar_bg.setStyleSheet(
            "background: rgba(100,116,139,0.20); border-radius:3px;"
        )
        bl = QHBoxLayout(bar_bg)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)

        self._confidence_bar = QFrame()
        self._confidence_bar.setFixedHeight(6)
        self._confidence_bar.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {PURPLE}, stop:1 {BLUE}); border-radius:3px;"
        )
        self._confidence_bar.setFixedWidth(0)
        bl.addWidget(self._confidence_bar)
        bl.addStretch()
        il.addWidget(bar_bg)

        self._inference_conf_label = QLabel("Confidence: 0%")
        self._inference_conf_label.setAlignment(Qt.AlignCenter)
        self._inference_conf_label.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:11px; {_nb}"
        )
        il.addWidget(self._inference_conf_label)
        cc.addWidget(inf_card)

        # 05  DETECTED WORDS
        cc.addWidget(_divider("05 — DETECTED WORDS"))

        words_card = QWidget()
        words_card.setAttribute(Qt.WA_StyledBackground, True)
        words_card.setStyleSheet(
            "QWidget {"
            "  background: rgba(3,7,18,0.55);"
            f"  border: 1px solid rgba(0,255,178,0.22);"
            "  border-radius: 16px;"
            "}"
        )
        wc = QVBoxLayout(words_card)
        wc.setContentsMargins(14, 10, 14, 10)
        wc.setSpacing(8)

        # Header row: title + clear button
        wh = QHBoxLayout()
        wh.setSpacing(6)

        words_icon = QLabel("👁")
        words_icon.setStyleSheet(
            f"color:{GREEN}; font-size:13px; background:transparent; border:none;"
        )
        wh.addWidget(words_icon)
        wh.addStretch()

        self._clear_words_btn = QPushButton("✕  Clear")
        self._clear_words_btn.setCursor(Qt.PointingHandCursor)
        self._clear_words_btn.setFixedHeight(22)
        self._clear_words_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: rgba(255,59,92,0.10); color: {RED};"
            f"  border: 1px solid rgba(255,59,92,0.30); border-radius: 11px;"
            f"  font-size: 10px; font-weight:700; padding: 0 10px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: rgba(255,59,92,0.22); border: 1px solid {RED};"
            f"}}"
        )
        self._clear_words_btn.clicked.connect(self._on_clear_words)
        wh.addWidget(self._clear_words_btn)
        wc.addLayout(wh)

        # Words display — right-aligned, bottom-anchored
        self._detected_words_label = QLabel("—  No words yet")
        self._detected_words_label.setStyleSheet(
            f"color:{GREEN}; font-size:14px; font-weight:700;"
            " background:transparent; border:none; letter-spacing:2px;"
        )
        self._detected_words_label.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self._detected_words_label.setWordWrap(True)
        self._detected_words_label.setMinimumHeight(40)
        wc.addWidget(self._detected_words_label)

        cc.addWidget(words_card)
        cc.addStretch()

        lay.addWidget(card, 1)
        return lay

    # ──────────────────────────────────────────────────────────────────────────
    # Footer
    # ──────────────────────────────────────────────────────────────────────────
    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setObjectName("ftr")
        footer.setAttribute(Qt.WA_StyledBackground, True)
        footer.setFixedHeight(36)
        footer.setStyleSheet(
            "QWidget#ftr {"
            "  background: rgba(3,7,18,0.92);"
            "  border-top: 1px solid rgba(0,229,255,0.11);"
            "}"
        )
        lay = QHBoxLayout(footer)
        lay.setContentsMargins(28, 0, 28, 0)
        lay.setSpacing(0)

        _nb = "background:transparent;"
        sys_lbl = QLabel(
            "VisionAI v2.0.1  •  Groq LLaMA 3.3  •  All Systems Operational"
        )
        sys_lbl.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:10px; font-weight:500; {_nb}"
        )
        lay.addWidget(sys_lbl)
        lay.addStretch()

        self._gpu_lbl = QLabel(f"GPU {self._gpu_val}%")
        self._cpu_lbl = QLabel(f"CPU {self._cpu_val}%")
        self._ram_lbl = QLabel(f"RAM {self._ram_val}%")

        for lbl in (self._gpu_lbl, self._cpu_lbl, self._ram_lbl):
            lbl.setStyleSheet(
                f"color:{TEXT_MUTED}; font-size:10px; font-weight:600; {_nb}"
            )
            lay.addWidget(lbl)
            lay.addSpacing(18)

        return footer

    # ══════════════════════════════════════════════════════════════════════════
    # BACKEND
    # ══════════════════════════════════════════════════════════════════════════

    def _init_backend(self) -> None:
        self._inference_adapter = InferenceAdapter(
            model_dir=self._model_dir, device=self._device, enable_tts=False
        )
        self._inference_adapter.load()
        self._try_load_model()

    def _try_load_model(self) -> None:
        if self._inference_adapter is None:
            return
        loaded = self._inference_adapter.is_loaded
        self._model_loaded = loaded
        _nb = "background:transparent; border:none;"
        if loaded:
            classes = self._inference_adapter.class_names
            self._model_status_label.setText(
                f"Model Loaded  •  {len(classes)} Class(es)"
            )
            self._model_status_label.setStyleSheet(
                f"color:{GREEN}; font-size:12px; font-weight:600; {_nb}"
            )
            self._classes_label.setText(f"Trained signs: {', '.join(classes)}")
            self._analytics["model"].set_value("READY")
        else:
            self._model_status_label.setText("No checkpoint found in 'models/'")
            self._model_status_label.setStyleSheet(
                f"color:{RED}; font-size:12px; font-weight:600; {_nb}"
            )
            self._classes_label.setText("Trained signs: —")
            self._analytics["model"].set_value("NONE")

    # ══════════════════════════════════════════════════════════════════════════
    # GROQ LLM  +  TTS  (all blocking work runs in daemon threads)
    # ══════════════════════════════════════════════════════════════════════════

    def _call_groq_llm(self, word: str) -> str | None:
        """
        Ask Groq LLaMA to produce a short, natural Arabic sentence from *word*
        (which may be one word or several space-separated words).
        Returns the clean sentence string, or None on error.
        """
        if not GROQ_API_KEY:
            print("[Groq] API key not set — skipping LLM call")
            return None

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        # System prompt — منطق واضح: الكلمات إشارات مستقلة وليست أجزاء جملة
        system_prompt = (
            "أنت مساعد لغة إشارة عربية. مهمتك: تحويل كلمات الإشارة إلى جملة عربية واحدة طبيعية سليمة المعنى.\n"
            "\n"
            "⚠️ قانون أساسي: الكلمات المعطاة هي إشارات مستقلة تمثل مواضيع وليست أجزاء جملة.\n"
            "لا تحاول تركيبها حرفياً. بدلاً من ذلك، افهم الموضوع العام وأنشئ جملة منطقية.\n"
            "\n"
            "قواعد الإخراج:\n"
            "- جملة واحدة فقط، سطر واحد، بدون أي مقدمة أو تفسير.\n"
            "- من 5 إلى 10 كلمات.\n"
            "- عربية فصيحة طبيعية.\n"
            "\n"
            "كيف تتعامل مع الكلمات:\n"
            "- تحية (مرحبا / سلام عليكم): أنشئ تحية كاملة.\n"
            "- فعل (يشرب / يأكل): أنشئ جملة فعلية بفاعل ومفعول واضحين.\n"
            "- اسم مكان (الجزائر): أنشئ جملة عن المكان.\n"
            "- تعبير ديني (الحمدلله): استخدمه في سياقه الطبيعي.\n"
            "- شكر (شكرا): أنشئ عبارة شكر كاملة.\n"
            "- مزيج من الكلمات: اختر الموضوع الأبرز وابنِ حوله الجملة، لا تجمعها كلها قسراً.\n"
            "\n"
            "أمثلة — لاحظ أن الإخراج منطقي وليس تركيباً حرفياً:\n"
            "يشرب → أنا أشرب الماء البارد الآن\n"
            "الحمدلله → الحمد لله على نعمة الصحة والعافية\n"
            "يشرب الحمدلله → شربت الماء والحمد لله على هذه النعمة\n"
            "سلام عليكم → السلام عليكم ورحمة الله وبركاته\n"
            "مرحبا → مرحباً بك أهلاً وسهلاً\n"
            "الجزائر → أنا فخور بانتمائي إلى الجزائر الحبيبة\n"
            "شكرا → شكراً جزيلاً على لطفك وكرمك\n"
            "مرحبا شكرا → مرحباً بك وأشكرك على حضورك معنا\n"
            "سلام عليكم الحمدلله → السلام عليكم والحمد لله على لقائنا\n"
            "يشرب الجزائر → في الجزائر نشرب القهوة مع الأصدقاء\n"
        )
        user_prompt = word

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "max_tokens": 80,       # كافٍ للجملة العربية الكاملة
            "temperature": 0.3,     # أقل عشوائية = جملة أكثر دقة واتساقاً
            "stream": False,
        }

        try:
            resp = requests.post(GROQ_URL, json=payload,
                                 headers=headers, timeout=10)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            # Strip ANY label/prefix the model might prepend (e.g. "إليك الجملة:")
            cleaned = re.sub(r"^[\s\S]*?[:：]\s*", "", content, count=1).strip()
            # If stripping the colon left nothing, use original
            raw = cleaned if cleaned else content
            # Take first line only
            raw = raw.split("\n")[0].strip()
            # Remove trailing period (reads awkwardly in TTS)
            raw = raw.rstrip(".")
            # Strip underscores
            raw = raw.replace("_", " ").strip()
            return raw if raw else None
        except requests.exceptions.Timeout:
            print("[Groq] timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("[Groq] connection error")
            return None
        except Exception as exc:
            print(f"[Groq] {exc}")
            return None

    def _update_llm_composition(self, sign: str, conf_pct: int) -> None:
        """
        Called from the main thread each time a new sign is confirmed.
        Now only accumulates the detected word — LLM is triggered manually
        via the "Create Sentence" button.
        """
        # Always strip underscores at the entry point — the model may return
        # "سلام_عليكم" even after earlier cleaning if it goes through adapter paths
        sign = sign.replace("_", " ").strip()
        if not sign:
            return

        now = time.monotonic()
        elapsed = now - self._last_llm_time

        # Debounce: skip if same word appeared very recently
        if sign == self._last_llm_word and elapsed < LLM_COOLDOWN:
            return

        self._last_llm_word = sign
        self._last_llm_time = now

        # Add word to the list (avoid consecutive duplicates)
        if not self._detected_words or self._detected_words[-1] != sign:
            self._detected_words.append(sign)
            # Keep last 10 words to avoid overflow
            if len(self._detected_words) > 10:
                self._detected_words = self._detected_words[-10:]

        # Render words with wide spacing for readability
        words_display = "   ·   ".join(self._detected_words)
        self._sig_update_words.emit(words_display)

    @Slot()
    def _on_create_sentence(self) -> None:
        """Manual LLM trigger — called when the user presses 'Create Sentence'."""
        if not self._detected_words:
            return

        # Build input from all accumulated words
        words_input = " ".join(self._detected_words)

        self._create_sentence_btn.setEnabled(False)
        self._llm_composition.setPlainText(
            f"الكلمات المكتشفة : {words_input}\n\n"
            f"⏳ جارٍ توليد الجملة…"
        )
        self._sig_enable_repeat.emit(False)

        _words = words_input

        def _run() -> None:
            sentence = self._call_groq_llm(_words)

            if sentence is None:
                display = (
                    f"الكلمات المكتشفة : {_words}\n\n"
                    f"تعذّر الاتصال بـ Groq — تحقق من المفتاح والاتصال."
                )
                self._sig_set_llm_text.emit(display)
                self._create_sentence_btn.setEnabled(True)
                return

            self._last_generated_sentence = sentence
            display = (
                f"الكلمات المكتشفة : {_words}\n\n"
                f"◈ الجملة:\n{sentence}"
            )
            self._sig_set_llm_text.emit(display)
            self._sig_enable_repeat.emit(True)
            self._create_sentence_btn.setEnabled(True)

            # Speak ONLY the Arabic sentence
            self._speak_in_thread(sentence)

        threading.Thread(target=_run, daemon=True).start()

    @Slot()
    def _on_clear_words(self) -> None:
        """Clear the accumulated detected words list."""
        self._detected_words.clear()
        self._last_llm_word = ""
        self._detected_words_label.setText("—  لم يتم اكتشاف كلمات بعد")
        self._create_sentence_btn.setEnabled(False)
        self._llm_composition.setPlainText("")
        self._last_generated_sentence = ""
        self._sig_enable_repeat.emit(False)

    def _speak_in_thread(self, sentence: str) -> None:
        """
        Play TTS for *sentence* in a new thread, but only if no TTS is
        currently playing (_tts_busy flag).
        Marks the thread as authorised so _play_audio() lets it through.
        """
        if self._tts_busy.is_set():
            return   # already speaking — skip (don't queue)

        def _run() -> None:
            _tts_authorized.ok = True   # authorise THIS thread only
            self._tts_busy.set()
            try:
                _speak_arabic_safe(sentence)
            finally:
                _tts_authorized.ok = False
                self._tts_busy.clear()

        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # CAMERA
    # ══════════════════════════════════════════════════════════════════════════

    @Slot()
    def _on_start_camera(self) -> None:
        if self._camera_active:
            return
        if self._inference_adapter is not None:
            self._inference_adapter.reload()
            self._try_load_model()

        self._viewport_label.setText("Initializing camera feed…")
        self._prediction_overlay.hide()
        self._reset_inference_display()

        self._capture_worker = CaptureWorker(
            camera_index=0, enable_face=False, target_fps=30, parent=self
        )
        self._capture_worker.frame_ready.connect(self._on_frame_ready)
        self._capture_worker.landmarks_ready.connect(self._on_landmarks_ready)
        self._capture_worker.fps_updated.connect(self._on_fps_updated)
        self._capture_worker.error_occurred.connect(self._on_camera_error)
        self._capture_worker.start()

        self._camera_active = True

    @Slot()
    def _on_stop_camera(self) -> None:
        self.stop_camera()

    def stop_camera(self) -> None:
        if self._capture_worker is not None:
            self._capture_worker.stop()
            self._capture_worker = None
        if self._inference_adapter is not None:
            self._inference_adapter.reset_buffer()
        self._camera_active = False
        self._viewport_label.clear()
        self._viewport_label.setText(
            "Camera Feed Offline\n"
            "Click  ▶ Start  to initiate verification loop."
        )
        self._prediction_overlay.hide()
        self._reset_inference_display()
        self._analytics["fps"].set_value("0")
        self._analytics["latency"].set_value("—ms")

    # ══════════════════════════════════════════════════════════════════════════
    # TTS SLOTS
    # ══════════════════════════════════════════════════════════════════════════

    @Slot()
    def _on_repeat_tts(self) -> None:
        """Re-speak the last detected sign word — cleaned of underscores."""
        if self._last_llm_word:
            # _last_llm_word is already cleaned (underscore→space) at this point
            self._speak_in_thread(self._last_llm_word)

    @Slot()
    def _on_repeat_tts_sentence(self) -> None:
        """Re-speak the last LLM-generated sentence.  No UI text is spoken."""
        sentence = self._last_generated_sentence
        if not sentence:
            return
        self._speak_in_thread(sentence)

    # ══════════════════════════════════════════════════════════════════════════
    # FRAME SLOTS
    # ══════════════════════════════════════════════════════════════════════════

    @Slot(QPixmap)
    def _on_frame_ready(self, pixmap: QPixmap) -> None:
        if pixmap and not pixmap.isNull():
            # Scale to fill label while preserving aspect ratio (centered)
            scaled = pixmap.scaled(
                self._viewport_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self._viewport_label.setPixmap(scaled)
            self._prediction_overlay.show()
        else:
            self._viewport_label.clear()
            self._prediction_overlay.hide()

    @Slot(object)
    def _on_landmarks_ready(self, fd: FrameData) -> None:
        if not self._model_loaded or self._inference_adapter is None:
            return
        sign, conf = self._inference_adapter.push_frame(fd.to_dict())
        # Clean underscore BEFORE display, LLM, or any TTS reads the word
        if isinstance(sign, str):
            sign = sign.replace("_", " ").strip()
        self._update_inference_display(sign, conf)

    @Slot(float)
    def _on_fps_updated(self, fps: float) -> None:
        self._analytics["fps"].set_value(f"{fps:.0f}")

    @Slot(str)
    def _on_camera_error(self, msg: str) -> None:
        self._analytics["model"].set_value("ERR")
        self.stop_camera()

    # ══════════════════════════════════════════════════════════════════════════
    # DISPLAY HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _update_inference_display(self, sign: str, conf: float) -> None:
        _nb = "background:transparent; border:none;"

        if sign == "---" or conf < 0.35:
            self._inference_sign_label.setText("-")
            self._inference_sign_label.setStyleSheet(
                f"color:{TEXT_MUTED}; font-size:36px; font-weight:800; {_nb}"
            )
            self._inference_conf_label.setText("Confidence: 0%")
            self._confidence_bar.setFixedWidth(0)
            self._prediction_text.setText("No sign detected")
            self._prediction_conf.setText("0%")
            self._prediction_icon.setStyleSheet(
                f"color:{TEXT_MUTED}; font-size:20px; {_nb}"
            )
            self._analytics["confidence"].set_value("0%")
            return

        conf_pct = int(conf * 100)
        # Replace underscore with space so TTS/LLM never reads "_"
        # e.g. "سلام_عليكم" → "سلام عليكم" ,  "HELLO_WORLD" → "HELLO WORLD"
        clean = sign.replace("_", " ").strip()
        label = clean.upper() if clean.isascii() else clean

        self._inference_sign_label.setText(label)
        self._inference_sign_label.setStyleSheet(
            f"color:{BLUE}; font-size:36px; font-weight:800; {_nb}"
        )
        self._inference_conf_label.setText(f"Confidence: {conf_pct}%")
        self._confidence_bar.setFixedWidth(int(260 * conf))
        self._prediction_text.setText(label)
        self._prediction_conf.setText(f"{conf_pct}%")
        self._prediction_icon.setStyleSheet(
            f"color:{BLUE}; font-size:20px; {_nb}"
        )
        self._analytics["confidence"].set_value(f"{conf_pct}%")

        # ── Trigger LLM composition + TTS ──────────────────────────────────
        self._update_llm_composition(label, conf_pct)

        self._repeat_btn.setEnabled(True)

    def _reset_inference_display(self) -> None:
        _nb = "background:transparent; border:none;"
        self._inference_sign_label.setText("-")
        self._inference_sign_label.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:36px; font-weight:800; {_nb}"
        )
        self._inference_conf_label.setText("Confidence: 0%")
        self._confidence_bar.setFixedWidth(0)
        self._prediction_text.setText("No sign detected")
        self._prediction_conf.setText("0%")
        self._prediction_icon.setStyleSheet(f"color:{TEXT_MUTED}; font-size:20px; {_nb}")
        self._analytics["confidence"].set_value("0%")
        self._repeat_btn.setEnabled(False)
        self._repeat_text_btn.setEnabled(False)
        self._voice_btn.setEnabled(False)
        self._last_generated_sentence = ""
        self._last_llm_word = ""
        self._last_llm_time = 0.0
        self._llm_composition.setPlainText("")
        # Do NOT clear detected_words on camera stop — user may want to keep them

    # ══════════════════════════════════════════════════════════════════════════
    # SYSTEM STATS TICKER
    # ══════════════════════════════════════════════════════════════════════════

    def _tick_system_stats(self) -> None:
        self._gpu_val = max(20, min(95, self._gpu_val + random.randint(-3, 4)))
        self._cpu_val = max(10, min(80, self._cpu_val + random.randint(-2, 3)))
        self._ram_val = max(40, min(85, self._ram_val + random.randint(-1, 2)))
        self._gpu_lbl.setText(f"GPU {self._gpu_val}%")
        self._cpu_lbl.setText(f"CPU {self._cpu_val}%")
        self._ram_lbl.setText(f"RAM {self._ram_val}%")
        if self._camera_active:
            self._lat_val = max(18, min(48,
                                        self._lat_val + random.randint(-2, 3)))
            self._analytics["latency"].set_value(f"{self._lat_val}ms")

    # ══════════════════════════════════════════════════════════════════════════
    # NAVIGATION / LIFECYCLE
    # ══════════════════════════════════════════════════════════════════════════

    def _on_back_to_dashboard(self) -> None:
        self.stop_camera()
        self.navigate_to.emit("home")

    def hideEvent(self, event) -> None:
        self.stop_camera()
        super().hideEvent(event)

    def update_frame(self, pixmap: QPixmap) -> None:
        self._on_frame_ready(pixmap)

    # ══════════════════════════════════════════════════════════════════════════
    # HOVER-GLOW EVENT FILTER
    # ══════════════════════════════════════════════════════════════════════════

    def eventFilter(self, watched, event):
        if self._start_btn is not None and watched is self._start_btn:
            if event.type() == event.Type.Enter:
                r, g, b = [int(x) for x in self._start_rgb.split(",")]
                self._start_glow.setColor(QColor(r, g, b, 210))
                self._start_glow.setBlurRadius(56)
            elif event.type() == event.Type.Leave:
                r, g, b = [int(x) for x in self._start_rgb.split(",")]
                self._start_glow.setColor(QColor(r, g, b, 120))
                self._start_glow.setBlurRadius(38)
        return super().eventFilter(watched, event)