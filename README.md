# 通用快捷输入工作台 (QuickInput)

[English](README_EN.md) | [简体中文](README.md)

[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-0078D6.svg?logo=windows)](https://www.microsoft.com/windows)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt5-41CD52.svg?logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Windows SendInput](https://img.shields.io/badge/engine-Windows%20SendInput%20(Unicode)-F58220.svg)]()
[![Tests](https://img.shields.io/badge/tests-100%20passed-brightgreen.svg)]()
[![Package Size](https://img.shields.io/badge/portable%20zip-24.7%20MB-blueviolet.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<p align="center">
  <img src="docs/images/banner.png" alt="QuickInput Banner" width="100%" />
</p>

**通用快捷输入工作台 (QuickInput)** 是一款专为 Windows 平台打造的高性能、免夺焦轻量级悬浮动作面板。

用户无需编写代码或繁琐的配置文件，即可悬浮于任意目标软件（如 **Word / WPS、终端 / VS Code、客服聊天工具、工业与数据标注软件、浏览器、各类办公系统** 等）上方。通过点击悬浮面板上的快捷按钮，瞬时完成**文本直通注入、单键敲击、复杂快捷键组合、剪贴板无损粘贴模板、多步骤宏流程执行**，并在多个专业场景间一键自由切换键盘矩阵。

---

## 🌟 核心特性与设计哲学

1. **绝对不抢输入焦点 (Zero Focus Stealing) 与 Windows 原生窗口**：
   - 底层采用 Windows 原生扩展窗口样式 `WS_EX_NOACTIVATE` 与鼠标命中测试 `MA_NOACTIVATE` 架构。
   - 彻底解决普通悬浮窗点击导致第三方应用失去输入光标的难题。点击面板按钮时，**目标软件光标始终原地闪烁，物理键盘随时敲击毫无冲突**。
   - 保留 Windows 原生标题栏与边缘拖拽缩放能力，点击原生关闭 `×` 自动收起至系统托盘，杜绝后台僵尸进程。
2. **Win32 `SendInput` Unicode 直通注入技术**：
   - 全面采用 Windows 标准 `SendInput` API，注入文本使用 `KEYEVENTF_UNICODE` 标志。
   - **完全绕过中文拼音输入法的候选词框拦截**，杜绝弹窗吞字、打字串位或字符截断。
3. **严格遵循国家标准的预设场景（开箱即用）**：
   - 独家内置按照 **《党政机关公文格式》国家标准 (GB/T 9704-2012)** 规范打造的公文排版场景。
   - 内置**程序员常用命令、电商客服高频话术、图片质检标注**等场景包，即开即用。
4. **可视化布局设计中心与无冲突按键录制**：
   - 直观的网格可视化预览，支持**自由设定行列尺寸、一键行列转置 (Transpose)、空槽微调与按钮属性实时编辑**。
   - 提供专用按键录制器，直接按下物理按键或组合键即可精准捕获；敲击 `Enter` 时智能录制为回车键本身，防止误关闭确认。
5. **动态模板变量与安全剪贴板**：
   - 支持动态插入 `{{date}}` (当前日期)、`{{time}}` (当前时间)、`{{counter}}` (流水号计数器)、`{{clipboard}}` (剪贴板内容)、`{{app_name}}` (前台应用名称)。
   - 粘贴长文本后**自动无损还原用户的原始剪贴板**，不破坏日常复制粘贴习惯。
6. **无缝中英双语国际化 (i18n)**：
   - 内置简体中文与英文语言包，设置中随时切换，**整个工作台、预设布局名称、右键托盘、设置中心与诊断工具实时全量刷新**。
7. **极简超轻量，免安装绿色便携**：
   - 采用纯净精简依赖打包，去除冗余大动态库，解压后体积仅 **61.9 MB**，压缩 ZIP 便携包仅 **24.7 MB**。

---

## 🎬 核心实际应用场景展示

### 场景一：党政机关公文标准排版 (GB/T 9704-2012)

在 Word / WPS 中起草或排版红头文件、通告、报告等公文时，格式规范要求极其严苛（页边距精确到毫米、字体字号严格对应、行数网格对应磅值等）。以往需在繁杂菜单中反复查找修改，现在通过悬浮面板**一键标准化完成**。

<p align="center">
  <img src="docs/images/scene_official_doc.png" alt="公文标准排版实际应用场景" width="100%" />
</p>

| 按钮 | 国家标准条款 | 规范要求 | 自动化动作说明 |
| :--- | :--- | :--- | :--- |
| **【边距】** | 条款 5.2.2 | **天头 37mm、地脚 35mm、订口 28mm、切口 26mm** | 自动调出页面设置，精准填入公文标准四方毫米边距并确认 |
| **【正文】** | 条款 7.3.3 | **仿宋_GB2312 + Times New Roman 三号**，两端对齐 | 调出字体对话框，同时设定中西文字体字号，并触发 `Ctrl+J` 两端对齐 |
| **【行距】** | 条款 5.2.3 | **每页 22 行，每行 28 个汉字**（版心固定值） | 自动进入段落设置，设定行距为**固定值 28.9 磅**（精准契合22行版心） |
| **【缩进】** | 条款 7.3.3 | **首行空 2 字符**（正文自然段规范） | 自动配置段落首行缩进 2 字符 |
| **【六角】** | 条款 7.2.5 | 发文字号年份必须使用六角括号**“〔 〕”**（非中括号） | 自动键入 `〔 〕` 并**将光标精确定位在括号正中央**，直接键入年份即可 |
| **【大标】** | 条款 7.3.1 | **方正小标宋简体 二号**，居中对齐，不加粗 | 设置小标宋二号字，并触发 `Ctrl+E` 居中对齐 |
| **【标1】** | 条款 7.3.2 | 一级标题：序号用“一、”，**黑体 三号** | 自动设置黑体三号字，两端对齐 |
| **【标2】** | 条款 7.3.2 | 二级标题：序号用“（一）”，**楷体 三号** | 自动设置楷体_GB2312 三号字，两端对齐 |
| **【标3】** | 条款 7.3.2 | 三级标题：序号用“1.”，**仿宋加粗 三号** | 自动设置仿宋三号字并加粗 (`Ctrl+B`) |
| **【页码】** | 条款 7.5 | 4号宋体阿拉伯数字，左右各放一字线 | 一键插入公文标准单双页码格式：`— 1 —` |

---

### 场景二：程序员控制台与 DevOps 运维自动化

在日常开发与服务器运维过程中，开发者需要在 VS Code、Windows Terminal、Git Bash 等窗口频繁键入重复指令。QuickInput 悬浮于终端边缘，支持一键发送复杂命令或动态参数代码模板。

<p align="center">
  <img src="docs/images/scene_programmer.png" alt="程序员与DevOps终端自动化场景" width="100%" />
</p>

- **`git st`**：发送 `git status` 并自动执行，秒看本地工作区改动。
- **`git pull`**：发送带变基的安全同步指令 `git pull --rebase`。
- **`git ci`**：自动带入当前系统实时日期的提交模板：`git commit -m "fix: update {{date}}"`。
- **`docker ps`**：快速查询本地所有容器状态：`docker ps -a`。
- **`TODO 日期`**：自动向当前光标处输入标准化代办注释：`// TODO({{date}}): `。
- **`Log 调试`**：输入 `console.log("[DEBUG]", );` 并**自动将光标回退 2 格**至逗号右侧，便于直接敲入变量名。

---

### 场景三：电商与售后客服高效话术回复

在千牛、京东麦麦、微信客服、企业微信等聊天窗口接待买家咨询时，QuickInput 提供秒级一键回复，避免频繁打开文本文件查找或手动打字。

<p align="center">
  <img src="docs/images/scene_customer_service.png" alt="电商与售后客服高效话术回复场景" width="100%" />
</p>

- **标准服务问候**：一键发送热情规范欢迎语，大幅提升店铺客服第一响应速度。
- **物流查单引导**：告知买家已进入系统核验流程，安抚等待情绪。
- **无损剪贴板极速粘贴**：采用剪贴板高速粘贴长文本，并在粘贴后**自动恢复用户原有的剪贴板内容**。
- **带工单流水号的接待备忘**：点击直接注入包含系统时间与递增计数的工单记录：
  > `【接待记录】客服已于 {{date}} {{time}} 接待咨询，工单编号: CS-{{counter}}。`

---

### 场景四：图片与工业质检数据标注 (Labelme / CVAT)

在深度学习数据集清洗、目标检测标注（Labelme、LabelImg、CVAT 等）或流水线缺陷分类质检中，传统标注流程需要“画框 -> 弹窗打字输类别 -> 敲回车 -> 点下一张”，繁琐耗时。

<p align="center">
  <img src="docs/images/scene_annotation.png" alt="图片与工业质检标注场景" width="100%" />
</p>

- **【缺陷+下张】**：自动输入标签 `defect` -> 确认 Enter -> 等待 50ms -> 自动发送 `Right` 方向键切换到下一张图片，实现**流水线式一秒一张打标**。
- **【正常+下张】**：自动输入 `normal` -> 确认 Enter -> 发送 `Right` 键切换。
- **绘图工具无缝切换**：一键触发矩形框标注 (`Ctrl+R`)、多边形描点标注 (`Ctrl+N`)、快速保存文件 (`Ctrl+S`)。

---

## 🛠️ 设置中心与可视化宏设计器

点击悬浮面板上的齿轮图标，即可呼出功能强大的设置中心：

<p align="center">
  <img src="docs/images/settings_layouts.png" alt="设置中心 - 布局与按钮设计器" width="49%" />
  <img src="docs/images/settings_diagnostics.png" alt="设置中心 - 常规与诊断工具" width="49%" />
</p>

### 1. 布局与按钮设计中心
- **所见即所得的预览网格**：点击任意槽位即时选中，支持调换位置、清空槽位、上下左右方向微调。
- **行列转置 (Transpose)**：点击一键行列互换（如 2×4 转置为 4×2），行列数与按钮位置自适应调整。
- **多步骤动作链组合**：支持在一个按钮中自由编排**“输入文本”**、**“按键敲击”**、**“组合快捷键”**、**“等待延迟”**。
- **优雅的按键录制窗口**：
  <p align="center">
    <img src="docs/images/key_capture_dialog.png" alt="按键录制窗口" width="380px" />
  </p>
  点击“＋ 按键”后，按下任意单键（如 `F5`、`Enter`、`Tab`）或组合键（如 `Ctrl+Alt+S`）即可录制。按下 `Enter` 键时识别为按键本身，杜绝意外提交！

### 2. 目标感知、应用绑定与诊断
- **窗口智能感知与跟随**：实时显示当前活动前台窗口标题、进程名、PID 与句柄。
- **场景自动绑定 (Profiles)**：可将特定布局绑定至特定进程（例如检测到 `labelme.exe` 时自动切换到标注布局，切换到 Word 时自动切换到公文布局）。
- **目标锁定模式**：点击托盘或主面板锁按钮，可固定向指定程序注入按键，即使中途点击了其他窗口也能精准回送输入。
- **实时执行诊断日志**：完整记录每一步宏的触发时间、成功状态与执行说明。

---

## ⌨️ 全局默认快捷键

| 快捷键 | 功能说明 | 特性机制 |
| :--- | :--- | :--- |
| **`Alt + Q`** | 全局显示 / 隐藏工作台 | 基于 Qt 跨线程信号桥接（QueuedConnection），绝不卡顿或假死 |
| **`Esc`** | 紧急停止当前正在执行的宏 | 任何多步骤长宏在执行过程中均可单键强行熔断中断 |

---

## 🚀 启动与使用方式

### 方式 1：免安装绿色便携版（推荐，开箱即用）
1. 从 Release 下载或进入本地目录：
   👉 [`dist/QuickInput/QuickInput.exe`](dist/QuickInput/QuickInput.exe)
2. 双击直接运行，无需安装任何环境，不向系统注册表写入任何垃圾项。
3. （若需调试排查，可双击 `QuickInput_Debug.bat` 在日志控制台下启动）。

### 方式 2：Python 源代码运行
```bash
# 1. 克隆代码仓库
git clone https://github.com/Gavin-Liuu/QuickInput.git
cd QuickInput

# 2. 安装必要运行依赖
pip install -r requirements.txt

# 3. 启动主程序
python main.py
```

### 方式 3：一键重新打包为绿色便携版
本工程内置自动化优化打包脚本，自动过滤未使用的动态库并精简包体体积：
```bash
python build_portable.py
```
打包完成后将在 `dist/` 目录下生成：
- 解压即用文件夹：`dist/QuickInput/` (约 61.9 MB)
- 便携发布压缩包：`dist/QuickInput_v2.0.0_Windows_x64.zip` (约 24.7 MB)

---

## 🏗️ 软件架构设计

软件严格遵循**清晰分层架构**，业务核心不侵入特定 GUI 框架或操作系统底层：

```text
FloatPoint/
├── domain/                  # 纯领域模型 (Action, ActionStep, Button, Layout, Profile, i18n 语言系统)
├── application/             # 业务服务层 (ActionExecutor, TargetManager, MacroRecorder, LayoutManager, AppContext)
├── platform_layer/          # 操作系统适配抽象层
│   ├── base.py              # 跨平台接口基类
│   └── windows/             # Win32 SendInput 引擎、窗体句柄追踪、无损剪贴板、全局热键
├── storage/                 # 配置持久化与场景包存储 (.qipack / JSON)
│   ├── config_store.py      # 原子保存、Schema 版本迁移与损坏自愈备份
│   └── pack_store.py        # 场景包导入导出、安全路径拦截与校验
├── ui/                      # PyQt5 悬浮界面与可视化设计工作室
│   ├── floating_panel.py    # 零夺焦悬浮主工作台
│   ├── settings_dialog.py   # 布局与按钮设置中心、诊断与应用绑定面板
│   ├── key_capture_dialog.py# 可视化按键录制弹窗
│   ├── new_layout_dialog.py # 新建布局向导
│   └── tray_icon.py         # 系统托盘图标与右键菜单
├── packs/                   # 内置 4 套开箱即用标准场景包
│   ├── official_doc/        # 党政机关公文格式 (GB/T 9704-2012)
│   ├── programmer/          # 程序员常用命令与终端控制
│   ├── customer_service/    # 电商与售后客服话术
│   └── annotation/          # 图片质检与数据标注
├── docs/images/             # 说明文档高清场景展示图与界面截图
├── tests/                   # 100 项全覆盖单元测试与回归测试
└── build_portable.py        # 纯净便携分发打包脚本
```

---

## 🧪 自动化测试验证

本工程维护了覆盖率极高的自动化测试套件（含无头 Qt UI 测试、宏引擎测试、跨平台注入 Mock 测试等）：

```bash
python -m pytest tests/
```

测试范围包含：
- ✅ 100 项测试用例全部通过（100% Passed）。
- ✅ GB/T 9704-2012 公文页边距、中西文字体、22行行距、六角括号等参数回归校验。
- ✅ `Alt + Q` 快捷键跨线程安全触发与无阻塞显示隐藏。
- ✅ 录制按键时 `Enter` 键防误触与独立捕获测试。
- ✅ 中英双语动态切换无残缺测试。
- ✅ 剪贴板注入恢复、宏超时熔断与最大步数保护。

---

## 📄 开源许可证

本项目采用 [MIT 许可证](LICENSE) 开源。欢迎提交 Issue 或 Pull Request 贡献新场景包！
