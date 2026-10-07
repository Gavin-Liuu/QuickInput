# 通用快捷输入工作台 (QuickInput)

[English](README_EN.md) | [简体中文](README.md)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt5-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Windows SendInput](https://img.shields.io/badge/platform-Windows_SendInput-orange.svg)]()
[![Tests](https://img.shields.io/badge/tests-91%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**通用快捷输入工作台 (QuickInput)** 是一款专为 Windows 平台打造的高效、轻量级免夺焦悬浮动作面板。用户无需编辑代码或 JSON，即可在任何第三方目标软件（如 Labelme 标注工具、记事本、Word、Excel、浏览器、VS Code、各类工作/聊天软件等）中，通过悬浮按钮快速注入文本、敲击单键、执行组合键、粘贴富文本模板、运行复杂宏动作，并在不同场景间一键秒级切换键盘布局。

软件提供直观的布局设计中心与安全可视化的宏录制器，开箱内置多套常用场景包（图片标注、客服话术、程序员指令、记谱符号等），支持高度自定义与随时扩展。

---

## 🌟 核心特性

1. **绝对不抢输入焦点 (Zero Focus Stealing) 与 Windows 原生窗口机制**：
   - 采用 Windows 原生 `WS_EX_NOACTIVATE` 与 `MA_NOACTIVATE` 架构，无边框伪标题栏全部升级为 Windows 原生标题栏与原生边缘缩放。
   - 点击面板按钮时，光标始终在目标软件的输入框中闪烁，**物理键盘可随时敲击，绝不冲突**。
   - 原生关闭 `×` 默认隐藏到系统托盘，彻底退出通过系统托盘右键“退出程序”，清理全部全局热键与钩子线程，绝不残留后台进程。
2. **现代 Windows `SendInput` Unicode 直通注入**：
   - 彻底摒弃旧版 `keybd_event`，全面采用 Win32 `SendInput`。
   - 注入字符直接使用 `KEYEVENTF_UNICODE` 标志，**完全绕过中文拼音输入法候选框**，杜绝弹窗或吞字。
3. **极简主面板结构**：
   - 左上角首个控件为**搜索按钮**，点击即可展开搜索框并直接输入中文/英文检索按钮；关闭搜索后自动恢复零夺焦状态。
   - 底部左侧提供**透明度实时调节滑块**，调整后立即生效并保存至当前布局。
   - 底部无冗余“执行完成”持久化文字，仅在宏运行期间临时出现停止按钮。
4. **统一“布局与按钮”设置中心**：
   - 合并原分散标签页，提供直观的**布局预览网格**与**上下文属性编辑**，用户完全无需关心任何内部 ID。
   - 新建布局向导可一键生成指定行列的预设按钮网格；支持空槽位点击添加与按钮顺序调整。
   - “动作结束后发送 Enter”与“执行前确认”升级为布局级统一开关。
5. **安全可靠的可视化宏按键录制器**：
   - 严格限定录制目标，自动过滤非目标窗口击键与 QuickInput 自身窗口操作，切换离开目标时给出警告。
   - 基于 `ToUnicodeEx` 与系统当前键盘布局精准解析按键字符，标准化组合键排序 (`Ctrl+Shift+...`)，自动过滤键盘长按重复。
   - 支持“文本 / 粘贴捕获”模式，便于中文与长段落无损录制。
6. **动态模板变量**：
   - 支持插入 `{{date}}` (当前日期)、`{{time}}` (当前时间)、`{{counter}}` (递增流水号)、`{{clipboard}}` (剪贴板文本)、`{{app_name}}` (目标应用名称)。
7. **目标软件感知与自动绑定 (Profiles)**：
   - 支持“自动跟踪最近前台窗口”与“🔒锁定目标窗口”双模式。
   - 在当前布局中即可一键绑定目标应用（例如检测到 `labelme.exe` 时自动切换为标注布局）。
8. **配置自愈与平滑迁移**：
   - 配置格式全面升级为 `schema_version: 2`，全自动向下兼容迁移旧版全局透明度与按钮回车设置。
   - 具备原子保存与损坏自动备份恢复机制。

---

## 🎯 内置预设场景包

### 1. 图片与数据标注 (Labelme / YOLO / 质检分类)
- **⚠ 缺陷+下一张**：输入 `defect` -> 确认 Enter -> 等待 50ms -> 发送 Right 键切换下一张图片。
- **✔ 正常+下一张**：输入 `normal` -> 确认 Enter -> 发送 Right 键切换下一张图片。
- **快捷键**：一键保存 (`Ctrl+S`)、多边形标注 (`Ctrl+N`)、矩形框 (`Ctrl+R`)、上张/下张图片。

### 2. 电商与售后客服话术 (淘宝 / 京东 / 拼多多)
- 标准欢迎语、查单核实、退款引导、致歉安抚、感谢道别。
- **服务记录工单**：自动插入带有实时系统时间与递增咨询单号的标准服务备忘：`【接待记录】客服已于 {{date}} {{time}} 接待咨询，工单编号: CS-{{counter}}。`
- 采用剪贴板无损粘贴并在使用后**自动恢复用户原剪贴板内容**。

### 3. 程序员 & DevOps 快捷输入
- `git status`、`git pull --rebase`、`git commit -m "fix: update {{date}}"`
- `docker ps -a`
- 插入 `// TODO({{date}}): ` 注释
- 插入 `console.log("[DEBUG]", );` 并自动将光标回退 2 格定位在括号内。

### 4. 符号录入与棋牌记谱 (中国象棋等)
| 阵营 | 按钮显示 | 点击输出字符 | 编码规则 |
| :--- | :--- | :--- | :--- |
| **红方 (7)** | 红兵 (`rb`), 红炮 (`rp`), 红马 (`rm`), 红车 (`rc`), 红士 (`rs`), 红相 (`rx`), 红帅 (`rshuai`) | `rb`, `rp`, `rm`, `rc`, `rs`, `rx`, `rshuai` | r + 拼音首字母 |
| **黑方 (7)** | 黑卒 (`bz`), 黑炮 (`bp`), 黑马 (`bm`), 黑车 (`bc`), 黑士 (`bs`), 黑象 (`bx`), 黑将 (`bj`) | `bz`, `bp`, `bm`, `bc`, `bs`, `bx`, `bj` | b + 拼音首字母 |

*支持在布局属性中开启“动作结束后发送 Enter”，便于连续记谱录入。*

---

## ⌨ 全局快捷键

| 快捷键 | 功能说明 |
| :--- | :--- |
| `Alt + Q` | 全局显示 / 隐藏悬浮工作台 |
| `Esc` | 紧急停止当前正在执行的多步骤宏 |

---

## 🚀 启动与使用方式

### 方式 1：免安装绿色版（无需 Python，双击即用）
直接打开已构建的便携目录：
👉 `dist\QuickInput\QuickInput.exe`
*(或者双击 `dist\QuickInput\QuickInput_Debug.bat` 在调试控制台下启动)*

### 方式 2：Python 源代码直接运行
若在开发环境中，推荐安装依赖后直接启动：
```bash
pip install -r requirements.txt
python main.py
```
*(或者直接双击 `start.bat` / 运行 `python floating_keyboard.py` 均可启动)*

### 方式 3：一键构建绿色便携版
双击运行根目录下的 `build.bat` 或执行：
```bash
python build_portable.py
```
构建产物将自动生成于 `dist/QuickInput/` 目录。

---

## 🏗 代码架构设计

软件严格遵循分层解耦与可扩展架构，核心模型不依赖任何操作系统专有 API：

```text
FloatPoint/
├── domain/                  # 纯领域模型 (Action, ActionStep, Button, Layout, Profile)
├── application/             # 业务层 (ActionExecutor, TargetManager, MacroRecorder, LayoutManager)
├── platform_layer/          # 平台抽象与操作系统适配
│   ├── base.py              # 跨平台抽象基类
│   └── windows/             # Windows SendInput、Win32 窗口管理、剪贴板与全局热键
├── storage/                 # 配置持久化与 .qipack 包管理
│   ├── config_store.py      # 原子写入、版本管理与损坏自愈
│   └── pack_store.py        # 导入导出、安全路径校验与打包
├── ui/                      # PyQt5 悬浮界面与可视化工作室
│   ├── floating_panel.py    # 零夺焦悬浮主面板
│   ├── settings_dialog.py   # 场景向导、布局与按钮编辑器
│   ├── macro_recorder_dialog.py # 宏录制弹窗
│   └── tray_icon.py         # 系统托盘管理
├── packs/                   # 内置 4 套开箱即用场景按钮包
├── docs/                    # 完整产品规格、格式规范与测试报告
│   ├── CONFIG_SPEC.md       # 配置与存储规范
│   ├── MACRO_ACTIONS_SPEC.md# 宏动作与步骤类型规范
│   ├── CROSS_PLATFORM_SPEC.md# 后续 macOS/Linux 适配指南
│   ├── LIMITATIONS.md       # 已知边界与限制
│   └── TEST_REPORT.md       # 自动化与功能测试报告
└── tests/                   # 91 项自动化单元测试与回归测试
```

---

## 🧪 自动化测试验证

在根目录下运行 pytest：
```bash
python -m pytest tests/
```
已包含：
- 领域模型与序列化校验
- 配置保存原子性与损坏自愈测试
- 按钮包导入导出与目录穿透拦截安全测试
- 宏执行器取消、超时、最大步数熔断测试
- 目标窗口自动追踪与管理员权限提升检测测试
- 锁定目标失焦前台恢复测试
- 宏录制器按键自动合并测试
- 预设场景包字符编码输出与自动回车回归测试
- SendInput 虚拟键标点映射防误删与扩展导航键测试
- 命名热键动态注册与注销测试（杜绝系统 ESC 键劫持）
- 屏幕工作区边缘像素级贴边吸附精准度测试
- 旧版配置平滑自动迁移测试
