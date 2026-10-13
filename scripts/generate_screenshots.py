# -*- coding: utf-8 -*-
"""Generate high-resolution screenshots and scenario demonstration graphics for README."""

import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from application.context import AppContext
from ui.floating_panel import FloatingPanel
from ui.settings_dialog import SettingsDialog
from ui.key_capture_dialog import KeyCaptureDialog


def draw_rounded_card(painter: QtGui.QPainter, rect: QtCore.QRectF, bg_color: QtGui.QColor, border_color: QtGui.QColor, radius: float = 10.0):
    painter.save()
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    path = QtGui.QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    painter.fillPath(path, QtGui.QBrush(bg_color))
    painter.setPen(QtGui.QPen(border_color, 1.5))
    painter.drawPath(path)
    painter.restore()


def create_banner(img_dir: str, panel_pix: QtGui.QPixmap):
    width, height = 1100, 360
    pix = QtGui.QPixmap(width, height)
    pix.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    # 1. Background gradient
    grad = QtGui.QLinearGradient(0, 0, width, height)
    grad.setColorAt(0.0, QtGui.QColor("#0F141C"))
    grad.setColorAt(0.5, QtGui.QColor("#161D2A"))
    grad.setColorAt(1.0, QtGui.QColor("#0B0E14"))
    painter.fillRect(0, 0, width, height, grad)

    # Subtle grid accent
    painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 12), 1, QtCore.Qt.DotLine))
    for x in range(0, width, 40):
        painter.drawLine(x, 0, x, height)
    for y in range(0, height, 40):
        painter.drawLine(0, y, width, y)

    # 2. Left side: Title & Badges
    painter.setPen(QtGui.QColor("#38BDF8"))
    font_badge = QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold)
    painter.setFont(font_badge)
    painter.drawText(60, 75, "WINDOWS 免夺焦轻量级悬浮工作台 · QUICKINPUT")

    painter.setPen(QtGui.QColor("#F8FAFC"))
    font_title = QtGui.QFont("Microsoft YaHei UI", 26, QtGui.QFont.Bold)
    painter.setFont(font_title)
    painter.drawText(60, 125, "通用快捷输入工作台")

    painter.setPen(QtGui.QColor("#94A3B8"))
    font_sub = QtGui.QFont("Microsoft YaHei UI", 13)
    painter.setFont(font_sub)
    painter.drawText(60, 165, "零夺焦原生输入 · 矩阵布局自由定制 · 多步骤宏与中英双语")
    painter.drawText(60, 195, "国家标准公文排版 (GB/T 9704-2012) · 程序员控制台 · 客服与标注")

    # Feature pills
    features = [
        ("⚡ 零夺焦注入 (WS_EX_NOACTIVATE)", "#10B981"),
        ("🇨🇳/🇬🇧 中英双语实时切换", "#6366F1"),
        ("📦 绿色便携 (仅 24.7MB)", "#EC4899"),
        ("🛡️ 100% 单元测试全覆盖", "#0EA5E9"),
    ]
    cur_x = 60
    cur_y = 240
    for text, col in features:
        draw_rounded_card(painter, QtCore.QRectF(cur_x, cur_y, 225, 34), QtGui.QColor(30, 41, 59, 200), QtGui.QColor(col), 6)
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor("#F1F5F9"))
        painter.drawText(QtCore.QRectF(cur_x, cur_y, 225, 34), QtCore.Qt.AlignCenter, text)
        cur_x += 240

    # 3. Right side: Panel Preview Card with Glow
    glow_rect = QtCore.QRectF(740, 50, 310, 220)
    draw_rounded_card(painter, glow_rect, QtGui.QColor(15, 23, 42, 220), QtGui.QColor("#38BDF8"), 12)
    # Draw floating panel scaled
    scaled_panel = panel_pix.scaled(280, 160, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    painter.drawPixmap(755, 75, scaled_panel)

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(QtCore.QRectF(740, 235, 310, 24), QtCore.Qt.AlignCenter, "✦ 悬浮于任意应用之上 · 即点即输")

    painter.end()
    out_file = os.path.join(img_dir, "banner.png")
    pix.save(out_file, "PNG")
    print(f"Generated Banner: {out_file}")


def create_scene_official_doc(img_dir: str, panel_pix: QtGui.QPixmap):
    width, height = 1040, 540
    pix = QtGui.QPixmap(width, height)
    pix.fill(QtGui.QColor("#0F172A"))

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    # Title header
    painter.setPen(QtGui.QColor("#F8FAFC"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 16, QtGui.QFont.Bold))
    painter.drawText(40, 45, "场景一：党政机关公文标准排版 (GB/T 9704-2012)")

    painter.setPen(QtGui.QColor("#94A3B8"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 11))
    painter.drawText(40, 75, "严格遵循国家公文标准规范，告别繁琐菜单点击，一键完成页边距、中西文字体字号、22行标准行距设置")

    # Left: Mockup Word A4 Paper Card
    paper_rect = QtCore.QRectF(40, 100, 560, 400)
    draw_rounded_card(painter, paper_rect, QtGui.QColor("#FFFFFF"), QtGui.QColor("#CBD5E1"), 8)

    # Word Paper Content
    painter.setPen(QtGui.QColor("#0284C7"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9, QtGui.QFont.Bold))
    # Margins guides
    painter.drawText(60, 125, "↑ 天头（上白边）：37 mm ± 1 mm")
    painter.drawText(60, 485, "↓ 地脚（下白边）：35 mm ± 1 mm    |    ← 订口: 28 mm    |    切口: 26 mm →")

    # Document Number (发文字号)
    painter.setPen(QtGui.QColor("#1E293B"))
    painter.setFont(QtGui.QFont("FangSong", 11))
    painter.drawText(QtCore.QRectF(40, 145, 560, 24), QtCore.Qt.AlignCenter, "国发〔2026〕1号")

    # Title (公文标题)
    painter.setPen(QtGui.QColor("#0F172A"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 14, QtGui.QFont.Bold))
    painter.drawText(QtCore.QRectF(40, 180, 560, 30), QtCore.Qt.AlignCenter, "国务院关于推进标准化办公排版的通知")

    # Heading 1 (一级标题: 黑体)
    painter.setFont(QtGui.QFont("SimHei", 11, QtGui.QFont.Bold))
    painter.drawText(75, 235, "一、总体要求与基本原则")

    # Body (正文: 仿宋_GB2312)
    painter.setFont(QtGui.QFont("FangSong", 10))
    painter.drawText(75, 265, "    各地区、各部门要高度重视公文规范化工作，严格按照《党政机关公文格式》")
    painter.drawText(75, 288, "国家标准（GB/T 9704-2012）要求，准确设定页面尺寸与字体字号。正文统一使用")
    painter.drawText(75, 311, "仿宋三号字，西文使用 Times New Roman，行距设置为固定值 28.9 磅（对应每面 22 行）。")

    # Heading 2 (二级标题: 楷体)
    painter.setFont(QtGui.QFont("KaiTi", 11, QtGui.QFont.Bold))
    painter.drawText(75, 350, "    （一）加强公文版面规范化管理")

    # Heading 3 (三级标题: 仿宋加粗)
    painter.setFont(QtGui.QFont("FangSong", 10, QtGui.QFont.Bold))
    painter.drawText(75, 380, "    1. 全面落实版心页边距与行字符数标准。")

    # Page number
    painter.setFont(QtGui.QFont("SimSun", 10))
    painter.drawText(QtCore.QRectF(40, 440, 560, 20), QtCore.Qt.AlignCenter, "— 1 —")

    # Right side: Floating Panel Mockup + Callout badges
    panel_card = QtCore.QRectF(630, 100, 370, 400)
    draw_rounded_card(painter, panel_card, QtGui.QColor("#1E293B"), QtGui.QColor("#334155"), 10)

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 12, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(655, 135, "公文常用格式悬浮面板 (2×5 栅格)")

    # Draw Floating Panel
    scaled_panel = panel_pix.scaled(320, 180, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    painter.drawPixmap(655, 155, scaled_panel)

    # Bullet point annotations
    badges = [
        ("【边距】", "自动设置天头37 / 地脚35 / 订口28 / 切口26 mm"),
        ("【正文】", "一键设置 仿宋_GB2312 + Times New Roman 三号 两端对齐"),
        ("【行距】", "设置段落固定值 28.9 磅（精准对应标准每页 22 行）"),
        ("【六角】", "快速插入发文字号专用六角括号〔 〕并光标居中"),
        ("【大标】", "二号 方正小标宋简体 居中对齐"),
        ("【标1/2/3】", "一级黑体、二级楷体、三级仿宋加粗快速应用"),
    ]
    cur_by = 310
    for b_title, b_desc in badges:
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor("#FBBF24"))
        painter.drawText(655, cur_by, b_title)
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 8))
        painter.setPen(QtGui.QColor("#E2E8F0"))
        painter.drawText(725, cur_by, b_desc)
        cur_by += 28

    painter.end()
    out_file = os.path.join(img_dir, "scene_official_doc.png")
    pix.save(out_file, "PNG")
    print(f"Generated Scene Official Doc: {out_file}")


def create_scene_programmer(img_dir: str, panel_pix: QtGui.QPixmap):
    width, height = 1040, 520
    pix = QtGui.QPixmap(width, height)
    pix.fill(QtGui.QColor("#0F172A"))

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    # Header
    painter.setPen(QtGui.QColor("#F8FAFC"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 16, QtGui.QFont.Bold))
    painter.drawText(40, 45, "场景二：程序员控制台与 DevOps 自动化快速输入")

    painter.setPen(QtGui.QColor("#94A3B8"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 11))
    painter.drawText(40, 75, "悬浮在终端、VS Code、Git Bash 上方，高频命令免重复敲击，支持动态日期变量与光标回退定位")

    # Left: Terminal Window Mockup
    term_rect = QtCore.QRectF(40, 100, 580, 380)
    draw_rounded_card(painter, term_rect, QtGui.QColor("#0D1117"), QtGui.QColor("#30363D"), 8)

    # Terminal Titlebar
    painter.fillRect(40, 100, 580, 32, QtGui.QColor("#161B22"))
    # Mac/Linux style dots
    for i, col in enumerate(["#FF5F56", "#FFBD2E", "#27C93F"]):
        painter.setBrush(QtGui.QBrush(QtGui.QColor(col)))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(55 + i * 18, 110, 12, 12)

    painter.setPen(QtGui.QColor("#C9D1D9"))
    painter.setFont(QtGui.QFont("Consolas", 10))
    painter.drawText(120, 122, "bash — 80x24 (QuickInput Terminal Automation)")

    # Terminal Content
    painter.setFont(QtGui.QFont("Consolas", 10))
    lines = [
        ("$ git status", "#58A6FF"),
        ("On branch main", "#8B949E"),
        ("Your branch is up to date with 'origin/main'.", "#8B949E"),
        ("", "#000000"),
        ("$ git pull --rebase", "#58A6FF"),
        ("Current branch main is up to date.", "#3FB950"),
        ("", "#000000"),
        ("$ docker ps -a", "#58A6FF"),
        ("CONTAINER ID   IMAGE          COMMAND       STATUS", "#8B949E"),
        ("4c01db0b339c   nginx:alpine   \"/docker-…\"   Up 3 hours", "#7EE787"),
        ("", "#000000"),
        ("$ // TODO(2026-10-13): optimize cache layer", "#D29922"),
        ("$ console.log(\"[DEBUG]\", data);", "#BC8CFF"),
    ]
    term_y = 155
    for text, col in lines:
        if text:
            painter.setPen(QtGui.QColor(col))
            painter.drawText(55, term_y, text)
        term_y += 20

    # Right: Floating Panel + Features
    panel_card = QtCore.QRectF(650, 100, 350, 380)
    draw_rounded_card(painter, panel_card, QtGui.QColor("#1E293B"), QtGui.QColor("#334155"), 10)

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 12, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(675, 135, "程序员常用命令面板 (2×3)")

    scaled_panel = panel_pix.scaled(300, 160, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    painter.drawPixmap(675, 155, scaled_panel)

    features = [
        ("git st", "一键执行 git status 查询工作区状态"),
        ("git pull", "安全带变基拉取远程最新代码"),
        ("git ci", "带今天动态日期的提交信息模板"),
        ("docker ps", "快速列出本地所有活跃容器"),
        ("TODO 日期", "自动插入带当前日期的标准化待办注释"),
        ("Log 调试", "插入打印语句并将光标自动回退到参数位置"),
    ]
    cur_fy = 280
    for cmd, desc in features:
        painter.setFont(QtGui.QFont("Consolas", 10, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor("#38BDF8"))
        painter.drawText(675, cur_fy, f"[{cmd}]")
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 8))
        painter.setPen(QtGui.QColor("#E2E8F0"))
        painter.drawText(755, cur_fy, desc)
        cur_fy += 26

    painter.end()
    out_file = os.path.join(img_dir, "scene_programmer.png")
    pix.save(out_file, "PNG")
    print(f"Generated Scene Programmer: {out_file}")


def create_scene_customer_service(img_dir: str, panel_pix: QtGui.QPixmap):
    width, height = 1040, 520
    pix = QtGui.QPixmap(width, height)
    pix.fill(QtGui.QColor("#0F172A"))

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    # Header
    painter.setPen(QtGui.QColor("#F8FAFC"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 16, QtGui.QFont.Bold))
    painter.drawText(40, 45, "场景三：电商与客服高效话术回复")

    painter.setPen(QtGui.QColor("#94A3B8"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 11))
    painter.drawText(40, 75, "支持剪贴板无损秒级粘贴（用后自动还原），内置实时时间与工单流水号计数器，接待效率提升数倍")

    # Left: Chat Window Mockup
    chat_rect = QtCore.QRectF(40, 100, 580, 380)
    draw_rounded_card(painter, chat_rect, QtGui.QColor("#F8FAFC"), QtGui.QColor("#CBD5E1"), 8)

    # Header in chat
    painter.fillRect(40, 100, 580, 36, QtGui.QColor("#F1F5F9"))
    painter.setPen(QtGui.QColor("#0F172A"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 10, QtGui.QFont.Bold))
    painter.drawText(55, 123, "💬 客户服务对话 — 在线咨询中 (千牛 / 企微 / 京麦)")

    # Chat Bubbles
    def draw_bubble(y, text, is_user=False):
        bubble_rect = QtCore.QRectF(60 if is_user else 150, y, 360, 46)
        bg = QtGui.QColor("#E2E8F0") if is_user else QtGui.QColor("#0284C7")
        draw_rounded_card(painter, bubble_rect, bg, bg, 8)
        painter.setPen(QtGui.QColor("#0F172A") if is_user else QtGui.QColor("#FFFFFF"))
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9))
        painter.drawText(bubble_rect.adjusted(12, 6, -12, -6), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)

    draw_bubble(155, "买家：您好，请问我的订单发货了吗？什么时候能收到？", is_user=True)
    draw_bubble(215, "客服：您好！正在为您查询物流进度，请稍候片刻…", is_user=False)
    draw_bubble(275, "客服：已为您核实包裹已出库顺丰发出，预计明后天送达！", is_user=False)
    draw_bubble(335, "【接待记录】客服已于 2026-10-13 13:10 接待，工单: CS-10042", is_user=False)

    # Right: Floating Panel + Features
    panel_card = QtCore.QRectF(650, 100, 350, 380)
    draw_rounded_card(painter, panel_card, QtGui.QColor("#1E293B"), QtGui.QColor("#334155"), 10)

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 12, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(675, 135, "客服常用话术面板 (2×3)")

    scaled_panel = panel_pix.scaled(300, 160, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    painter.drawPixmap(675, 155, scaled_panel)

    features = [
        ("标准问候", "热烈欢迎致辞，提升第一响应率"),
        ("查单核实", "安抚客户并告知正在核对系统订单"),
        ("极速退款", "一键给出标准退款与售后指引流程"),
        ("致歉关怀", "真诚致歉并提供补偿优惠券方案"),
        ("礼貌感谢", "温馨感谢咨询并祝客户生活愉快"),
        ("工单记录", "自动注入 {{date}} {{time}} 与 {{counter}} 流水号"),
    ]
    cur_fy = 275
    for tag, desc in features:
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor("#38BDF8"))
        painter.drawText(675, cur_fy, f"• {tag}:")
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 8))
        painter.setPen(QtGui.QColor("#E2E8F0"))
        painter.drawText(750, cur_fy, desc)
        cur_fy += 26

    painter.end()
    out_file = os.path.join(img_dir, "scene_customer_service.png")
    pix.save(out_file, "PNG")
    print(f"Generated Scene Customer Service: {out_file}")


def create_scene_annotation(img_dir: str, panel_pix: QtGui.QPixmap):
    width, height = 1040, 520
    pix = QtGui.QPixmap(width, height)
    pix.fill(QtGui.QColor("#0F172A"))

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    # Header
    painter.setPen(QtGui.QColor("#F8FAFC"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 16, QtGui.QFont.Bold))
    painter.drawText(40, 45, "场景四：图片与工业质检数据高效标注 (Labelme / CVAT)")

    painter.setPen(QtGui.QColor("#94A3B8"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 11))
    painter.drawText(40, 75, "标注目标类别 + 自动确认 + 自动按右方向键切换下一张，实现流水线式每秒一张极速打标")

    # Left: Labeling Tool Mockup
    view_rect = QtCore.QRectF(40, 100, 580, 380)
    draw_rounded_card(painter, view_rect, QtGui.QColor("#18181B"), QtGui.QColor("#27272A"), 8)

    # Draw simulated image with bounding box
    img_box = QtCore.QRectF(60, 120, 540, 330)
    painter.fillRect(img_box, QtGui.QColor("#27272A"))

    # Bounding box defect
    bbox1 = QtCore.QRectF(140, 180, 180, 160)
    painter.setPen(QtGui.QPen(QtGui.QColor("#EF4444"), 2))
    painter.drawRect(bbox1)
    painter.fillRect(140, 155, 110, 24, QtGui.QColor("#EF4444"))
    painter.setPen(QtGui.QColor("#FFFFFF"))
    painter.setFont(QtGui.QFont("Consolas", 9, QtGui.QFont.Bold))
    painter.drawText(148, 172, "defect (0.94)")

    # Bounding box normal
    bbox2 = QtCore.QRectF(360, 220, 160, 130)
    painter.setPen(QtGui.QPen(QtGui.QColor("#10B981"), 2))
    painter.drawRect(bbox2)
    painter.fillRect(360, 195, 110, 24, QtGui.QColor("#10B981"))
    painter.setPen(QtGui.QColor("#FFFFFF"))
    painter.drawText(368, 212, "normal (0.98)")

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9))
    painter.setPen(QtGui.QColor("#A1A1AA"))
    painter.drawText(QtCore.QRectF(60, 420, 540, 20), QtCore.Qt.AlignCenter, "当前进度: [348 / 1200]  |  模式: 自动切换下一张已开启")

    # Right: Floating Panel + Features
    panel_card = QtCore.QRectF(650, 100, 350, 380)
    draw_rounded_card(painter, panel_card, QtGui.QColor("#1E293B"), QtGui.QColor("#334155"), 10)

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 12, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(675, 135, "图片标注快捷面板 (2×4)")

    scaled_panel = panel_pix.scaled(310, 160, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    painter.drawPixmap(675, 155, scaled_panel)

    features = [
        ("缺陷+下张", "输入 'defect' -> 确认 -> 延迟 50ms -> 自动右键下一张"),
        ("正常+下张", "输入 'normal' -> 确认 -> 自动切下一张"),
        ("快捷保存", "直接发送 Ctrl+S，标注结果实时持久化"),
        ("多边形标", "发送 Ctrl+N，即刻激活多边形描点工具"),
        ("矩形标注", "发送 Ctrl+R，快速拉取目标矩形边界框"),
        ("翻页控制", "Left / Right 快速回退检查已打标图片"),
    ]
    cur_fy = 275
    for tag, desc in features:
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor("#38BDF8"))
        painter.drawText(675, cur_fy, f"• {tag}:")
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 8))
        painter.setPen(QtGui.QColor("#E2E8F0"))
        painter.drawText(750, cur_fy, desc)
        cur_fy += 26

    painter.end()
    out_file = os.path.join(img_dir, "scene_annotation.png")
    pix.save(out_file, "PNG")
    print(f"Generated Scene Annotation: {out_file}")


def generate_all():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    img_dir = os.path.join(BASE_DIR, "docs", "images")
    os.makedirs(img_dir, exist_ok=True)

    ctx = AppContext.create_default(base_dir=BASE_DIR)
    ctx.initialize()

    panel = FloatingPanel(
        layout_mgr=ctx.layout_mgr,
        executor=ctx.executor,
        target_mgr=ctx.target_mgr,
        config_store=ctx.config_store,
    )
    panel.show()
    app.processEvents()

    panel_pixmaps = {}
    presets = [
        ("official_doc", "panel_official_doc.png"),
        ("programmer", "panel_programmer.png"),
        ("customer_service", "panel_customer_service.png"),
        ("annotation", "panel_annotation.png"),
    ]

    for lid, fname in presets:
        if lid in ctx.layout_mgr.layouts:
            ctx.layout_mgr.set_active_layout(lid)
            app.processEvents()
            QtCore.QThread.msleep(100)
            app.processEvents()
            pix = panel.grab()
            out_path = os.path.join(img_dir, fname)
            pix.save(out_path, "PNG")
            panel_pixmaps[lid] = pix
            print(f"Saved: {out_path} ({pix.width()}x{pix.height()})")

    # Key Capture Dialog
    k_dlg = KeyCaptureDialog(initial_key="CTRL+SHIFT+C")
    k_dlg.show()
    app.processEvents()
    k_pix = k_dlg.grab()
    k_dlg_path = os.path.join(img_dir, "key_capture_dialog.png")
    k_pix.save(k_dlg_path, "PNG")
    print(f"Saved: {k_dlg_path} ({k_pix.width()}x{k_pix.height()})")
    k_dlg.close()

    # Settings Dialog
    s_dlg = SettingsDialog(
        layout_mgr=ctx.layout_mgr,
        executor=ctx.executor,
        target_mgr=ctx.target_mgr,
        config_store=ctx.config_store,
    )
    s_dlg.show()
    app.processEvents()
    QtCore.QThread.msleep(150)
    app.processEvents()

    s1_pix = s_dlg.grab()
    s1_path = os.path.join(img_dir, "settings_layouts.png")
    s1_pix.save(s1_path, "PNG")
    print(f"Saved: {s1_path} ({s1_pix.width()}x{s1_pix.height()})")

    s_dlg.tabs.setCurrentIndex(1)
    app.processEvents()
    QtCore.QThread.msleep(100)
    app.processEvents()
    s2_pix = s_dlg.grab()
    s2_path = os.path.join(img_dir, "settings_diagnostics.png")
    s2_pix.save(s2_path, "PNG")
    print(f"Saved: {s2_path} ({s2_pix.width()}x{s2_pix.height()})")
    s_dlg.close()

    panel.close()

    # Composite Scenes
    if "official_doc" in panel_pixmaps:
        create_banner(img_dir, panel_pixmaps["official_doc"])
        create_scene_official_doc(img_dir, panel_pixmaps["official_doc"])
    if "programmer" in panel_pixmaps:
        create_scene_programmer(img_dir, panel_pixmaps["programmer"])
    if "customer_service" in panel_pixmaps:
        create_scene_customer_service(img_dir, panel_pixmaps["customer_service"])
    if "annotation" in panel_pixmaps:
        create_scene_annotation(img_dir, panel_pixmaps["annotation"])

    print("\nAll documentation and scenario screenshots successfully generated!")


if __name__ == "__main__":
    generate_all()
