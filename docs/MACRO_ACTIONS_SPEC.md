# QuickInput 宏动作与步骤类型规范 (Macro & Action Specification)

QuickInput 将复杂的自动化操作抽象为原子化的步骤（`ActionStep`）。多个步骤串联构成动作（`Action`）。

---

## 1. 动作对象 (Action) 定义

```json
{
  "id": "act_defect_next",
  "label": "缺陷+下一张",
  "description": "输入 defect，按回车确认并跳转下一张",
  "icon": "warning",
  "color": "#D32F2F",
  "steps": [
    { "type": "text", "value": "defect" },
    { "type": "key", "key": "ENTER" },
    { "type": "delay", "ms": 50 },
    { "type": "key", "key": "RIGHT" }
  ],
  "on_error": "stop",
  "confirm": false,
  "auto_enter": false
}
```

### 属性说明
- `id`: 动作唯一标识符（字符串）。
- `label`: 界面显示名称。
- `description`: 描述说明或悬浮提示。
- `steps`: 步骤列表，按顺序执行。
- `on_error`: 步骤出错时的策略：
  - `"stop"`: 遇到错误立即停止后续步骤并提示用户；
  - `"continue"`: 忽略错误继续执行下一步骤。
- `confirm`: 是否在运行前弹出对话框要求用户确认（用于危险操作）。
- `auto_enter`: 动作执行完后是否自动追加一个 Enter 键。

---

## 2. 支持的步骤类型 (Step Types)

### 2.1 `text` (文本输入)
直接向目标窗口注入 Unicode 文本，底层采用 Windows `SendInput` 的 `KEYEVENTF_UNICODE` 标志。
- **特性**: 完全绕过中文输入法（如搜狗、微软拼音、微信输入法）候选框，不跳词、不吞字、绝不产生拼音干扰。
- **支持变量替换**: 可以在文本中混入模板变量，如 `"Item-{{counter}}: {{date}}"`。
```json
{ "type": "text", "value": "git commit -m \"update {{date}}\"" }
```

### 2.2 `key` (单键敲击)
发送标准键盘按键的按下与弹起事件。
- 支持按键: `ENTER`、`TAB`、`ESC`、`SPACE`、`BACKSPACE`、`DELETE`、`LEFT`、`RIGHT`、`UP`、`DOWN`、`HOME`、`END`、`PAGEUP`、`PAGEDOWN`、`F1`~`F12`、字母及数字键。
```json
{ "type": "key", "key": "ENTER" }
```

### 2.3 `hotkey` (组合键)
发送复合修饰键组合，按顺序按下修饰键 -> 按下主键 -> 逆序释放修饰键。
- 支持修饰键: `CTRL`、`SHIFT`、`ALT`、`WIN`。
```json
{ "type": "hotkey", "hotkey": "CTRL+S" }
```
或者：
```json
{ "type": "hotkey", "keys": ["CTRL", "SHIFT", "P"] }
```

### 2.4 `delay` (毫秒等待)
宏执行期间非阻塞等待指定毫秒数（内部采用毫秒切片轮询，随时响应取消操作）。
```json
{ "type": "delay", "ms": 100 }
```

### 2.5 `paste` (剪贴板注入与自动恢复)
将指定文本复制到剪贴板，发送 `Ctrl+V` 粘贴，并在完成后自动将剪贴板恢复为用户原有的内容。
- **适用场景**: 包含大量换行符的多行长文本、客服大段标准话术。
```json
{ "type": "paste", "value": "亲，您好！很高兴为您服务～\n请问有什么可以帮您的呢？" }
```

### 2.6 `variable` (动态变量)
快速将系统环境或上下文变量直接注入到输入流中：
```json
{ "type": "variable", "name": "clipboard" }
```

### 2.7 `repeat` (步骤重复循环)
将包含的子步骤列表循环执行指定次数：
```json
{
  "type": "repeat",
  "count": 3,
  "steps": [
    { "type": "text", "value": "abc" },
    { "type": "key", "key": "TAB" }
  ]
}
```

### 2.8 `mouse` (鼠标操作)
执行鼠标点击、双击、右击或移动：
```json
{ "type": "mouse", "mouse_action": "click", "x": 500, "y": 300 }
```

---

## 3. 支持的动态模板变量 (Template Variables)

| 变量语法 | 替换内容 | 示例输出 |
| :--- | :--- | :--- |
| `{{clipboard}}` | 当前系统剪贴板中的纯文本 | `https://example.com` |
| `{{date}}` | 当前系统本地日期 (YYYY-MM-DD) | `2026-09-30` |
| `{{time}}` | 当前系统本地时间 (HH:MM:SS) | `14:30:00` |
| `{{counter}}` | 运行时自动递增的正整数计数器 | `1`, `2`, `3`... |
| `{{app_name}}` | 当前目标软件的进程名或窗口标题 | `Labelme.exe` |

---

## 4. 安全防护机制
1. **最大步数限制**: 单个宏最大展开步骤数默认为 500 步，杜绝由于 `repeat` 嵌套导致的无限步骤死循环。
2. **最大执行超时**: 单个宏执行时间硬性上限为 30 秒，超时自动熔断并中止。
3. **紧急停止**: 用户随时可按下 `ESC` 键或悬浮窗底部的 `⏹停止` 按钮立即终止当前宏。
