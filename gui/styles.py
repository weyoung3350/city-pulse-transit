"""统一样式常量 — 颜色主题、字体、尺寸"""

from config import FONT_FAMILY

# ── 颜色 ──────────────────────────────────────────────
COLORS = {
    "bg_main": "#f5f7fa",
    "bg_panel": "#ffffff",
    "bg_title": "#1a73e8",
    "text_title": "#ffffff",
    "text_primary": "#202124",
    "text_secondary": "#5f6368",
    "accent": "#ea4335",
    "accent_green": "#34a853",
    "accent_yellow": "#fbbc04",
    "border": "#e0e0e0",
}

# ── 字体 ──────────────────────────────────────────────
FONT_TITLE = (FONT_FAMILY, 16, "bold")
FONT_HEADING = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)

# ── 尺寸 ──────────────────────────────────────────────
WINDOW_SIZE = "1200x800"
WINDOW_MIN = (1000, 650)
CONTROL_WIDTH = 220
REPORT_WIDTH = 280
TITLE_HEIGHT = 50
STATUS_HEIGHT = 25
