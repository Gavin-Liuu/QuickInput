# QuickInput 跨平台架构与 macOS / Linux 适配指南 (Cross-Platform Specification)

## 1. 架构解耦现状

QuickInput 严格遵循领域驱动设计 (DDD) 与依赖倒置原则，核心逻辑（`domain` 与 `application`）与底层操作系统的输入注入和窗口管理完全解耦：

```text
QuickInput/
├── domain/                  # 纯领域模型，零 OS 与 Qt 依赖
│   ├── action.py
│   ├── button.py
│   ├── layout.py
│   └── profile.py
├── application/             # 业务应用层，依赖 platform_layer 抽象基类
│   ├── action_executor.py
│   ├── target_manager.py
│   ├── macro_recorder.py
│   └── layout_manager.py
└── platform_layer/          # 跨平台适配层
    ├── base.py              # 统一的抽象接口 (InputInjector, WindowManager, Clipboard, Hotkey)
    ├── windows/             # Windows 原生实现 (SendInput, Win32 API)
    ├── macos/               # macOS 适配层 (CGEvent, Accessibility)
    └── linux/               # Linux 适配层 (X11 / Wayland / uinput)
```

所有平台相关实现均必须继承 `platform_layer/base.py` 中定义的四个核心抽象类：
- `BaseInputInjector`
- `BaseWindowManager`
- `BaseClipboardManager`
- `BaseGlobalHotkeyManager`

---

## 2. 后续平台适配方案

### 2.1 macOS 平台适配 (`platform_layer/macos/`)

#### 1. 权限模型
- macOS 模拟键盘鼠标事件必须获取**辅助功能权限 (Accessibility Permissions)** (`AXIsProcessTrustedWithOptions`)。
- 当权限未授予时，平台适配层需检测并调用系统偏好设置向导引导用户开启权限。

#### 2. 输入注入 (`CGEvent`)
- 文本与按键模拟使用 CoreGraphics `CGEventCreateKeyboardEvent` 与 `CGEventPost`。
- Unicode 文本直接使用 `CGEventKeyboardSetUnicodeString` 注入多字节 UTF-16 字符，绕过 macOS 简体中文输入法。

#### 3. 悬浮窗不夺焦点
- Qt 设置 `NSWindowStyleMaskNonactivatingPanel`。
- 窗口层级设置为 `NSFloatingWindowLevel` 或 `kCGStatusWindowLevel`。
- 窗口点击消息返回不激活主应用。

#### 4. 目标窗口探测
- 通过 `NSWorkspace.shared.frontmostApplication` 获取当前活跃的 PID 和应用名称。
- 通过 Quartz Window Services (`CGWindowListCopyWindowInfo`) 获取窗口标题。

---

### 2.2 Linux 平台适配 (`platform_layer/linux/`)

#### 1. X11 环境
- **按键注入**: 使用 `XTest` 扩展 (`XTestFakeKeyEvent`) 或 `xdotool` / `uinput`。
- **免夺焦点**: 设置窗口属性 `_NET_WM_WINDOW_TYPE_UTILITY` 或 `_NET_WM_WINDOW_TYPE_DOCK`，并设置 `WM_TAKE_FOCUS` 标志。
- **窗口查询**: 通过 `_NET_ACTIVE_WINDOW` 获取当前活动窗口 ID，利用 `_NET_WM_NAME` 和 `_NET_WM_PID` 查询进程。

#### 2. Wayland 环境
- Wayland 默认禁止应用窥视其他窗口输入及全局合成注入。
- **推荐方案**:
  - 利用 Linux 核心虚拟输入设备 `/dev/uinput`（需要用户位于 `input` 用户组）；
  - 或通过 XDG Desktop Portal `org.freedesktop.portal.RemoteDesktop` 注入输入。
