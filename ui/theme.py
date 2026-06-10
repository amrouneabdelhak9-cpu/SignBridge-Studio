# ui/theme.py
from PySide6.QtGui import QColor, QLinearGradient


class FuturisticTheme:
    # Deep cinematic background
    BG_DEEP = "#02040B"
    BG_MID = "#030816"
    BG_LIGHT = "#071124"

    # Glass surfaces (translucent)
    GLASS_BG = "rgba(12, 20, 32, 0.65)"
    GLASS_BG_STRONG = "rgba(12, 20, 32, 0.85)"
    GLASS_BORDER = "rgba(0, 229, 255, 0.25)"
    GLASS_BORDER_HOVER = "rgba(0, 229, 255, 0.6)"
    GLASS_GLOW = QColor(0, 229, 255, 80)  # ← Added missing attribute

    # Primary AI accents
    CYAN = "#00E5FF"
    BLUE_AURORA = "#33CFFF"
    VIOLET_HOLO = "#7B61FF"
    PURPLE_NEON = "#A855F7"

    # Accents
    MAGENTA = "#FF4DDB"
    EMERALD = "#00FFB2"
    RED_NEURAL = "#FF3B5C"

    # Text
    TEXT_PRIMARY = "#F5F7FF"
    TEXT_SECONDARY = "#AAB3C5"
    TEXT_MUTED = "#6E7891"

    # Gradients
    @staticmethod
    def primary_gradient():
        grad = QLinearGradient(0, 0, 1, 1)
        grad.setColorAt(0, QColor(FuturisticTheme.CYAN))
        grad.setColorAt(1, QColor(FuturisticTheme.VIOLET_HOLO))
        return grad

    @staticmethod
    def danger_gradient():
        grad = QLinearGradient(0, 0, 1, 1)
        grad.setColorAt(0, QColor(FuturisticTheme.RED_NEURAL))
        grad.setColorAt(1, QColor("#FF006E"))
        return grad

    @staticmethod
    def success_gradient():
        grad = QLinearGradient(0, 0, 1, 1)
        grad.setColorAt(0, QColor(FuturisticTheme.EMERALD))
        grad.setColorAt(1, QColor("#00D68F"))
        return grad