
# ui/quiz_screen.py
"""
SignBridge Studio — Quiz Studio Screen  (v8.5 — PipelineButton-style options)

Changes
───────
1. AnswerCard restyled to match PipelineButton from learning_screen.py:
   • Rounded pill shape (radius 21)
   • Gradient backgrounds per letter (A/B/C each unique)
   • Outer glow halo + hover overlay
   • Dark text on bright gradients; white text on violet
2. Removed unused _CCOLORS mapping.
"""

import os, random, math, time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy, QSpacerItem,
)
from PySide6.QtCore import (
    Qt, QTimer, QPoint, QSize, QRect, QRectF,
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush,
    QLinearGradient, QRadialGradient, QConicalGradient,
    QFont, QPainterPath, QMovie, QImageReader,
)

# ── TOKENS ──────────────────────────────────────────────────────────────────────
BG      = "#050B1A"
CYAN    = "#00E5FF"
CYAN2   = "#00B8FF"
TEAL    = "#00C9B8"
VIOLET  = "#7C3AED"
VIOLET2 = "#B300FF"
MAGENTA = "#E040FB"
PRI     = "#FFFFFF"
SEC     = "#A0AEC0"
MUTED   = "#3A5A7A"
SUCCESS = "#00E5A0"
DANGER  = "#FF4D6D"

# ── ASSET HELPERS ────────────────────────────────────────────────────────────────
SIGNS_BASE = os.path.join("assets", "signs")
def gif_path(cat, fn): return os.path.join(SIGNS_BASE, cat, fn)

QUESTIONS = [
    {"gif": gif_path("courtesy",  "thank_you.gif"),    "options": ["Thank You","Sorry","Hello"],           "correct": "Thank You", "category": "Courtesy"},
    {"gif": gif_path("courtesy",  "Sorry.gif"),         "options": ["Understand","Sorry","Thank You"],      "correct": "Sorry",     "category": "Courtesy"},
    {"gif": gif_path("courtesy",  "Understand.gif"),    "options": ["Sorry","Hello","Understand"],          "correct": "Understand","category": "Courtesy"},
    {"gif": gif_path("greetings", "hello.gif"),         "options": ["How Are You","Hello","Nice to Meet"],  "correct": "Hello",     "category": "Greetings"},
    {"gif": gif_path("greetings", "How_are_you.gif"),   "options": ["Hello","Nice to Meet","How Are You"],  "correct": "How Are You","category":"Greetings"},
    {"gif": gif_path("greetings", "Nice_to_meet.gif"),  "options": ["Nice to Meet","Hello","How Are You"],  "correct": "Nice to Meet","category":"Greetings"},
]
TOTAL = len(QUESTIONS)

FB_OK  = ["Excellent recognition speed","Strong semantic association detected",
           "Neural pathway reinforced","Your gesture understanding is improving"]
FB_ERR = ["Focus on the hand motion and direction.","Study the emotional intent of the gesture.",
           "Review the gesture's semantic context.","Try to understand the gesture meaning."]

# ══════════════════════════════════════════════════════════════════════════════════
#  ANIMATED BACKGROUND
# ══════════════════════════════════════════════════════════════════════════════════
class ParticleBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self._t = 0.0
        self._pts = [
            {"x": random.random(), "y": random.random(),
             "vx": random.uniform(-0.00012, 0.00012),
             "vy": random.uniform(-0.00012, 0.00012),
             "r":  random.uniform(1.0, 2.0),
             "op": random.uniform(0.05, 0.22),
             "hue": random.choice([185, 260, 200])}
            for _ in range(55)
        ]
        timer = QTimer(self); timer.timeout.connect(self._tick); timer.start(33)

    def _tick(self):
        self._t += 0.016
        for p in self._pts:
            p["x"] = (p["x"] + p["vx"]) % 1.0
            p["y"] = (p["y"] + p["vy"]) % 1.0
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        bg = QLinearGradient(0, 0, W, H)
        bg.setColorAt(0, QColor("#030810")); bg.setColorAt(0.5, QColor("#050B1A")); bg.setColorAt(1, QColor("#060212"))
        p.fillRect(0, 0, W, H, bg)
        rg = QRadialGradient(W*.12, H*.10, W*.38)
        rg.setColorAt(0, QColor(0, 120, 220, 24)); rg.setColorAt(1, QColor(0,0,0,0))
        p.fillRect(0, 0, W, H, rg)
        rg2 = QRadialGradient(W*.88, H*.90, W*.32)
        rg2.setColorAt(0, QColor(124,58,237,18)); rg2.setColorAt(1, QColor(0,0,0,0))
        p.fillRect(0, 0, W, H, rg2)
        pen = QPen(QColor(0,229,255,5)); pen.setWidthF(0.5); p.setPen(pen)
        for x in range(0, W+52, 52): p.drawLine(x,0,x,H)
        for y in range(0, H+52, 52): p.drawLine(0,y,W,y)
        p.setPen(Qt.NoPen)
        for pt in self._pts:
            c = QColor.fromHsv(int(pt["hue"]), 200, 240, int(pt["op"]*255))
            p.setBrush(c); r = pt["r"]
            p.drawEllipse(QRectF(pt["x"]*W-r, pt["y"]*H-r, r*2, r*2))
        vg = QRadialGradient(W/2, H/2, max(W,H)*.65)
        vg.setColorAt(0.45, QColor(0,0,0,0)); vg.setColorAt(1, QColor(0,0,0,160))
        p.fillRect(0, 0, W, H, vg); p.end()

# ══════════════════════════════════════════════════════════════════════════════════
#  GLOW CARD
# ══════════════════════════════════════════════════════════════════════════════════
class GlowCard(QFrame):
    def __init__(self, glow=CYAN, parent=None):
        super().__init__(parent)
        self._gc = QColor(glow)
        self.setStyleSheet("GlowCard{background:rgba(7,18,37,0.90);border:1px solid rgba(0,229,255,0.09);border-radius:18px;}")

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        W = self.width()
        tg = QLinearGradient(0,0,W,0)
        tg.setColorAt(0, QColor(0,0,0,0))
        gc = QColor(self._gc); gc.setAlpha(75)
        tg.setColorAt(0.5, gc); tg.setColorAt(1, QColor(0,0,0,0))
        p.setPen(QPen(QBrush(tg), 1.0)); p.drawLine(20,1,W-20,1); p.end()

# ══════════════════════════════════════════════════════════════════════════════════
#  CIRCULAR PROGRESS RING
# ══════════════════════════════════════════════════════════════════════════════════
class RingWidget(QWidget):
    def __init__(self, size=76, font_size=15, sub="COMPLETE", parent=None):
        super().__init__(parent)
        self._pct = 0; self._t = 0.0; self._sub = sub; self._fs = font_size
        self.setFixedSize(size, size)
        t = QTimer(self); t.timeout.connect(self._tick); t.start(40)

    def set_pct(self, v): self._pct = max(0, min(100, v)); self.update()
    def _tick(self): self._t += 0.05; self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height(); cx, cy = W//2, H//2; r = W//2 - 6
        p.setPen(QPen(QColor(0,229,255,18), 5, Qt.SolidLine, Qt.RoundCap)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPoint(cx,cy), r, r)
        if self._pct > 0:
            g = QConicalGradient(cx,cy,90)
            g.setColorAt(0, QColor(CYAN)); g.setColorAt(0.5, QColor(CYAN2)); g.setColorAt(1, QColor(TEAL))
            p.setPen(QPen(QBrush(g), 5, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(cx-r, cy-r, r*2, r*2, 90*16, -int(self._pct/100*360*16))
        p.setPen(QColor(PRI)); p.setFont(QFont("Arial", self._fs, QFont.Bold))
        p.drawText(QRect(0, cy-12, W, 24), Qt.AlignCenter, f"{self._pct}%")
        p.setPen(QColor(MUTED)); f2=QFont("Arial",5); f2.setLetterSpacing(QFont.AbsoluteSpacing,2); p.setFont(f2)
        p.drawText(QRect(0, cy+12, W, 12), Qt.AlignCenter, self._sub); p.end()

# ══════════════════════════════════════════════════════════════════════════════════
#  STREAK RING
# ══════════════════════════════════════════════════════════════════════════════════
class StreakRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._streak=0; self._t=0.0
        self.setFixedSize(72, 72)
        t=QTimer(self); t.timeout.connect(self._tick); t.start(40)

    def set_streak(self, v): self._streak=v; self.update()
    def _tick(self): self._t+=0.05; self.update()

    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        W,H=self.width(),self.height(); cx,cy=W//2,H//2; r=27
        p.setPen(QPen(QColor(0,229,255,18),4,Qt.SolidLine,Qt.RoundCap)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPoint(cx,cy),r,r)
        if self._streak>0:
            g=QConicalGradient(cx,cy,90); g.setColorAt(0,QColor(CYAN)); g.setColorAt(1,QColor(TEAL))
            p.setPen(QPen(QBrush(g),4,Qt.SolidLine,Qt.RoundCap))
            p.drawArc(cx-r,cy-r,r*2,r*2,90*16,-int(min(self._streak/10,1)*360*16))
        p.setPen(QColor(PRI)); p.setFont(QFont("Arial",16,QFont.Bold))
        p.drawText(QRect(0,cy-11,W,22),Qt.AlignCenter,str(self._streak))
        p.setPen(QColor(MUTED)); f2=QFont("Arial",5); f2.setLetterSpacing(QFont.AbsoluteSpacing,2); p.setFont(f2)
        p.drawText(QRect(0,cy+12,W,11),Qt.AlignCenter,"STREAK"); p.end()

# ══════════════════════════════════════════════════════════════════════════════════
#  ROUND TRACKER
# ══════════════════════════════════════════════════════════════════════════════════
class RoundTracker(QWidget):
    DOT = 30
    GAP = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cur = 0
        tw = 6*self.DOT + 5*self.GAP
        self.setFixedSize(tw, self.DOT + 4)

    def set_step(self, i): self._cur = i; self.update()

    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        H=self.height(); cy=H//2; sw=self.DOT+self.GAP
        for i in range(6):
            cx=i*sw+self.DOT//2
            if i<5:
                nx=(i+1)*sw+self.DOT//2
                if i<self._cur:
                    g=QLinearGradient(cx,cy,nx,cy); g.setColorAt(0,QColor(CYAN)); g.setColorAt(1,QColor(CYAN2))
                    p.setPen(QPen(QBrush(g),2))
                else:
                    p.setPen(QPen(QColor(0,229,255,20),2))
                p.drawLine(cx+self.DOT//2,cy,nx-self.DOT//2,cy)
            r=self.DOT//2-2
            if i<self._cur:
                g2=QRadialGradient(cx,cy,r); g2.setColorAt(0,QColor(CYAN)); g2.setColorAt(1,QColor(CYAN2))
                p.setBrush(g2); p.setPen(QPen(QColor(CYAN),1.2))
                p.drawEllipse(QPoint(cx,cy),r,r)
                p.setPen(QColor("#000")); p.setFont(QFont("Arial",8,QFont.Bold))
                p.drawText(QRect(cx-r,cy-r,r*2,r*2),Qt.AlignCenter,"✓")
            elif i==self._cur:
                gw=QRadialGradient(cx,cy,r+4); gw.setColorAt(0,QColor(0,229,255,45)); gw.setColorAt(1,QColor(0,0,0,0))
                p.setBrush(gw); p.setPen(Qt.NoPen); p.drawEllipse(QPoint(cx,cy),r+4,r+4)
                g3=QRadialGradient(cx,cy,r); g3.setColorAt(0,QColor(0,229,255,170)); g3.setColorAt(1,QColor(0,180,255,80))
                p.setBrush(g3); p.setPen(QPen(QColor(CYAN),2))
                p.drawEllipse(QPoint(cx,cy),r,r)
                p.setPen(QColor(PRI)); p.setFont(QFont("Arial",9,QFont.Bold))
                p.drawText(QRect(cx-r,cy-r,r*2,r*2),Qt.AlignCenter,str(i+1))
            else:
                p.setBrush(QColor(0,229,255,10)); p.setPen(QPen(QColor(0,229,255,30),1.2))
                p.drawEllipse(QPoint(cx,cy),r,r)
                p.setPen(QColor(MUTED)); p.setFont(QFont("Arial",8))
                p.drawText(QRect(cx-r,cy-r,r*2,r*2),Qt.AlignCenter,str(i+1))
        p.end()

# ══════════════════════════════════════════════════════════════════════════════════
#  MINI ACCURACY BAR
# ══════════════════════════════════════════════════════════════════════════════════
class MiniBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self._pct=0; self.setFixedHeight(3)
    def set_pct(self,v): self._pct=max(0,min(100,v)); self.update()
    def paintEvent(self,_):
        p=QPainter(self); W=self.width()
        p.setBrush(QColor(0,229,255,16)); p.setPen(Qt.NoPen); p.drawRoundedRect(0,0,W,3,1.5,1.5)
        if self._pct>0:
            g=QLinearGradient(0,0,W,0); g.setColorAt(0,QColor(CYAN)); g.setColorAt(1,QColor(TEAL))
            p.setBrush(g); p.drawRoundedRect(0,0,int(W*self._pct/100),3,1.5,1.5)
        p.end()

# ══════════════════════════════════════════════════════════════════════════════════
#  STAT ROW
# ══════════════════════════════════════════════════════════════════════════════════
class StatRow(QWidget):
    def __init__(self, icon, label, value="—", bar=False, parent=None):
        super().__init__(parent); self._bar=bar
        lay=QVBoxLayout(self)
        lay.setContentsMargins(0,3,0,3); lay.setSpacing(2)
        row=QHBoxLayout(); row.setSpacing(6)
        ico=QLabel(icon); ico.setStyleSheet(f"color:{CYAN};font-size:10px;"); ico.setFixedWidth(16)
        self._l=QLabel(label)
        self._l.setStyleSheet(f"color:{SEC};font-size:11px;")
        self._l.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._l.setWordWrap(False)
        self._v=QLabel(value)
        self._v.setStyleSheet(f"color:{PRI};font-size:11px;font-weight:700;")
        self._v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(ico); row.addWidget(self._l); row.addStretch(); row.addWidget(self._v)
        lay.addLayout(row)
        if bar:
            self._mb=MiniBar(self); lay.addWidget(self._mb)
        sep=QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color:#0D1E3A;")
        lay.addWidget(sep)

    def set_value(self,v): self._v.setText(str(v))
    def set_bar(self,v):
        if self._bar and hasattr(self,"_mb"): self._mb.set_pct(v)

# ══════════════════════════════════════════════════════════════════════════════════
#  ANSWER CARD  (PipelineButton style — per-letter colour)
# ══════════════════════════════════════════════════════════════════════════════════
class AnswerCard(QPushButton):
    """PipelineButton-styled option card. Each letter gets its own idle gradient."""

    # Idle gradient per letter  (c1, c2)
    IDLE_GRAD = {
        "A": ("#00E5FF", "#00B8FF"),   # Cyan
        "B": ("#00C9B8", "#00E5A0"),   # Teal
        "C": ("#7C3AED", "#9333EA"),   # Violet
    }
    # State override gradients
    ST_GRAD = {
        "correct": ("#00E5A0", "#00FFB2"),
        "wrong":   ("#FF4D6D", "#FF8FA3"),
        "reveal":  ("#00C9B8", "#00E5FF"),
    }
    # Text colour for idle states (dark on bright, white on violet)
    TXT_COL = {
        "A": "#030712",
        "B": "#030712",
        "C": "#FFFFFF",
    }

    def __init__(self, letter, text, parent=None):
        super().__init__(parent)
        self._letter = letter
        self._answer_text = text
        self._state = "idle"
        self._hover = False
        self._t = 0.0
        self.setFixedHeight(54)
        self.setMinimumWidth(120)
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet("background:transparent;border:none;")
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(33)

    def _tick(self):
        self._t += 0.05
        if self._state in ("correct", "wrong", "reveal"):
            self.update()

    def set_state(self, s):
        self._state = s
        self.update()

    def reset(self):
        self._state = "idle"
        self._hover = False
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        # ── Resolve colours ──
        if self._state in self.ST_GRAD:
            c1, c2 = self.ST_GRAD[self._state]
            txt = "#030712"
            status_c = SUCCESS if self._state == "correct" else (DANGER if self._state == "wrong" else TEAL)
            status_txt = "✓" if self._state in ("correct", "reveal") else "✗"
        else:
            c1, c2 = self.IDLE_GRAD[self._letter]
            txt = self.TXT_COL[self._letter]
            status_c = c1
            status_txt = ""

        # ── Glow halo (full widget rect) ──
        glow_a = 45 if self._hover else 28
        if self._state in ("correct", "wrong", "reveal"):
            glow_a = 55 + int(abs(math.sin(self._t * 3)) * 35)
        glow_path = QPainterPath()
        glow_path.addRoundedRect(QRectF(0, 0, W, H), 23, 23)
        glow_col = QColor(c1)
        glow_col.setAlpha(glow_a)
        p.fillPath(glow_path, QBrush(glow_col))

        # ── Pill background (inset 2 px) ──
        path = QPainterPath()
        path.addRoundedRect(QRectF(2, 2, W - 4, H - 4), 21, 21)
        grad = QLinearGradient(0, 0, W, 0)
        grad.setColorAt(0, QColor(c1))
        grad.setColorAt(1, QColor(c2))
        p.fillPath(path, QBrush(grad))

        # ── Hover overlay ──
        if self._hover and self._state == "idle":
            ov = QColor(255, 255, 255, 30)
            p.fillPath(path, QBrush(ov))

        # ── Pulse border for active states ──
        if self._state in ("correct", "wrong", "reveal"):
            pulse = 2 + int(abs(math.sin(self._t * 3)) * 2.5)
            pulse_c = QColor(c1)
            pulse_c.setAlpha(100)
            p.setPen(QPen(pulse_c, pulse))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)

        # ── Inner border ──
        border_c = QColor(c1)
        border_c.setAlpha(140)
        p.setPen(QPen(border_c, 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

        # ── Letter badge ──
        bs = 26
        bx = 16
        by = (H - bs) // 2
        badge_bg = QColor(txt)
        badge_bg.setAlpha(22)
        p.setBrush(QBrush(badge_bg))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRect(bx, by, bs, bs), 6, 6)
        p.setPen(QColor(txt))
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(QRect(bx, by, bs, bs), Qt.AlignCenter, self._letter)

        # ── Answer text ──
        status_w = 28 if self._state in ("correct", "wrong", "reveal") else 0
        tx = bx + bs + 12
        text_w = W - tx - status_w - 16
        p.setPen(QColor(txt))
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.drawText(QRect(tx, 0, text_w, H), Qt.AlignVCenter | Qt.AlignLeft, self._answer_text)

        # ── Status icon ──
        if self._state in ("correct", "wrong", "reveal"):
            p.setPen(QColor(status_c))
            p.setFont(QFont("Arial", 16, QFont.Bold))
            p.drawText(QRect(W - status_w - 12, 0, status_w, H), Qt.AlignVCenter | Qt.AlignRight, status_txt)

        p.end()

# ══════════════════════════════════════════════════════════════════════════════════
#  GIF AVATAR WIDGET
# ══════════════════════════════════════════════════════════════════════════════════
class AvatarGifWidget(QLabel):
    PAD = 24
    MIN_H = 380

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(self.MIN_H)
        self.setAlignment(Qt.AlignCenter)
        self._movie     = None
        self._src_w     = 0
        self._src_h     = 0
        self._scaled_ok = False
        self._placeholder()

    def _placeholder(self):
        self.setText("▶  GIF")
        self.setStyleSheet(
            f"color:{MUTED};font-size:16px;"
            f"background:rgba(0,229,255,0.04);"
            f"border:2px dashed rgba(0,229,255,0.16);"
            f"border-radius:18px;")

    def _available(self):
        return max(self.width()  - 2*self.PAD, 1), \
               max(self.height() - 2*self.PAD, 1)

    def _aspect_fit(self, avail_w, avail_h):
        if self._src_w <= 0 or self._src_h <= 0:
            return avail_w, avail_h
        ratio = self._src_w / self._src_h
        w = avail_w
        h = int(w / ratio)
        if h > avail_h:
            h = avail_h
            w = int(h * ratio)
        return max(w, 1), max(h, 1)

    def _apply_scale(self):
        if self._movie is None or self._src_w <= 0:
            return
        aw, ah = self._available()
        sw, sh = self._aspect_fit(aw, ah)
        self._movie.setScaledSize(QSize(sw, sh))
        self._scaled_ok = True

    def load_gif(self, path: str):
        if self._movie:
            self._movie.stop()
            self._movie = None
        self._src_w = self._src_h = 0
        self._scaled_ok = False

        if not os.path.isfile(path):
            self._placeholder()
            self.setText(f"Missing:\n{os.path.basename(path)}")
            return

        reader = QImageReader(path)
        native = reader.size()
        if native.isValid() and native.width() > 0 and native.height() > 0:
            self._src_w = native.width()
            self._src_h = native.height()

        self.setText("")
        self.setStyleSheet("background:transparent;border:none;")
        movie = QMovie(path)
        self._movie = movie

        if self._src_w > 0:
            self._apply_scale()

        def _on_first_frame(frame_number: int):
            if frame_number == 0 and not self._scaled_ok:
                px = movie.currentPixmap()
                if not px.isNull():
                    orig = movie.currentImage().size()
                    if orig.isValid() and orig.width() > 0:
                        self._src_w = orig.width()
                        self._src_h = orig.height()
                self._apply_scale()

        movie.frameChanged.connect(_on_first_frame)
        self.setMovie(movie)
        movie.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_scale()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        bp = QPainterPath(); bp.addRoundedRect(QRectF(0,0,W,H), 20, 20)
        bg = QLinearGradient(0,0,0,H)
        bg.setColorAt(0, QColor("#0A1830")); bg.setColorAt(1, QColor("#060E22"))
        p.fillPath(bp, bg)
        rg = QRadialGradient(W/2, H/2, W*.42)
        rg.setColorAt(0, QColor(0,229,255,18)); rg.setColorAt(1, QColor(0,0,0,0))
        p.fillPath(bp, rg)
        p.setPen(QPen(QColor(0,229,255,55), 1.5)); p.setBrush(Qt.NoBrush); p.drawPath(bp)
        ca = QColor(CYAN); ca.setAlpha(110); al = 16; aw = 2.5
        p.setPen(QPen(ca, aw, Qt.SolidLine, Qt.RoundCap))
        for ax,ay,dx,dy in [(20,20,1,1),(W-20,20,-1,1),(20,H-20,1,-1),(W-20,H-20,-1,-1)]:
            p.drawLine(ax,ay,ax+dx*al,ay); p.drawLine(ax,ay,ax,ay+dy*al)
        p.end()
        super().paintEvent(event)

# ══════════════════════════════════════════════════════════════════════════════════
#  MAIN QUIZ SCREEN
# ══════════════════════════════════════════════════════════════════════════════════
class QuizScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background:{BG};")
        self._qi=0; self._score=0; self._ans=0; self._streak=0
        self._locked=False; self._t0=time.time()

        self._bg=ParticleBackground(self); self._bg.lower()
        self._clock=QTimer(self); self._clock.timeout.connect(self._tick_time); self._clock.start(1000)
        self._build(); self._load()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._bg.setGeometry(0,0,self.width(),self.height())
        if hasattr(self, '_qc') and hasattr(self, '_cards'):
            panel_w = self._qc.width()
            if panel_w > 0:
                card_w = max(180, min(300, int(panel_w * 0.30)))
                for c in self._cards:
                    c.setFixedWidth(card_w)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 14, 28, 14)
        root.setSpacing(8)

        tt = QLabel("Quiz Studio")
        tt.setStyleSheet(f"font-size:22px;font-weight:800;color:{PRI};background:transparent;")
        root.addWidget(tt)

        # ── ROUND TRACKER ─────────────────────────────────────────────────────
        tbar = GlowCard(CYAN2,self); tbar.setFixedHeight(44)
        tl = QHBoxLayout(tbar); tl.setContentsMargins(24,0,24,0); tl.setSpacing(16)
        self._rl = QLabel(f"ROUND 1 OF {TOTAL}")
        self._rl.setStyleSheet(f"color:{CYAN};font-size:8px;font-weight:700;letter-spacing:2px;")
        self._rt = RoundTracker(self)
        self._pl = QLabel("0% Complete")
        self._pl.setStyleSheet(f"color:{MUTED};font-size:8px;")
        tl.addWidget(self._rl, alignment=Qt.AlignVCenter)
        tl.addStretch(); tl.addWidget(self._rt, alignment=Qt.AlignVCenter); tl.addStretch()
        tl.addWidget(self._pl, alignment=Qt.AlignVCenter)
        root.addWidget(tbar)

        # ── MAIN ROW ────────────────────────────────────────────────────────────
        mr = QHBoxLayout(); mr.setSpacing(12)

        # ── Left: Quiz card ───────────────────────────────────────────────────
        qc = GlowCard(CYAN,self)
        self._qc = qc
        ql = QVBoxLayout(qc)
        ql.setContentsMargins(20,12,20,14)
        ql.setSpacing(0)

        # — Top info row: badge only (score removed) —
        tr = QHBoxLayout()
        self._badge = QLabel("● SIGN RECOGNITION")
        self._badge.setStyleSheet(
            f"color:{CYAN};background:transparent;"
            f"border:1px solid rgba(0,229,255,0.35);border-radius:10px;"
            f"font-size:10px;font-weight:700;letter-spacing:2px;padding:4px 24px;min-width:160px;")
        self._badge.setAlignment(Qt.AlignCenter)
        tr.addWidget(self._badge)
        tr.addStretch()
        ql.addLayout(tr)
        ql.addSpacing(10)

        # — Question text —
        self._qq = QLabel("What does this sign mean?")
        self._qq.setStyleSheet(f"color:{PRI};font-size:12px;background:transparent;")
        ql.addWidget(self._qq)
        ql.addSpacing(8)

        # — Avatar —
        self._av = AvatarGifWidget(self)
        ql.addWidget(self._av, stretch=1)

        # — Gap —
        ql.addSpacing(40)

        # — Answer section header —
        ans_hdr = QHBoxLayout()
        ans_lbl = QLabel("SELECT YOUR ANSWER")
        ans_lbl.setStyleSheet(f"color:{MUTED};font-size:7px;letter-spacing:2px;")
        ans_hdr.addWidget(ans_lbl)
        ans_hdr.addStretch()
        ql.addLayout(ans_hdr)
        ql.addSpacing(8)

        # — Answer cards —
        CARD_W = 220
        self._cards = []
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        cards_row.addStretch()
        for lt, opt in zip(["A","B","C"], QUESTIONS[0]["options"]):
            c = AnswerCard(lt, opt, self)
            c.setFixedWidth(CARD_W)
            c.clicked.connect(lambda ch=False, card=c, a=opt: self._on_ans(card,a))
            cards_row.addWidget(c)
            self._cards.append(c)
        cards_row.addStretch()
        ql.addLayout(cards_row)
        ql.addSpacing(10)

        # — Feedback panel (transparent, no black tile) —
        self._fb = GlowCard(TEAL,self); self._fb.setFixedHeight(50)
        self._fb.setStyleSheet("background:transparent; border:none;")
        fbl = QHBoxLayout(self._fb); fbl.setContentsMargins(14,0,14,0); fbl.setSpacing(10)
        self._fb_ico = QLabel(); self._fb_ico.setStyleSheet("font-size:16px;")
        self._fb_st  = QLabel()
        self._fb_msg = QLabel(); self._fb_msg.setStyleSheet(f"font-size:9px;color:{SEC};")
        fbc = QVBoxLayout(); fbc.setSpacing(1)
        fbc.addWidget(self._fb_st); fbc.addWidget(self._fb_msg)
        self._nb = QPushButton("Next →"); self._nb.setCursor(Qt.PointingHandCursor)
        self._nb.setFixedSize(84,28)
        self._nb.setStyleSheet(
            f"QPushButton{{background:rgba(0,229,255,0.10);border:1px solid {CYAN};"
            f"border-radius:7px;color:{CYAN};font-size:9px;font-weight:700;}}"
            f"QPushButton:hover{{background:rgba(0,229,255,0.22);}}")
        self._nb.clicked.connect(self._next)
        fbl.addWidget(self._fb_ico); fbl.addLayout(fbc,1); fbl.addWidget(self._nb)
        self._fb.hide()
        ql.addSpacing(6)
        ql.addWidget(self._fb)

        mr.addWidget(qc, 76)

        # ── Right: Stats column ─────────────────────────────────────────────
        sp = QVBoxLayout(); sp.setSpacing(8)

        # ── CURRENT STREAK ────────────────────────────────────────────────────
        cs_hdr = QLabel("CURRENT STREAK")
        cs_hdr.setStyleSheet(f"color:{PRI};font-size:9px;letter-spacing:2px;")
        sp.addWidget(cs_hdr)

        # CURRENT STREAK — same style as Session Stats
        stc = GlowCard(VIOLET,self)
        stl = QVBoxLayout(stc); stl.setContentsMargins(14,8,14,6); stl.setSpacing(0)
        self._sr = StatRow("⚡","Current Streak","0")
        self._sr.setStyleSheet("background:transparent;")
        self._sr._v.setStyleSheet(f"color:{PRI};font-size:18px;font-weight:800;")
        self._sr._l.setStyleSheet(f"color:{SEC};font-size:12px;")
        stl.addWidget(self._sr)
        sp.addWidget(stc)

        # ── SESSION STATS ─────────────────────────────────────────────────────
        ss_hdr = QLabel("SESSION STATS")
        ss_hdr.setStyleSheet(f"color:{PRI};font-size:9px;letter-spacing:2px;")
        sp.addWidget(ss_hdr)

        ssc = GlowCard(VIOLET,self)
        ssl = QVBoxLayout(ssc); ssl.setContentsMargins(14,8,14,6); ssl.setSpacing(0)
        self._sa  = StatRow("◎","Accuracy","—",bar=True); self._sa.setStyleSheet("background:transparent;")
        self._sq  = StatRow("◈","Questions","0");          self._sq.setStyleSheet("background:transparent;")
        self._sc2 = StatRow("✦","Correct","0");            self._sc2.setStyleSheet("background:transparent;")
        self._st  = StatRow("◷","Time","00:00");           self._st.setStyleSheet("background:transparent;")
        for w in [self._sa,self._sq,self._sc2,self._st]: ssl.addWidget(w)
        sp.addWidget(ssc, 1)

        # RESET SESSION — styled like pipeline Pause button
        rc = GlowCard(VIOLET, self); rc.setMinimumHeight(72)
        rl2 = QVBoxLayout(rc); rl2.setContentsMargins(12, 8, 12, 8)
        rb = QPushButton("↺   Reset Session"); rb.setCursor(Qt.PointingHandCursor)
        rb.setFixedHeight(42)
        rb.setStyleSheet(
            "QPushButton {"
            "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 #6D28D9, stop:1 {VIOLET});"
            "  color: white; border: none; border-radius: 21px;"
            "  font-size: 13px; font-weight:700; padding: 0 20px;"
            "}"
            "QPushButton:hover {"
            "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {VIOLET}, stop:1 #C084FC);"
            "}")
        rb.clicked.connect(self._reset)
        rl2.addStretch(); rl2.addWidget(rb); rl2.addStretch()
        sp.addWidget(rc)

        mr.addLayout(sp, 24)
        root.addLayout(mr, 1)

    def _slim_label(self, text):
        l = QLabel(text)
        l.setStyleSheet(f"color:{MUTED};font-size:7px;letter-spacing:2px;")
        return l

    def _load(self):
        if self._qi >= TOTAL: return
        q = QUESTIONS[self._qi]
        self._badge.setText(f"● {q['category'].upper()}")
        self._av.load_gif(q["gif"])
        opts = q["options"][:]; random.shuffle(opts)
        for card,opt,lt in zip(self._cards,opts,["A","B","C"]):
            card._answer_text=opt; card._letter=lt; card.reset(); card.setEnabled(True)
            try: card.clicked.disconnect()
            except RuntimeError: pass
            card.clicked.connect(lambda ch=False,c=card,a=opt: self._on_ans(c,a))
        pct = int(self._qi/TOTAL*100)
        self._rl.setText(f"ROUND {self._qi+1} OF {TOTAL}")
        self._pl.setText(f"{pct}% Complete")
        self._rt.set_step(self._qi)
        self._fb.hide()

    def _on_ans(self, card, ans):
        if self._locked: return
        self._locked=True; self._ans+=1
        q = QUESTIONS[self._qi]; ok = ans==q["correct"]
        if ok:
            card.set_state("correct"); self._score+=1; self._streak+=1
            self._show_fb(True, random.choice(FB_OK))
        else:
            card.set_state("wrong"); self._streak=0
            for c in self._cards:
                if c._answer_text==q["correct"]: c.set_state("reveal")
            self._show_fb(False, random.choice(FB_ERR))
        for c in self._cards: c.setEnabled(False)
        self._upd_stats()

    def _show_fb(self, ok, msg):
        if ok:
            self._fb_ico.setText("✦"); self._fb_st.setText("Correct Answer")
            self._fb_st.setStyleSheet(f"font-size:12px;font-weight:700;color:{SUCCESS};")
        else:
            self._fb_ico.setText("⊘"); self._fb_st.setText("Incorrect")
            self._fb_st.setStyleSheet(f"font-size:12px;font-weight:700;color:{DANGER};")
        self._fb_msg.setText(msg); self._fb.show()

    def _next(self):
        self._qi=(self._qi+1)%TOTAL; self._locked=False; self._load()

    def _upd_stats(self):
        acc = int(self._score/self._ans*100) if self._ans else 0
        self._sa.set_value(f"{acc}%" if self._ans else "—"); self._sa.set_bar(acc)
        self._sq.set_value(self._ans); self._sc2.set_value(self._score)
        self._sr.set_value(str(self._streak))

    def _tick_time(self):
        e=int(time.time()-self._t0); m,s=divmod(e,60)
        self._st.set_value(f"{m:02d}:{s:02d}")

    def _reset(self):
        self._qi=0; self._score=0; self._ans=0; self._streak=0
        self._locked=False; self._t0=time.time()
        self._sr.set_value("0")
        self._sa.set_value("—"); self._sa.set_bar(0)
        self._sq.set_value(0); self._sc2.set_value(0); self._st.set_value("00:00")
        self._load()