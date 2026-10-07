# QuickInput - Lightweight Floating Action Panel & Quick Input Workbench

[English](README_EN.md) | [简体中文](README.md)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt5-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Windows SendInput](https://img.shields.io/badge/platform-Windows_SendInput-orange.svg)]()
[![Tests](https://img.shields.io/badge/tests-91%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**QuickInput** is a lightweight, zero-focus-stealing floating action panel and productivity workbench tailored for Windows. Without touching code or JSON files, users can quickly inject text, dispatch keystrokes, execute keyboard shortcuts, paste dynamic rich-text templates, and run multi-step macros into any third-party target application (e.g., Labelme annotation tool, Notepad, Microsoft Word, Excel, web browsers, VS Code, workplace & chat tools) with a single click.

The workbench provides a fully customizable visual layout studio and safe macro recorder, complete with built-in preset packs for data annotation, customer support scripts, developer quick actions, and fast notation recording.

---

## 🌟 Key Features

1. **Zero Focus Stealing & Native Windows Integration**:
   - Built on native Win32 `WS_EX_NOACTIVATE` and `MA_NOACTIVATE` architectures.
   - Clicking floating buttons never steals focus or activates the QuickInput window—your text caret stays firmly inside your target application with zero physical keyboard interruption.
   - Adopts Windows native window frame and edge-resizing, complete with Windows DWM immersive dark mode (`DWMWA_USE_IMMERSIVE_DARK_MODE`).
   - Native close button (`×`) minimizes safely to the system tray. Exiting cleanly through tray right-click unhooks all global hotkeys and threads, leaving zero orphaned background processes.

2. **Direct Unicode `SendInput` Engine**:
   - Built entirely on modern Win32 `SendInput` with `KEYEVENTF_UNICODE` flags.
   - Bypasses active Chinese/IME input candidate boxes completely, preventing unwanted popup candidates, dropped characters, or garbled text.

3. **Clean & Tactile Main Panel**:
   - **Global Search Button**: Expand the search bar with `[🔍]` to search action buttons across all layouts instantly, with automatic zero-focus-stealing restoration upon exit.
   - **Real-Time Opacity Slider**: Adjust panel transparency smoothly from 20% to 100% on the fly.
   - **Tactile Keycaps**: Subtle bevel micro-gradients with a 2px physical depression feedback, maintaining precision scaling across compact, standard, and touch sizes.

4. **Unified "Layout & Buttons" Studio**:
   - Visual interactive grid preview with click-to-add empty slots, drag/drop order, and row-column transposition (`⇄`).
   - Layout-level unified toggles for "Send Enter on completion" and "Confirmation before execution".

5. **Safe Visual Macro Key Recorder**:
   - Target-window guarded: Filters out non-target and self-window keystrokes, warning users when focus switches away.
   - Resolves key characters accurately via `ToUnicodeEx` based on active keyboard layout, standardizes modifier order (`Ctrl+Shift+...`), and prevents key-repeat flooding.
   - Supports "Text / Clipboard Capture" mode for pristine multiline and Chinese text recording.

6. **Dynamic Template Variables**:
   - Insert live parameters: `{{date}}` (current date), `{{time}}` (current time), `{{counter}}` (incrementing sequence number), `{{clipboard}}` (clipboard content), `{{app_name}}` (target application process name).

7. **Target App Sensing & Auto-Binding (Profiles)**:
   - Supports both "Auto-track foreground window" and "🔒 Lock target window" modes.
   - Bind layouts to specific processes (e.g., auto-switch to Annotation layout when `labelme.exe` is detected).

8. **Configuration Self-Healing & Seamless Migration**:
   - Fully versioned (`schema_version: 2`) configuration with atomic writes and automatic corrupted-file recovery.
   - Backward-compatible migration from legacy `floating_keyboard_config.json`.

---

## 🎯 Built-in Preset Packs

### 1. Image & Data Annotation (Labelme / YOLO / Inspection)
- **Defect + Next**: Types `defect` -> Enter -> Wait 50ms -> Right arrow key to advance.
- **Normal + Next**: Types `normal` -> Enter -> Right arrow key.
- **Shortcuts**: Save (`Ctrl+S`), Create Polygon (`Ctrl+N`), Create Rectangle (`Ctrl+R`), Prev/Next image.

### 2. Customer Service & Sales Templates
- Quick greetings, order lookups, refund guides, and farewells.
- **Ticket Note Generator**: Inserts timestamped service logs with auto-incrementing serial IDs:
  `[Service Note] Handled on {{date}} {{time}}, Ticket ID: CS-{{counter}}.`
- Uses lossless clipboard injection that automatically restores your original clipboard content.

### 3. Developer & DevOps Quick Actions
- Git commands: `git status`, `git pull --rebase`, `git commit -m "fix: update {{date}}"`.
- Docker commands: `docker ps -a`.
- Code snippets: Insert `// TODO({{date}}): ` or `console.log("[DEBUG]", );` with caret auto-positioned inside quotes.

### 4. Fast Notation & Symbol Entry (Chinese Chess, etc.)
| Side | Display | Output Code | Naming Rule |
| :--- | :--- | :--- | :--- |
| **Red (7)** | 红兵 (`rb`), 红炮 (`rp`), 红马 (`rm`), 红车 (`rc`), 红士 (`rs`), 红相 (`rx`), 红帅 (`rshuai`) | `rb`, `rp`, `rm`, `rc`, `rs`, `rx`, `rshuai` | r + Pinyin initial |
| **Black (7)** | 黑卒 (`bz`), 黑炮 (`bp`), 黑马 (`bm`), 黑车 (`bc`), 黑士 (`bs`), 黑象 (`bx`), 黑将 (`bj`) | `bz`, `bp`, `bm`, `bc`, `bs`, `bx`, `bj` | b + Pinyin initial |

*Supports automatic Enter confirmation configured per-layout.*

---

## ⌨ Global Hotkeys

| Hotkey | Action |
| :--- | :--- |
| `Alt + Q` | Toggle show/hide floating workbench |
| `Esc` | Emergency abort for running multi-step macros |

---

## 🚀 Getting Started

### Option 1: Standalone Portable Package (No Python Required)
Run the pre-built portable executable:
👉 `dist\QuickInput\QuickInput.exe`
*(or run `dist\QuickInput\QuickInput_Debug.bat` for debug console output)*

### Option 2: Run from Source
Clone the repository and install dependencies:
```bash
git clone https://github.com/Gavin-Liuu/QuickInput.git
cd QuickInput
pip install -r requirements.txt
python main.py
```
*(or run `start.bat` / `python floating_keyboard.py`)*

### Option 3: Build Standalone Executable
Run the portable build script:
```bash
python build_portable.py
```
The output directory will be created at `dist/QuickInput/`.

---

## 🏗 Architecture Overview

The codebase follows a decoupled domain-driven design:

```text
QuickInput/
├── domain/                  # Pure domain entities (Action, ActionStep, Button, Layout, Profile)
├── application/             # Application services (ActionExecutor, TargetManager, MacroRecorder, LayoutManager)
├── platform_layer/          # OS abstraction layer
│   ├── base.py              # Cross-platform abstract interfaces
│   └── windows/             # Windows SendInput, Win32 window manager, clipboard & global hotkeys
├── storage/                 # Persistence & .qipack package management
│   ├── config_store.py      # Atomic write, schema versioning & self-healing
│   └── pack_store.py        # Preset pack import/export & traversal security
├── ui/                      # PyQt5 floating interface & settings studio
│   ├── floating_panel.py    # Zero-focus-stealing floating main panel
│   ├── settings_dialog.py   # Unified layout & button visual studio
│   ├── macro_recorder_dialog.py # Visual macro recording dialog
│   └── tray_icon.py         # System tray icon & lifecycle manager
├── packs/                   # 4 built-in preset scene packages
├── docs/                    # Architecture, specifications & test reports
│   ├── tasks/               # Historical development specifications
│   ├── CONFIG_SPEC.md       # Configuration format specification
│   ├── MACRO_ACTIONS_SPEC.md# Macro actions & step specification
│   ├── CROSS_PLATFORM_SPEC.md# macOS / Linux extension roadmap
│   ├── LIMITATIONS.md       # Known boundaries & edge cases
│   └── TEST_REPORT.md       # Comprehensive testing report
└── tests/                   # 91 automated unit and regression test suites
```

---

## 🧪 Automated Tests

Run pytest across all 91 test suites:
```bash
python -m pytest tests/
```

Verified test suites include:
- Domain model validation and serialization
- Config atomic write and corrupted file self-healing
- Preset pack import/export and path traversal security guards
- Macro execution cancellation, timeouts, and max-step circuit breakers
- Target window auto-tracking and elevated UAC admin detection
- Target window focus restore upon blur
- Macro recorder key merging and debounce handling
- Preset pack character encoding and auto-enter validation suite
- SendInput punctuation mapping and navigation key tests
- Global hotkey safe registration and cleanup
- Pixel-perfect screen edge snapping algorithms
- Legacy config smooth migration

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
