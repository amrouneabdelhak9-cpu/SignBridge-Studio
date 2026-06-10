"""
SignBridge Studio — Splash Screen v4
=====================================
Compact, centered, professional. All icons are SVG-drawn on canvas (no emoji).
"""

import math, random, sys

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QRectF,
    Qt, QTimer, Signal, QPointF, QSizeF,
)
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetrics,
    QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication, QGraphicsOpacityEffect,
    QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget, QFrame,
)

# ── palette ───────────────────────────────────────────────────────────────────
C_BG    = QColor(5,   8,  22)
C_CYAN  = QColor(0,  229, 255)
C_PURP  = QColor(100, 80, 240)
C_VIOL  = QColor(160,  75, 245)
C_BLUE  = QColor( 30, 140, 255)
C_WHITE = QColor(245, 247, 255)
C_SEC   = QColor(160, 170, 195)
C_MUTED = QColor(100, 112, 138)

S_WHITE = "#F5F7FF"
S_SEC   = "#A0AAC3"
S_MUTED = "#64708A"
S_CYAN  = "#00E5FF"
S_PURP  = "#6450F0"
S_VIOL  = "#A04BF5"


# ── helpers ───────────────────────────────────────────────────────────────────
def _pen(color: QColor, w: float = 1.0, style=Qt.SolidLine) -> QPen:
    p = QPen(color, w, style); p.setCapStyle(Qt.RoundCap); p.setJoinStyle(Qt.RoundJoin)
    return p

def _col(r,g,b,a=255): return QColor(r,g,b,a)


# ── tiny particle ─────────────────────────────────────────────────────────────
class _Dot:
    __slots__ = ("x","y","r","vx","vy","a","k","w","h")
    def __init__(self, w, h, initial=True):
        self.w=w; self.h=h
        self.x=random.uniform(0,w)
        self.y=random.uniform(0,h) if initial else -3.0
        self.r=random.uniform(0.7,2.0)
        self.vy=random.uniform(0.12,0.45)
        self.vx=random.uniform(-0.1,0.1)
        self.a=random.uniform(30,130)
        self.k=random.choice(("c","p","w"))
    def step(self):
        self.y+=self.vy; self.x+=self.vx
        if self.y>self.h+3: self.__init__(self.w,self.h,False)
    def paint(self,qp):
        c=(QColor(0,229,255,int(self.a)) if self.k=="c" else
           QColor(100,80,240,int(self.a)) if self.k=="p" else
           QColor(245,247,255,int(self.a)))
        qp.setBrush(QBrush(c)); qp.setPen(Qt.NoPen)
        qp.drawEllipse(QRectF(self.x-self.r,self.y-self.r,self.r*2,self.r*2))


# ── animated background ───────────────────────────────────────────────────────
class BgCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._t=0.0; self._dots=[]
        QTimer(self).setInterval(36) or None
        t=QTimer(self); t.timeout.connect(self._tick); t.start(36)

    def resizeEvent(self,e):
        w,h=self.width(),self.height()
        self._dots=[_Dot(w,h) for _ in range(80)]
        super().resizeEvent(e)

    def _tick(self):
        self._t+=0.016
        for d in self._dots: d.step()
        self.update()

    def paintEvent(self,e):
        qp=QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        g=QLinearGradient(0,0,0,h)
        g.setColorAt(0,QColor(4,7,20)); g.setColorAt(1,QColor(8,14,28))
        qp.fillRect(self.rect(),QBrush(g))

        # hero glow
        pulse=1+0.04*math.sin(self._t*1.1)
        rg=QRadialGradient(w*.5,h*.38,h*.5*pulse)
        rg.setColorAt(0,QColor(0,60,150,45)); rg.setColorAt(.7,QColor(0,20,60,15))
        rg.setColorAt(1,QColor(0,0,0,0))
        qp.setBrush(QBrush(rg)); qp.setPen(Qt.NoPen); qp.drawRect(self.rect())

        # grid
        qp.setPen(_pen(QColor(0,229,255,6),0.4))
        for x in range(0,w,52): qp.drawLine(x,0,x,h)
        for y in range(0,h,52): qp.drawLine(0,y,w,y)

        for d in self._dots: d.paint(qp)

        # vignette
        vg=QRadialGradient(w/2,h/2,max(w,h)*.6)
        vg.setColorAt(0,QColor(0,0,0,0)); vg.setColorAt(1,QColor(0,0,0,160))
        qp.setBrush(QBrush(vg)); qp.setPen(Qt.NoPen); qp.drawRect(self.rect())

        # border
        qp.setPen(_pen(QColor(0,180,255,38),1.0)); qp.setBrush(Qt.NoBrush)
        qp.drawRoundedRect(QRectF(4,4,w-8,h-8),12,12)
        qp.end()


# ── constellation widget (left) ───────────────────────────────────────────────
class ConstellationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(240,240)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._t=0.0
        random.seed(42)
        cx,cy,R=120,120,95
        self._base=[]
        for i in range(14):
            a=2*math.pi*i/14
            r=R*random.uniform(0.72,1.0)
            self._base.append((cx+r*math.cos(a), cy+r*math.sin(a),
                                random.uniform(0,6.28)))
        for _ in range(16):
            a=random.uniform(0,6.28); r=random.uniform(0,R*.6)
            self._base.append((cx+r*math.cos(a), cy+r*math.sin(a),
                                random.uniform(0,6.28)))
        t=QTimer(self); t.timeout.connect(self._tick); t.start(30)

    def _tick(self): self._t+=0.022; self.update()

    def paintEvent(self,e):
        qp=QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        qp.fillRect(self.rect(),Qt.transparent)
        cx,cy=120,120

        # rings
        for r,a in [(108,22),(85,32),(62,42),(40,52)]:
            pr=r+2.5*math.sin(self._t*1.4)
            c=QColor(0,229,255,a)
            qp.setPen(_pen(c,0.8)); qp.setBrush(Qt.NoBrush)
            qp.drawEllipse(QRectF(cx-pr,cy-pr,pr*2,pr*2))

        # rotating dashed
        qp.save(); qp.translate(cx,cy); qp.rotate(self._t*15)
        p=QPen(QColor(0,229,255,28),0.6,Qt.DashLine)
        qp.setPen(p); qp.drawEllipse(QRectF(-112,-112,224,224)); qp.restore()

        # inner glow
        rg=QRadialGradient(cx,cy,95)
        rg.setColorAt(0,QColor(0,70,160,40)); rg.setColorAt(1,QColor(0,0,0,0))
        qp.setBrush(QBrush(rg)); qp.setPen(Qt.NoPen)
        qp.drawEllipse(QRectF(cx-110,cy-110,220,220))

        # animated positions
        pos=[]
        for (ox,oy,ph) in self._base:
            dx=2.2*math.sin(self._t*.85+ph)
            dy=2.2*math.cos(self._t*.65+ph*1.2)
            pos.append((ox+dx,oy+dy))

        # edges
        for i,(x1,y1) in enumerate(pos):
            for j,(x2,y2) in enumerate(pos):
                if j<=i: continue
                d=math.hypot(x2-x1,y2-y1)
                if d < 75:  # FIXED: was d<<75 (bit-shift typo)
                    a=max(0,int(120*(1-d/75)))
                    qp.setPen(_pen(QColor(0,229,255,a),0.5))
                    qp.drawLine(QPointF(x1,y1),QPointF(x2,y2))

        # nodes
        for (x,y) in pos:
            g=QRadialGradient(x,y,6)
            g.setColorAt(0,QColor(0,229,255,140)); g.setColorAt(1,QColor(0,229,255,0))
            qp.setBrush(QBrush(g)); qp.setPen(Qt.NoPen)
            qp.drawEllipse(QRectF(x-6,y-6,12,12))
            qp.setBrush(QBrush(QColor(210,250,255,235)))
            qp.drawEllipse(QRectF(x-1.7,y-1.7,3.4,3.4))
        qp.end()


# ── neural wave (right) ───────────────────────────────────────────────────────
class WaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180,240)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._t=0.0; self._dots=[_Dot(180,240) for _ in range(22)]
        t=QTimer(self); t.timeout.connect(self._tick); t.start(30)

    def _tick(self):
        self._t+=0.038
        for d in self._dots: d.step()
        self.update()

    def paintEvent(self,e):
        qp=QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        qp.fillRect(self.rect(),Qt.transparent)
        for off,amp,freq,col,ba in [
            (0.0,42,1.0,QColor(0,229,255),60),
            (1.0,30,1.3,QColor(100,80,240),50),
            (2.2,48,0.8,QColor(30,140,255),42),
        ]:
            pts=[]
            for yi in range(0,self.height()+5,5):
                t2=yi/self.height()
                x=self.width()/2+amp*math.sin(freq*t2*6.28+off+self._t)
                x+=amp*.3*math.sin(freq*1.6*t2*6.28-off*.4+self._t*.55)
                pts.append(QPointF(x,float(yi)))
            for i in range(0,len(pts)-1,2):
                p1,p2=pts[i],pts[i+1]
                fade=abs(math.sin(self._t+i*.08))
                c=QColor(col); c.setAlpha(int(ba*(.3+.7*fade)))
                qp.setPen(_pen(c,1.0)); qp.drawLine(p1,p2)
            for i in range(0,len(pts),6):
                pt=pts[i]
                g=QRadialGradient(pt.x(),pt.y(),5)
                gc=QColor(col); gc.setAlpha(ba); g.setColorAt(0,gc)
                gc2=QColor(col); gc2.setAlpha(0); g.setColorAt(1,gc2)
                qp.setBrush(QBrush(g)); qp.setPen(Qt.NoPen)
                qp.drawEllipse(QRectF(pt.x()-5,pt.y()-5,10,10))
                qp.setBrush(QBrush(QColor(255,255,255,140)))
                qp.drawEllipse(QRectF(pt.x()-1.3,pt.y()-1.3,2.6,2.6))
        for d in self._dots: d.paint(qp)
        qp.end()


# ── AI POWERED pill ───────────────────────────────────────────────────────────
class AIBadge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(138,28); self.setAttribute(Qt.WA_TranslucentBackground)
        self._t=0.0
        t=QTimer(self); t.timeout.connect(self._tick); t.start(38)
    def _tick(self): self._t+=0.065; self.update()
    def paintEvent(self,e):
        qp=QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        path=QPainterPath(); path.addRoundedRect(QRectF(0,0,w,h),h/2,h/2)
        qp.fillPath(path,QBrush(QColor(0,229,255,20)))
        pulse=abs(math.sin(self._t))
        qp.setPen(_pen(QColor(0,229,255,int(95+75*pulse)),0.9))
        qp.setBrush(Qt.NoBrush); qp.drawPath(path)
        qp.setPen(QColor(0,229,255))
        f=QFont("Segoe UI",8,QFont.Weight.DemiBold); qp.setFont(f)
        qp.drawText(QRectF(0,0,w,h),Qt.AlignCenter,"✦  AI POWERED")
        qp.end()


# ── gradient "Studio" ─────────────────────────────────────────────────────────
class GradLabel(QWidget):
    def __init__(self, text, px, parent=None):
        super().__init__(parent)
        self._text=text; self._px=px
        self.setAttribute(Qt.WA_TranslucentBackground)
        f=QFont("Segoe UI",px,QFont.Weight.ExtraBold)
        fm=QFontMetrics(f)
        self.setFixedSize(fm.horizontalAdvance(text)+14, fm.height()+6)
    def paintEvent(self,e):
        qp=QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        f=QFont("Segoe UI",self._px,QFont.Weight.ExtraBold)
        fm=QFontMetrics(f); qp.setFont(f)
        for dx,dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
            qp.setPen(_pen(QColor(0,229,255,45),3))
            qp.drawText(QRectF(dx,dy,self.width(),self.height()),
                        Qt.AlignLeft|Qt.AlignVCenter,self._text)
        path=QPainterPath()
        path.addText(0,fm.ascent()+2,f,self._text)
        g=QLinearGradient(0,0,self.width(),0)
        g.setColorAt(0,QColor(0,229,255)); g.setColorAt(1,QColor(155,70,245))
        qp.setPen(Qt.NoPen); qp.setBrush(QBrush(g)); qp.drawPath(path)
        qp.end()


# ── SVG-style icon painter helpers ────────────────────────────────────────────
def _draw_hand_icon(qp: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Minimalist sign-language hand: open palm with 3 rays."""
    s = size / 2
    qp.setPen(_pen(color, 1.6)); qp.setBrush(Qt.NoBrush)
    # palm oval
    qp.drawEllipse(QRectF(cx-s*.55, cy-s*.3, s*1.1, s*.9))
    # three finger rays upward
    for dx in (-s*.3, 0, s*.3):
        qp.drawLine(QPointF(cx+dx, cy-s*.28), QPointF(cx+dx, cy-s*.85))
    # thumb right
    qp.drawLine(QPointF(cx+s*.52, cy-.05*s), QPointF(cx+s*.85, cy-s*.35))

def _draw_grad_icon(qp: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Graduation cap: flat top square + tassel."""
    s = size / 2
    qp.setPen(_pen(color, 1.6)); qp.setBrush(Qt.NoBrush)
    # cap top (diamond)
    pts = [QPointF(cx, cy-s*.75), QPointF(cx+s*.65, cy-s*.35),
           QPointF(cx, cy+s*.05),  QPointF(cx-s*.65, cy-s*.35)]
    for i in range(4):
        qp.drawLine(pts[i], pts[(i+1)%4])
    # brim rectangle
    qp.drawRoundedRect(QRectF(cx-s*.42, cy-s*.15, s*.84, s*.52), 4, 4)
    # tassel
    qp.drawLine(QPointF(cx+s*.62, cy-s*.32), QPointF(cx+s*.62, cy+s*.28))
    qp.drawEllipse(QRectF(cx+s*.5, cy+s*.2, s*.24, s*.24))

def _draw_wave_icon(qp: QPainter, cx: float, cy: float, size: float, color: QColor):
    """Audio waveform: 5 vertical bars of varying height."""
    s = size / 2
    qp.setPen(_pen(color, 1.8))
    heights = [0.30, 0.60, 1.0, 0.60, 0.30]
    spacing = s * 0.36
    for i, h in enumerate(heights):
        x = cx + (i - 2) * spacing
        bar = s * h
        qp.drawLine(QPointF(x, cy - bar), QPointF(x, cy + bar))


# ── icon circle widget ────────────────────────────────────────────────────────
class IconCircle(QWidget):
    """Draws a glowing circle with a vector icon inside."""
    def __init__(self, kind: str, accent: QColor, parent=None):
        super().__init__(parent)
        self._kind = kind; self._accent = accent
        self.setFixedSize(54, 54)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, e):
        qp = QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        cx, cy = 27.0, 27.0; r = 22.0
        ac = self._accent

        # glow bg
        g = QRadialGradient(cx, cy, r+6)
        gc = QColor(ac); gc.setAlpha(55); g.setColorAt(0, gc)
        gc2 = QColor(ac); gc2.setAlpha(0); g.setColorAt(1, gc2)
        qp.setBrush(QBrush(g)); qp.setPen(Qt.NoPen)
        qp.drawEllipse(QRectF(cx-r-6, cy-r-6, (r+6)*2, (r+6)*2))

        # circle bg
        bg = QRadialGradient(cx, cy, r)
        b1 = QColor(ac); b1.setAlpha(40); bg.setColorAt(0, b1)
        b2 = QColor(ac); b2.setAlpha(12); bg.setColorAt(1, b2)
        qp.setBrush(QBrush(bg))
        qp.setPen(_pen(QColor(ac.red(), ac.green(), ac.blue(), 90), 1.0))
        qp.drawEllipse(QRectF(cx-r, cy-r, r*2, r*2))

        # icon
        if   self._kind == "hand": _draw_hand_icon(qp, cx, cy, 30, ac)
        elif self._kind == "grad": _draw_grad_icon(qp, cx, cy, 30, ac)
        elif self._kind == "wave": _draw_wave_icon(qp, cx, cy, 30, ac)
        qp.end()


# ── feature card ──────────────────────────────────────────────────────────────
class FeatureCard(QWidget):
    def __init__(self, kind, title, desc, btn_text, accent: QColor, parent=None):
        super().__init__(parent)
        self._accent = accent; self._hov = False
        self.setFixedSize(230, 230)
        self.setCursor(Qt.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 16)
        lay.setSpacing(0)

        lay.addWidget(IconCircle(kind, accent))
        lay.addSpacing(12)

        r,g,b = accent.red(), accent.green(), accent.blue()
        tl = QLabel(title)
        tl.setStyleSheet(
            f"color:rgb({r},{g},{b});font-size:13px;font-weight:700;"
            "background:transparent;")
        lay.addWidget(tl)
        lay.addSpacing(7)

        dl = QLabel(desc)
        dl.setWordWrap(True)
        dl.setStyleSheet(f"color:{S_SEC};font-size:11px;line-height:1.5;background:transparent;")
        lay.addWidget(dl)
        lay.addStretch()

    def enterEvent(self,e): self._hov=True;  self.update()
    def leaveEvent(self,e): self._hov=False; self.update()

    def paintEvent(self,e):
        qp=QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        ac=self._accent; r,g,b=ac.red(),ac.green(),ac.blue()

        path=QPainterPath(); path.addRoundedRect(QRectF(0,0,w,h),16,16)

        bg=QLinearGradient(0,0,0,h)
        bg.setColorAt(0,QColor(10,20,48,215)); bg.setColorAt(1,QColor(7,13,32,215))
        qp.fillPath(path,QBrush(bg))

        border_a = 105 if self._hov else 58
        qp.setPen(_pen(QColor(r,g,b,border_a),0.9))
        qp.setBrush(Qt.NoBrush); qp.drawPath(path)

        # top accent line
        qp.setPen(_pen(QColor(r,g,b,160 if self._hov else 80),1.2))
        qp.drawLine(QPointF(16,0.6),QPointF(w-16,0.6))

        if self._hov:
            gl=QRadialGradient(w/2,h,h*.75)
            gl.setColorAt(0,QColor(r,g,b,22)); gl.setColorAt(1,QColor(0,0,0,0))
            qp.fillPath(path,QBrush(gl))
        qp.end()


# ── CTA button ────────────────────────────────────────────────────────────────
class CTAButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(420, 54)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background:transparent;border:none;")
        self._sw=0.0; self._hov=False; self._pt=0.0
        self._anim=QPropertyAnimation(self,b"sweep")
        self._anim.setDuration(800)
        self._anim.setStartValue(0.0); self._anim.setEndValue(1.0)
        t=QTimer(self); t.timeout.connect(self._tick); t.start(28)

    def _tick(self): self._pt+=0.048; self.update()
    def get_sweep(self): return self._sw
    def set_sweep(self,v): self._sw=v; self.update()
    sweep=Property(float,get_sweep,set_sweep)

    def enterEvent(self,e):
        self._hov=True
        self._anim.stop(); self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0); self._anim.start()
    def leaveEvent(self,e): self._hov=False

    def paintEvent(self,e):
        qp=QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        path=QPainterPath(); path.addRoundedRect(QRectF(0,0,w,h),27,27)

        g=QLinearGradient(0,0,w,0)
        g.setColorAt(0,QColor(0,220,255)); g.setColorAt(1,QColor(110,60,245))
        qp.fillPath(path,QBrush(g))

        if self._hov: qp.fillPath(path,QBrush(QColor(255,255,255,16)))

        if self._sw>0:
            sw=w*.26; sx=-sw+self._sw*(w+sw)
            sg=QLinearGradient(sx-sw,0,sx+sw,0)
            sg.setColorAt(0,QColor(255,255,255,0))
            sg.setColorAt(.5,QColor(255,255,255,48))
            sg.setColorAt(1,QColor(255,255,255,0))
            qp.fillPath(path,QBrush(sg))

        pa=int(50+35*math.sin(self._pt))
        qp.setPen(_pen(QColor(0,229,255,pa),2.0))
        qp.setBrush(Qt.NoBrush); qp.drawPath(path)

        qp.setPen(QColor(255,255,255))
        f=QFont("Segoe UI",14,QFont.Weight.Bold); qp.setFont(f)
        qp.drawText(QRectF(0,0,w-36,h),Qt.AlignCenter,"Enter Studio")
        ax,ay=w-34,h//2
        qp.setPen(_pen(QColor(255,255,255),1.8))
        qp.drawLine(QPointF(ax,float(ay)),QPointF(ax+13,float(ay)))
        qp.drawLine(QPointF(ax+7,ay-5.0),QPointF(ax+13,float(ay)))
        qp.drawLine(QPointF(ax+7,ay+5.0),QPointF(ax+13,float(ay)))
        qp.end()


# ── bottom badge ──────────────────────────────────────────────────────────────
def _draw_target(qp,cx,cy,s,c):
    qp.setPen(_pen(c,1.3)); qp.setBrush(Qt.NoBrush)
    for r in [s*.5,s*.33,s*.16]:
        qp.drawEllipse(QRectF(cx-r,cy-r,r*2,r*2))
    qp.drawLine(QPointF(cx-s*.6,cy),QPointF(cx+s*.6,cy))
    qp.drawLine(QPointF(cx,cy-s*.6),QPointF(cx,cy+s*.6))

def _draw_bolt(qp,cx,cy,s,c):
    qp.setPen(_pen(c,1.4)); qp.setBrush(Qt.NoBrush)
    pts=[QPointF(cx+s*.2,cy-s*.7),QPointF(cx-s*.1,cy-s*.05),
         QPointF(cx+s*.25,cy-s*.05),QPointF(cx-s*.2,cy+s*.7)]
    for i in range(len(pts)-1): qp.drawLine(pts[i],pts[i+1])

def _draw_lock(qp,cx,cy,s,c):
    qp.setPen(_pen(c,1.3)); qp.setBrush(Qt.NoBrush)
    qp.drawRoundedRect(QRectF(cx-s*.4,cy-s*.1,s*.8,s*.7),3,3)
    qp.drawArc(QRectF(cx-s*.28,cy-s*.55,s*.56,s*.55),0,180*16)

def _draw_cloud(qp,cx,cy,s,c):
    qp.setPen(_pen(c,1.3)); qp.setBrush(Qt.NoBrush)
    qp.drawEllipse(QRectF(cx-s*.38,cy-s*.25,s*.55,s*.55))
    qp.drawEllipse(QRectF(cx-s*.05,cy-s*.38,s*.45,s*.45))
    qp.drawEllipse(QRectF(cx+s*.18,cy-s*.18,s*.38,s*.38))
    qp.drawLine(QPointF(cx-s*.38,cy+s*.2),QPointF(cx+s*.56,cy+s*.2))

_BADGE_ICONS = {
    "target": _draw_target,
    "bolt":   _draw_bolt,
    "lock":   _draw_lock,
    "cloud":  _draw_cloud,
}

class BadgeCanvas(QWidget):
    def __init__(self, kind, label, parent=None):
        super().__init__(parent)
        self._kind=kind; self._label=label; self._hov=False
        self.setFixedSize(148,40); self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def enterEvent(self,e): self._hov=True;  self.update()
    def leaveEvent(self,e): self._hov=False; self.update()

    def paintEvent(self,e):
        qp=QPainter(self); qp.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        path=QPainterPath(); path.addRoundedRect(QRectF(0,0,w,h),10,10)
        qp.fillPath(path,QBrush(QColor(10,22,50,210)))
        a=100 if self._hov else 55
        qp.setPen(_pen(QColor(0,229,255,a),0.8)); qp.setBrush(Qt.NoBrush)
        qp.drawPath(path)
        if self._hov:
            gl=QRadialGradient(w/2,h/2,w*.5)
            gl.setColorAt(0,QColor(0,229,255,16)); gl.setColorAt(1,QColor(0,0,0,0))
            qp.fillPath(path,QBrush(gl))
        # icon
        ic=C_CYAN
        _BADGE_ICONS[self._kind](qp,18,h/2,9,ic)
        # label
        qp.setPen(C_SEC)
        f=QFont("Segoe UI",10,QFont.Weight.Medium); qp.setFont(f)
        qp.drawText(QRectF(34,0,w-40,h),Qt.AlignVCenter|Qt.AlignLeft,self._label)
        qp.end()


# ── main splash ───────────────────────────────────────────────────────────────
class SplashScreen(QWidget):
    """
    Futuristic splash screen — compact, centered, vector icons.

    Signal:
        enter_clicked  — user pressed "Enter Studio"
    """
    enter_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SplashScreen")
        self.setMinimumSize(960, 640)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._bg = BgCanvas(self)
        self._build()
        self._entrance()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # transparent overlay widget
        ow = QWidget(); ow.setStyleSheet("background:transparent;")
        root.addWidget(ow)

        outer = QVBoxLayout(ow)
        outer.setContentsMargins(28,14,28,12); outer.setSpacing(0)

        # tiny top-left label
        tl = QLabel("SignBridge Studio")
        tl.setStyleSheet(f"color:{S_MUTED};font-size:9px;font-weight:500;"
                         "letter-spacing:3px;background:transparent;")
        outer.addWidget(tl)
        outer.addSpacing(2)

        # ── three columns ──
        cols = QHBoxLayout(); cols.setSpacing(0)

        # LEFT
        lc = QVBoxLayout(); lc.setAlignment(Qt.AlignVCenter)
        self._constellation = ConstellationWidget()
        lc.addStretch(); lc.addWidget(self._constellation, alignment=Qt.AlignHCenter)
        lc.addStretch()
        cols.addLayout(lc)
        cols.addSpacing(4)

        # CENTER
        cc = QVBoxLayout(); cc.setSpacing(0); cc.setAlignment(Qt.AlignTop|Qt.AlignHCenter)

        # AI badge
        br=QHBoxLayout(); br.setAlignment(Qt.AlignHCenter)
        br.addWidget(AIBadge()); cc.addLayout(br)
        cc.addSpacing(12)

        # Title
        tr=QHBoxLayout(); tr.setSpacing(8); tr.setAlignment(Qt.AlignHCenter)
        tr.setContentsMargins(0,0,0,0)
        sb=QLabel("SignBridge")
        sb.setStyleSheet("color:#F5F7FF;font-size:42px;font-weight:800;"
                         "font-family:'Segoe UI',sans-serif;background:transparent;")
        tr.addWidget(sb)
        gl=GradLabel("Studio",42); tr.addWidget(gl)
        tw=QWidget(); tw.setStyleSheet("background:transparent;"); tw.setLayout(tr)
        cc.addWidget(tw, alignment=Qt.AlignHCenter)
        cc.addSpacing(8)

        # Subtitle
        sub=QLabel("AI Sign Language Translator")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#F0F2FF;font-size:15px;font-weight:600;background:transparent;")
        cc.addWidget(sub)
        cc.addSpacing(4)

        # tagline
        tg=QLabel("Break barriers. Bridge communication. Empower everyone.")
        tg.setAlignment(Qt.AlignCenter)
        tg.setStyleSheet(f"color:{S_MUTED};font-size:11px;background:transparent;")
        cc.addWidget(tg)
        cc.addSpacing(18)

        # cards
        cards_row=QHBoxLayout(); cards_row.setSpacing(12)
        cards_row.setAlignment(Qt.AlignHCenter)
        for kind,title,desc,btn,ac in [
            ("hand","Real-time Translation",
             "Instantly translate sign language\nthrough your camera with AI precision.",
             "Start Translating →", QColor(0,229,255)),
            ("grad","Learning Companion",
             "Learn sign language step-by-step\nwith interactive lessons & AI feedback.",
             "Start Learning →", QColor(100,80,240)),
            ("wave","Create Your Own Experience",
             "create you own signs and train a custom ai model on them",
             "Start Synthesizing →", QColor(30,140,255)),
        ]:
            cards_row.addWidget(FeatureCard(kind,title,desc,btn,ac))
        cc.addLayout(cards_row)
        cc.addSpacing(18)

        # CTA
        cta_r=QHBoxLayout(); cta_r.setAlignment(Qt.AlignHCenter)
        self._cta=CTAButton(); self._cta.clicked.connect(self.enter_clicked.emit)
        cta_r.addWidget(self._cta); cc.addLayout(cta_r)
        cc.addSpacing(9)

        # tagline below CTA
        bt=QLabel("✦   Your journey to inclusive communication begins here")
        bt.setAlignment(Qt.AlignCenter)
        bt.setStyleSheet(f"color:{S_MUTED};font-size:10px;background:transparent;")
        cc.addWidget(bt)
        cc.addSpacing(12)

        # badges
        bad_r=QHBoxLayout(); bad_r.setSpacing(8); bad_r.setAlignment(Qt.AlignHCenter)
        for kind,txt in [("target","91.4% Accuracy"),("bolt","Real-time AI"),
                         ("lock","Privacy First")]:
            bad_r.addWidget(BadgeCanvas(kind,txt))
        cc.addLayout(bad_r)
        cc.addSpacing(10)

        # footer
        ft=QLabel("MEDIAPIPE  |  PYTORCH  |  GROQ LLM  |  PYSIDE6")
        ft.setAlignment(Qt.AlignCenter)
        ft.setStyleSheet(f"color:{S_MUTED};font-size:8px;letter-spacing:2px;background:transparent;")
        cc.addWidget(ft)

        cols.addLayout(cc, stretch=1)
        cols.addSpacing(4)

        # RIGHT
        rc=QVBoxLayout(); rc.setAlignment(Qt.AlignVCenter)
        self._wave=WaveWidget()
        rc.addStretch(); rc.addWidget(self._wave,alignment=Qt.AlignHCenter); rc.addStretch()
        cols.addLayout(rc)

        outer.addLayout(cols)

    def _entrance(self):
        self._fx=QGraphicsOpacityEffect(self); self._fx.setOpacity(0.0)
        self.setGraphicsEffect(self._fx)
        self._anim=QPropertyAnimation(self._fx,b"opacity")
        self._anim.setDuration(700); self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0); self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.finished.connect(lambda: self.setGraphicsEffect(None))
        self._anim.start()

    def resizeEvent(self,e):
        self._bg.setGeometry(self.rect()); super().resizeEvent(e)


# ── entry ─────────────────────────────────────────────────────────────────────
def main():
    app=QApplication(sys.argv)
    app.setApplicationName("SignBridge Studio")
    w=SplashScreen()
    w.setWindowTitle("SignBridge Studio")
    w.resize(1100,700)
    w.show()
    w.enter_clicked.connect(app.quit)
    sys.exit(app.exec())

if __name__=="__main__":
    main()