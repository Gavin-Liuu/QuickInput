#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中国象棋标注/录入 专用迷你悬浮虚拟键盘 & 通用快捷输入工作台
======================================================
该入口与全新产品化架构 (domain, application, platform, storage, ui) 完全打通，
默认启动中国象棋 14 子专属标注布局，同时无缝支持横竖排切换、多场景布局切换、
宏录制与免夺焦 SendInput 极速字符注入。
"""

import sys
import os

# Ensure current directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from main import main

if __name__ == "__main__":
    main()
