# -*- coding: utf-8 -*-
"""Generate high-resolution screenshots and pixel-perfect scenario demonstration graphics for README."""

import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from application.context import AppContext
from ui.floating_panel import FloatingPanel
from ui.settings_dialog import SettingsDialog
from ui.key_capture_dialog import KeyCaptureDialog


def draw_window_frame(painter: QtGui.QPainter, rect: QtCore.QRectF, title: str, title_bg: QtGui.QColor, is_dark: bool = False):
    """Draw a clean native-style application window frame with titlebar."""
    painter.save()
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

    # Window shadow
    shadow_rect = rect.adjusted(-5, -5, 5, 5)
    shadow_path = QtGui.QPainterPath()
    shadow_path.addRoundedRect(shadow_rect, 10, 10)
    painter.fillPath(shadow_path, QtGui.QColor(0, 0, 0, 80))

    # Window body
    path = QtGui.QPainterPath()
    path.addRoundedRect(rect, 8, 8)
    bg_col = QtGui.QColor("#18181B") if is_dark else QtGui.QColor("#F8FAFC")
    border_col = QtGui.QColor("#27272A") if is_dark else QtGui.QColor("#CBD5E1")
    painter.fillPath(path, QtGui.QBrush(bg_col))
    painter.setPen(QtGui.QPen(border_col, 1))
    painter.drawPath(path)

    # Title bar
    title_rect = QtCore.QRectF(rect.x(), rect.y(), rect.width(), 32)
    t_path = QtGui.QPainterPath()
    t_path.addRoundedRect(rect, 8, 8)
    painter.save()
    painter.setClipRect(title_rect)
    painter.fillPath(t_path, QtGui.QBrush(title_bg))
    painter.restore()

    # Window controls (min, max, close)
    for i, c in enumerate(["#94A3B8", "#94A3B8", "#EF4444"]):
        painter.setBrush(QtGui.QBrush(QtGui.QColor(c)))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(int(rect.x() + 16 + i * 16), int(rect.y() + 11), 8, 8)

    # Title text
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#FFFFFF"))
    painter.drawText(QtCore.QRectF(rect.x(), rect.y(), rect.width(), 32), QtCore.Qt.AlignCenter, title)

    painter.restore()


def draw_panel_with_shadow(painter: QtGui.QPainter, x: int, y: int, panel_pix: QtGui.QPixmap):
    """Draw the actual QuickInput panel with a realistic drop shadow and accent border."""
    painter.save()
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

    shadow_rect = QtCore.QRectF(x - 6, y - 6, panel_pix.width() + 12, panel_pix.height() + 12)
    s_path = QtGui.QPainterPath()
    s_path.addRoundedRect(shadow_rect, 10, 10)
    painter.fillPath(s_path, QtGui.QColor(0, 0, 0, 130))

    g_path = QtGui.QPainterPath()
    g_path.addRoundedRect(QtCore.QRectF(x - 1, y - 1, panel_pix.width() + 2, panel_pix.height() + 2), 6, 6)
    painter.setPen(QtGui.QPen(QtGui.QColor("#0A84FF"), 2))
    painter.drawPath(g_path)

    painter.drawPixmap(x, y, panel_pix)
    painter.restore()


def draw_feature_card(painter: QtGui.QPainter, rect: QtCore.QRectF, title: str, items: list):
    """Draw a feature summary card with clean badge layout and zero text overflow."""
    painter.save()
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    path = QtGui.QPainterPath()
    path.addRoundedRect(rect, 8, 8)
    painter.fillPath(path, QtGui.QColor("#1E293B"))
    painter.setPen(QtGui.QPen(QtGui.QColor("#334155"), 1.2))
    painter.drawPath(path)

    # Header title
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 10, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(int(rect.x() + 16), int(rect.y() + 26), title)

    cur_y = int(rect.y() + 52)
    tag_font = QtGui.QFont("Microsoft YaHei UI", 8, QtGui.QFont.Bold)
    desc_font = QtGui.QFont("Microsoft YaHei UI", 8)
    fm_tag = QtGui.QFontMetrics(tag_font)

    for tag, desc in items:
        # Badge for tag
        tw = fm_tag.horizontalAdvance(tag)
        badge_w = tw + 12
        badge_rect = QtCore.QRectF(rect.x() + 14, cur_y - 14, badge_w, 20)
        b_path = QtGui.QPainterPath()
        b_path.addRoundedRect(badge_rect, 4, 4)
        painter.fillPath(b_path, QtGui.QColor("#334155"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#475569"), 1))
        painter.drawPath(b_path)

        painter.setFont(tag_font)
        painter.setPen(QtGui.QColor("#FBBF24"))
        painter.drawText(badge_rect, QtCore.Qt.AlignCenter, tag)

        # Description text
        painter.setFont(desc_font)
        painter.setPen(QtGui.QColor("#E2E8F0"))
        desc_x = badge_rect.right() + 10
        desc_rect = QtCore.QRectF(desc_x, cur_y - 14, rect.right() - 12 - desc_x, 20)
        painter.drawText(desc_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, desc)
        cur_y += 26

    painter.restore()


def create_banner(img_dir: str, panel_pix: QtGui.QPixmap):
    W, H = 1140, 320
    pix = QtGui.QPixmap(W, H)

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    # Background gradient
    grad = QtGui.QLinearGradient(0, 0, W, H)
    grad.setColorAt(0.0, QtGui.QColor("#0B0F17"))
    grad.setColorAt(0.6, QtGui.QColor("#111827"))
    grad.setColorAt(1.0, QtGui.QColor("#0B0F17"))
    painter.fillRect(0, 0, W, H, grad)

    # Left content
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))
    painter.drawText(50, 56, "WINDOWS 免夺焦轻量级悬浮工作台 · QUICKINPUT")

    painter.setPen(QtGui.QColor("#F8FAFC"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 24, QtGui.QFont.Bold))
    painter.drawText(50, 104, "通用快捷输入工作台")

    painter.setPen(QtGui.QColor("#94A3B8"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 11))
    painter.drawText(50, 142, "零夺焦原生输入 · 矩阵布局自由定制 · 宏动作与中英双语")
    painter.drawText(50, 168, "公文国标排版 (GB/T 9704-2012) · 程序员控制台 · 客服与数据标注")

    # Feature pills with dynamic text measurement
    pills = [
        ("零夺焦输入 (SendInput API)", "#10B981"),
        ("中英双语实时切换", "#6366F1"),
        ("绿色便携 (ZIP 仅 24.7MB)", "#EC4899"),
    ]
    cur_x = 50
    pill_font = QtGui.QFont("Microsoft YaHei UI", 8, QtGui.QFont.Bold)
    painter.setFont(pill_font)
    fm = painter.fontMetrics()
    for text, col in pills:
        tw = fm.horizontalAdvance(text)
        pill_w = tw + 24
        pill_rect = QtCore.QRectF(cur_x, 212, pill_w, 32)
        p_path = QtGui.QPainterPath()
        p_path.addRoundedRect(pill_rect, 6, 6)
        painter.fillPath(p_path, QtGui.QColor(30, 41, 59, 220))
        painter.setPen(QtGui.QPen(QtGui.QColor(col), 1.2))
        painter.drawPath(p_path)

        painter.setPen(QtGui.QColor("#F1F5F9"))
        painter.drawText(pill_rect, QtCore.Qt.AlignCenter, text)
        cur_x += pill_w + 14

    # Right: Floating panel
    panel_x = 780
    panel_y = 65
    draw_panel_with_shadow(painter, panel_x, panel_y, panel_pix)

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(QtCore.QRectF(panel_x - 30, panel_y + panel_pix.height() + 15, panel_pix.width() + 60, 22), QtCore.Qt.AlignCenter, "✦ 悬浮于任意应用之上 · 即点即输")

    painter.end()
    out = os.path.join(img_dir, "banner.png")
    pix.save(out, "PNG")
    print(f"Generated Banner: {out}")


def create_scene_official_doc(img_dir: str, panel_pix: QtGui.QPixmap):
    W, H = 1140, 580
    pix = QtGui.QPixmap(W, H)

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    painter.fillRect(0, 0, W, H, QtGui.QColor("#0F172A"))

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 13, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(30, 36, "办公排版应用场景 · 结合 Microsoft Word / WPS (GB/T 9704-2012 国家公文标准)")

    # Left: Word Window (width 690)
    word_rect = QtCore.QRectF(30, 55, 690, 490)
    draw_window_frame(painter, word_rect, "国务院关于推进公文标准化排版的决定.docx - Word", QtGui.QColor("#2B579A"), is_dark=False)

    # Word Ribbon
    painter.fillRect(int(word_rect.x()), int(word_rect.y() + 32), int(word_rect.width()), 32, QtGui.QColor("#F1F5F9"))
    painter.setPen(QtGui.QColor("#64748B"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 8))
    painter.drawText(45, 107, "文件   开始   插入   绘图   设计   [ 页面布局 (P) ]   引用   邮件   审阅   视图")

    # A4 Paper
    paper = QtCore.QRectF(75, 132, 600, 395)
    p_path = QtGui.QPainterPath()
    p_path.addRect(paper)
    painter.fillPath(p_path, QtGui.QColor("#FFFFFF"))
    painter.setPen(QtGui.QPen(QtGui.QColor("#E2E8F0"), 1))
    painter.drawPath(p_path)

    # Official Doc Header & Body
    painter.setPen(QtGui.QColor("#1E293B"))
    painter.setFont(QtGui.QFont("FangSong", 10))
    painter.drawText(QtCore.QRectF(75, 146, 600, 20), QtCore.Qt.AlignCenter, "国发〔2026〕1号")

    painter.setPen(QtGui.QPen(QtGui.QColor("#DC2626"), 2))
    painter.drawLine(105, 172, 645, 172)

    painter.setPen(QtGui.QColor("#0F172A"))
    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 12, QtGui.QFont.Bold))
    painter.drawText(QtCore.QRectF(75, 192, 600, 26), QtCore.Qt.AlignCenter, "国务院关于推进标准化公文格式排版的决定")

    painter.setFont(QtGui.QFont("SimHei", 10, QtGui.QFont.Bold))
    painter.drawText(110, 240, "一、总体要求与标准遵循")

    painter.setFont(QtGui.QFont("FangSong", 9))
    painter.drawText(110, 266, "    各地区各部门在起草公文时，必须严格执行国家标准 GB/T 9704-2012")
    painter.drawText(110, 288, "《党政机关公文格式》。公文用纸采用 A4 型（210mm × 297mm）。")
    painter.drawText(110, 310, "版面页边距设置为：天头 37mm、地脚 35mm、订口 28mm、切口 26mm。")

    painter.setFont(QtGui.QFont("KaiTi", 10, QtGui.QFont.Bold))
    painter.drawText(110, 344, "    （一）严格规范中西文字体与行数网格")

    painter.setFont(QtGui.QFont("FangSong", 9, QtGui.QFont.Bold))
    painter.drawText(110, 370, "    1. 正文三号仿宋配 Times New Roman，每面固定 22 行。")
    painter.setFont(QtGui.QFont("FangSong", 9))
    painter.drawText(110, 392, "    （排版固定行距 28.9 磅，严格执行标准公文版心网格）。")

    painter.setFont(QtGui.QFont("SimSun", 9))
    painter.drawText(QtCore.QRectF(75, 498, 600, 18), QtCore.Qt.AlignCenter, "— 1 —")

    # Right: Floating Panel
    panel_x = 790
    draw_panel_with_shadow(painter, panel_x, 65, panel_pix)

    # Right: Feature card
    items = [
        ("边距", "天头37 地脚35 订口28 切口26 mm"),
        ("正文", "仿宋_GB2312 三号 + TNR 英文字体"),
        ("行距", "固定值 28.9 磅 (对应22行/面)"),
        ("缩进", "段落首行缩进 2 字符"),
        ("六角", "发文字号六角括号〔 〕光标居中"),
        ("大标", "二号 方正小标宋简体 居中对齐"),
        ("标1/2/3", "一黑二楷三仿宋加粗 快速设标题"),
        ("页码", "标准一字线页码模板：— 1 —"),
    ]
    draw_feature_card(painter, QtCore.QRectF(750, 250, 360, 275), "公文常用格式 (一键对应国标)", items)

    painter.end()
    out = os.path.join(img_dir, "scene_official_doc.png")
    pix.save(out, "PNG")
    print(f"Generated Scene Official Doc: {out}")


def create_scene_programmer(img_dir: str, panel_pix: QtGui.QPixmap):
    W, H = 1140, 580
    pix = QtGui.QPixmap(W, H)

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    painter.fillRect(0, 0, W, H, QtGui.QColor("#0F172A"))

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 13, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(30, 36, "程序员终端与 DevOps 场景 · 结合 VS Code / Terminal / Git Bash")

    # Left: Terminal Window (width 690)
    term_rect = QtCore.QRectF(30, 55, 690, 490)
    draw_window_frame(painter, term_rect, "bash — QuickInput Terminal Automation", QtGui.QColor("#18181B"), is_dark=True)

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
        ("9a82cd1102ba   redis:latest   \"docker-…\"   Up 5 hours", "#7EE787"),
        ("", "#000000"),
        ("$ // TODO(2026-10-13): optimize cache layer", "#D29922"),
        ("$ console.log(\"[DEBUG]\", data);", "#BC8CFF"),
    ]
    cur_y = 120
    for text, col in lines:
        if text:
            painter.setPen(QtGui.QColor(col))
            painter.drawText(50, cur_y, text)
        cur_y += 24

    # Right: Floating Panel (centered in right column)
    panel_x = 820
    draw_panel_with_shadow(painter, panel_x, 75, panel_pix)

    items = [
        ("git st", "一键执行 git status 查询工作区"),
        ("git pull", "安全带变基拉取远程最新代码"),
        ("git ci", "带当前动态日期的提交信息模板"),
        ("docker", "快速列出本地所有活跃容器列表"),
        ("TODO", "自动插入带当前日期的标准化待办"),
        ("Log 调试", "插入打印语句并将光标回退到参数"),
    ]
    draw_feature_card(painter, QtCore.QRectF(750, 250, 360, 225), "程序员常用命令 (高频指令免打字)", items)

    painter.end()
    out = os.path.join(img_dir, "scene_programmer.png")
    pix.save(out, "PNG")
    print(f"Generated Scene Programmer: {out}")


def create_scene_customer_service(img_dir: str, panel_pix: QtGui.QPixmap):
    W, H = 1140, 580
    pix = QtGui.QPixmap(W, H)

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    painter.fillRect(0, 0, W, H, QtGui.QColor("#0F172A"))

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 13, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(30, 36, "电商客服话术应用场景 · 结合千牛 / 京麦 / 企业微信客服")

    # Left: Chat Window (width 690)
    chat_rect = QtCore.QRectF(30, 55, 690, 490)
    draw_window_frame(painter, chat_rect, "买家服务在线接待 — 千牛 / 企微", QtGui.QColor("#0284C7"), is_dark=False)

    def draw_bubble(y, text, is_user=False):
        b_x = 55 if is_user else 170
        b_w = 420 if is_user else 510
        b_rect = QtCore.QRectF(b_x, y, b_w, 44)
        bg = QtGui.QColor("#E2E8F0") if is_user else QtGui.QColor("#0284C7")
        p = QtGui.QPainterPath()
        p.addRoundedRect(b_rect, 8, 8)
        painter.fillPath(p, bg)
        painter.setPen(QtGui.QColor("#0F172A") if is_user else QtGui.QColor("#FFFFFF"))
        painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9))
        painter.drawText(b_rect.adjusted(14, 4, -14, -4), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)

    draw_bubble(120, "买家：您好，请问我昨天下单的商品什么时候发货？", is_user=True)
    draw_bubble(180, "客服：您好！正在为您查询物流进度，请稍候片刻…", is_user=False)
    draw_bubble(240, "客服：已为您核实包裹已由顺丰发出，预计明天送达！", is_user=False)
    draw_bubble(300, "【接待记录】客服已接待完毕，工单登记号: CS-10042", is_user=False)

    # Right: Floating Panel (centered in right column)
    panel_x = 820
    draw_panel_with_shadow(painter, panel_x, 75, panel_pix)

    items = [
        ("标准问候", "规范热情欢迎致辞，提升响应率"),
        ("查单核实", "安抚客户并告知正在核对系统订单"),
        ("极速退款", "一键给出标准退款与售后指引流程"),
        ("致歉关怀", "真诚致歉并提供补偿优惠券方案"),
        ("礼貌感谢", "温馨感谢咨询并祝客户生活愉快"),
        ("工单记录", "自动注入日期时间与工单流水号"),
    ]
    draw_feature_card(painter, QtCore.QRectF(750, 250, 360, 225), "客服常用话术 (秒级回复与流水号)", items)

    painter.end()
    out = os.path.join(img_dir, "scene_customer_service.png")
    pix.save(out, "PNG")
    print(f"Generated Scene Customer Service: {out}")


def create_scene_annotation(img_dir: str, panel_pix: QtGui.QPixmap):
    W, H = 1140, 580
    pix = QtGui.QPixmap(W, H)

    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

    painter.fillRect(0, 0, W, H, QtGui.QColor("#0F172A"))

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 13, QtGui.QFont.Bold))
    painter.setPen(QtGui.QColor("#38BDF8"))
    painter.drawText(30, 36, "数据标注应用场景 · 结合 Labelme / CVAT / 工业质检平台")

    # Left: Annotation Tool Window (width 690)
    view_rect = QtCore.QRectF(30, 55, 690, 490)
    draw_window_frame(painter, view_rect, "Labelme v5.2 - [348 / 1200] inspection_0348.jpg", QtGui.QColor("#18181B"), is_dark=True)

    # Canvas area
    img_area = QtCore.QRectF(50, 100, 650, 390)
    painter.fillRect(img_area, QtGui.QColor("#27272A"))

    # Bounding Box Defect
    b1 = QtCore.QRectF(130, 160, 200, 170)
    painter.setPen(QtGui.QPen(QtGui.QColor("#EF4444"), 2))
    painter.drawRect(b1)
    painter.fillRect(130, 134, 110, 26, QtGui.QColor("#EF4444"))
    painter.setPen(QtGui.QColor("#FFFFFF"))
    painter.setFont(QtGui.QFont("Consolas", 9, QtGui.QFont.Bold))
    painter.drawText(138, 152, "defect (0.94)")

    # Bounding Box Normal
    b2 = QtCore.QRectF(390, 210, 180, 150)
    painter.setPen(QtGui.QPen(QtGui.QColor("#10B981"), 2))
    painter.drawRect(b2)
    painter.fillRect(390, 184, 110, 26, QtGui.QColor("#10B981"))
    painter.setPen(QtGui.QColor("#FFFFFF"))
    painter.drawText(398, 202, "normal (0.98)")

    painter.setFont(QtGui.QFont("Microsoft YaHei UI", 9))
    painter.setPen(QtGui.QColor("#A1A1AA"))
    painter.drawText(QtCore.QRectF(50, 445, 650, 22), QtCore.Qt.AlignCenter, "当前模式: 快捷标签输入 -> 确认Enter -> 自动按Right切换下一张")

    # Right: Floating Panel (centered in right column)
    panel_x = 816
    draw_panel_with_shadow(painter, panel_x, 75, panel_pix)

    items = [
        ("缺陷下张", "打标 defect 并按回车自动切图"),
        ("正常下张", "打标 normal 并按回车自动切图"),
        ("快捷保存", "发送 Ctrl+S 实时持久化标注结果"),
        ("多边形", "发送 Ctrl+N 激活多边形描点工具"),
        ("矩形标注", "发送 Ctrl+R 拉取目标矩形边界框"),
        ("翻页控制", "Left / Right 快速回退检查已标图"),
    ]
    draw_feature_card(painter, QtCore.QRectF(750, 250, 360, 225), "图片标注常用动作 (流水线极速打标)", items)

    painter.end()
    out = os.path.join(img_dir, "scene_annotation.png")
    pix.save(out, "PNG")
    print(f"Generated Scene Annotation: {out}")


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

    print("\nAll clean documentation and scenario screenshots successfully generated!")


if __name__ == "__main__":
    generate_all()
