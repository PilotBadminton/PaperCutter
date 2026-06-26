"""
配置模块 - 语义化设计令牌系统 (Frutiger Aero)
"""
import os
from pathlib import Path


class Settings:
    PDF_ZOOM = 2.5
    MAX_CACHE_SIZE = 10

    # ── Frutiger Aero 基础色板 ─────────────────────────────────────────
    AERO_SKY       = '#00BFFF'   # 天蓝 (DeepSkyBlue)     — 交互高亮
    AERO_AZURE     = '#0099CC'   # 蔚蓝                   — 深色表层
    AERO_OCEAN     = '#008B8B'   # 海洋深青 (DarkCyan)     — 深层背景
    AERO_TEAL      = '#00CED1'   # 湖水绿 (DarkTurquoise)  — 背景基色
    AERO_SEAFOAM   = '#20B2AA'   # 海沫绿 (LightSeaGreen) — 背景边缘
    AERO_MINT      = '#66D9C8'   # 薄荷                   — 点缀
    AERO_GLASS     = '#E0FFFF'   # 玻璃白 (LightCyan)     — 高光/亮域
    AERO_CORAL     = '#FF6B6B'   # 珊瑚红                 — 选区/危险
    AERO_SUN       = '#FFD93D'   # 暖阳性感               — 星标/提示

    # ── 语义文字令牌 ──────────────────────────────────────────────────
    TEXT = {
        'primary':     '#06263A',   # 深海靛蓝 — 玻璃面板上主文字
        'secondary':   '#274F68',   # 蓝灰     — 辅助说明/标签
        'placeholder': '#60798C',   # 中蓝灰   — 占位符/禁用
        'disabled':    '#7890A0',   # 中灰蓝   — 禁用态
        'on_accent':   '#FFFFFF',   # 白色   — 彩色按钮上文字
        'inverse':     '#F0F8FF',   # 爱丽丝蓝—深色底上的文字
        'link':        '#075985',   # 深海蓝 — 可点击文字
        'selection':   '#FFFFFF',   # 白色   — 选中高亮上的文字
    }

    # ── 语义表面令牌 ──────────────────────────────────────────────────
    SURFACE = {
        'bg_base':     'rgba(238, 252, 255, 0.84)',   # 最底层承托
        'panel':       'rgba(240, 253, 255, 0.90)',   # 毛玻璃面板
        'panel_hover': 'rgba(252, 255, 255, 0.96)',   # 面板悬停
        'panel_focus': 'rgba(255, 255, 255, 0.97)',   # 面板聚焦
        'input':       'rgba(255, 255, 255, 0.93)',   # 输入框
        'input_focus': 'rgba(255, 255, 255, 0.99)',   # 输入框聚焦
        'button':      'qlineargradient(x1:0, y1:0, x2:0, y2:1, '
                           'stop:0 rgba(255,255,255,0.98), '
                           'stop:0.18 rgba(255,255,255,0.86), '
                           'stop:0.50 rgba(215,246,252,0.86), '
                           'stop:1 rgba(132,211,232,0.78))',
        'button_hov':  'qlineargradient(x1:0, y1:0, x2:0, y2:1, '
                           'stop:0 rgba(255,255,255,1.00), '
                           'stop:0.18 rgba(255,255,255,0.94), '
                           'stop:0.54 rgba(228,251,255,0.94), '
                           'stop:1 rgba(105,205,233,0.90))',
        'button_prs':  'qlineargradient(x1:0, y1:0, x2:0, y2:1, '
                           'stop:0 rgba(106,196,225,0.90), '
                           'stop:0.55 rgba(198,240,250,0.92), '
                           'stop:1 rgba(255,255,255,0.94))',
        'button_act':  'qlineargradient(x1:0, y1:0, x2:0, y2:1, '
                           'stop:0 rgba(18,191,238,0.90), '
                           'stop:0.52 rgba(0,154,214,0.84), '
                           'stop:1 rgba(0,118,186,0.82))',
        'button_act_hov': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, '
                           'stop:0 rgba(69,212,248,0.96), '
                           'stop:1 rgba(0,137,204,0.92))',
        'button_act_prs': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, '
                           'stop:0 rgba(0,112,178,0.92), '
                           'stop:1 rgba(35,192,235,0.90))',
        'button_dsb':  'rgba(226, 243, 248, 0.66)',
        'list_item':   'rgba(255, 255, 255, 0.90)',
        'list_sel':    'rgba(0, 154, 214, 0.68)',
        'tooltip':     'rgba(20, 40, 60, 0.92)',
        'dropdown':    'rgba(240, 248, 255, 0.95)',
        'statusbar':   'rgba(241, 253, 255, 0.90)',
        'toolbar':     'rgba(241, 253, 255, 0.90)',
    }

    # ── 语义边框令牌 ──────────────────────────────────────────────────
    BORDER = {
        'subtle':      'rgba(91, 161, 187, 0.34)',
        'normal':      'rgba(42, 132, 166, 0.54)',
        'strong':      'rgba(18, 111, 155, 0.68)',
        'highlight':   'rgba(255, 255, 255, 0.98)',
        'accent':      'rgba(0, 139, 205, 0.78)',
        'focus':       'rgba(0, 124, 202, 0.92)',
        'input':       'rgba(44, 131, 168, 0.54)',
        'list_item':   'rgba(82, 150, 178, 0.36)',
        'divider':     'rgba(42, 132, 166, 0.42)',
    }

    # ── 字体层级 ──────────────────────────────────────────────────────
    FONTS = {
        'family':       'Microsoft YaHei UI',

        'size_caption':  11,     # 辅助信息（状态栏、坐标）
        'size_body':     13,     # 正文（列表项、标签）
        'size_label':    14,     # 小标题/按钮文字
        'size_subtitle': 16,     # 次级标题
        'size_title':    18,     # 主标题
        'size_hero':     24,     # 大标题

        'weight_regular':   400,
        'weight_medium':    500,
        'weight_semibold':  600,
        'weight_bold':      700,
    }

    # ── 间距体系 ──────────────────────────────────────────────────────
    SPACING = {
        'small':   8,
        'normal':  12,
        'large':   16,
        'xlarge':  24,
    }

    # ── 圆角体系 ──────────────────────────────────────────────────────
    RADIUS = {
        'micro':    4,
        'small':    6,
        'normal':   8,
        'medium':   10,
        'large':    12,
        'pill':     20,
    }
