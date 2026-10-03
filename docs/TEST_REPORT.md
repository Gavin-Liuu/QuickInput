# QuickInput 自动化与功能测试报告 (Test Report)

**测试环境**:
- 操作系统: Windows 10/11 x64
- Python 版本: Python 3.11.7
- GUI 框架: PyQt5 5.15.10
- 底层 API: Windows Win32 API (`SendInput`, `WS_EX_NOACTIVATE`, `MA_NOACTIVATE`, `RegisterHotKey`)
- 测试框架: pytest 7.4.0

---

## 1. 自动化测试结果概览

运行命令：`python -m pytest tests/`  
测试结果：**59 项测试全部通过 (100% Passed)**，运行耗时 **0.98 秒**。

```text
============================= test session starts =============================
platform win32 -- Python 3.11.7, pytest-7.4.0, pluggy-1.0.0
rootdir: E:\Projects\FloatPoint
plugins: anyio-4.2.0
collected 59 items

tests\test_domain.py ......                                              [ 10%]
tests\test_edge_cases.py .....                                           [ 18%]
tests\test_executor.py .....                                             [ 27%]
tests\test_layout_manager.py ......                                      [ 37%]
tests\test_macro_recorder.py ...........                                 [ 55%]
tests\test_pack_store.py ...                                             [ 61%]
tests\test_platform_fixes.py .....                                       [ 69%]
tests\test_regression_chess.py ..                                        [ 72%]
tests\test_storage.py ....                                               [ 79%]
tests\test_target_manager.py ....                                        [ 86%]
tests\test_ui_behavior.py ........                                       [100%]

============================= 59 passed in 0.98s ==============================
```

---

## 2. 核心功能测试覆盖清单

### 2.1 领域模型与边界校验 (`tests/test_domain.py`)
- [x] `ActionStep` 序列化与反序列化验证
- [x] 各类型步骤参数有效性校验（无效类型、负延迟、非法变量名拦截）
- [x] `Action` 完整序列化、深度克隆与复合步骤验证
- [x] `Button` 属性映射、主题色与 Tooltip 验证
- [x] `Layout` 网格坐标非负性、行列合理性与设置项验证
- [x] `Profile` 目标软件进程名与标题模糊匹配测试

### 2.2 存储可靠性与异常恢复 (`tests/test_storage.py`)
- [x] 配置文件初次加载与默认结构生成
- [x] 基于临时文件与 `os.replace` 的原子写入机制验证
- [x] **配置损坏自愈机制**: 模拟非法 JSON 语法损坏，验证系统能否自动将损坏文件备份至 `backups/config_corrupted_*.json` 并自动恢复默认配置启动，零崩溃。
- [x] 时间戳快照配置备份功能

### 2.3 按钮包导入导出与安全防护 (`tests/test_pack_store.py`)
- [x] `.qipack` 标准 ZIP 包打包与全量解压导入
- [x] 4 套内置预设包（中国象棋、图片标注、客服话术、程序员快捷键）全量 schema 严格校验
- [x] 按钮与动作 ID 重复冲突拦截
- [x] **路径遍历安全防御**: 拦截包含 `../../` 等危险路径的恶意按钮包

### 2.4 动作执行引擎与变量插值 (`tests/test_executor.py`)
- [x] 纯文本注入、单键敲击、复合快捷键顺序模拟
- [x] 动态模板变量插值：`{{date}}`, `{{time}}`, `{{counter}}`, `{{clipboard}}`, `{{app_name}}`
- [x] 自动递增计数器 `{{counter}}` 状态维护
- [x] 自动回车 (Auto Enter) 全局/覆盖追加逻辑
- [x] **宏运行取消与熔断**: 执行中的非阻塞毫秒切片取消测试，确保取消请求毫秒级响应
- [x] 步骤最大上限（500步）防无限循环熔断测试

### 2.5 目标窗口跟踪与权限感知 (`tests/test_target_manager.py`)
- [x] 自身窗口过滤（不将悬浮面板识别为目标输入窗口）
- [x] 自动模式 (Auto) 下外部活动窗口动态跟踪
- [x] 锁定模式 (Locked) 下固定目标窗口保持与解除
- [x] 管理员权限提升状态探测与警示提示
- [x] **锁定目标失焦自动激活**: 锁定模式下，若当前前台窗口非锁定目标，在注入输入前自动调用 `set_foreground_safe` 激活目标，防止输入打入错误程序。

### 2.6 布局管理与场景联动 (`tests/test_layout_manager.py`)
- [x] 布局切换、复制、重命名与安全删除（防止全部删除）
- [x] 应用程序绑定规则触发的自动场景切换
- [x] 按钮关键字实时检索（匹配名称、动作与提示）
- [x] 最近使用按钮列表 LRU 自动追踪

### 2.7 宏录制器按键捕获与流合并 (`tests/test_macro_recorder.py`)
- [x] 连续敲击字符自动合并为单一 `text` 文本步骤（避免分散为单字符）
- [x] 特殊功能键（Enter, Tab, Esc 等）映射为 `key` 步骤
- [x] 修饰键组合（Ctrl+S 等）自动解析为 `hotkey` 步骤

### 2.8 原有中国象棋功能回归测试 (`tests/test_regression_chess.py`)
- [x] 原有 14 颗棋子快捷按钮完整性校验
- [x] 红兵 (`red_bing`) 严格输出 `rb`
- [x] 黑将 (`black_jiang`) 严格输出 `bj`
- [x] 自动回车开启时，输出字符编码后追加发送 `Enter`

### 2.9 极端边界用例测试 (`tests/test_edge_cases.py`)
- [x] 空步骤动作优雅完成，无异常
- [x] 嵌套循环步骤（`repeat` 嵌 `repeat`）完整展开执行
- [x] 高频快速连击防重入拦截（正在执行时阻止二次触发并发碰撞）
- [x] 多语言 Unicode、特殊字符与 Emoji 表情（`🌹❤️♟`）注入测试
- [x] 恶意 Zip 路径穿越防护拦截

### 2.10 平台底层与致命缺陷修复验证 (`tests/test_platform_fixes.py`)
- [x] **Win32 SendInput 虚拟键映射防踩坑修复**:
  - `.` 映射为 `VK_OEM_PERIOD` (0xBE = 190)，彻底杜绝因 `ord('.')` (46) 错误映射为 `VK_DELETE` (46) 导致点变成删除键的致命 bug；
  - `,` 映射为 `VK_OEM_COMMA` (0xBC = 188)，杜绝误映射为 `VK_SNAPSHOT` (44)；
  - `-` 映射为 `VK_OEM_MINUS` (0xBD = 189)，杜绝误映射为 `VK_INSERT` (45)；
  - `/` 与 `;` 映射为对应 OEM 键位，并使用 `VkKeyScanW` 动态补充未知标点符号。
- [x] **扩展导航键 (Extended Keys)**:
  - 方向键 (`UP`, `DOWN`, `LEFT`, `RIGHT`)、`HOME`、`END`、`PAGEUP`、`PAGEDOWN` 等自动附带 `KEYEVENTF_EXTENDEDKEY` 标志，防止在特定目标软件中被识别为小键盘数字键。
- [x] **命名全局热键与动态注销机制**:
  - 支持 `register_named_hotkey` 与 `unregister_named_hotkey`，支持在宏执行开始时动态注册 `ESC` 急停键，执行结束或取消后立即注销释放，**绝不占用系统全局 ESC 键**，彻底解决物理键盘被劫持的问题。
- [x] **旧版配置文件无损自动迁移**:
  - 自动将存量 `floating_keyboard_config.json` 的坐标、透明度、自动回车和布局模式合并迁移到产品化 `config.json`。
- [x] **像素级贴边吸附精准度计算**:
  - 验证屏幕边缘（左、右、上、下）吸附阈值（18px）下计算坐标与屏幕可用矩形边缘的像素级贴合（`geom.x() + geom.width() - width`）。

### 2.11 UI交互行为与关键缺陷修复验证 (`tests/test_ui_behavior.py`)
- [x] **设置对话框与全量模块导入零崩溃**:
  - 补充 `ui/settings_dialog.py` 中遗漏的 `typing` 模块导入（`Optional`, `List`, `Dict`, `Any`, `Tuple`），彻底杜绝由于 `NameError` 导致的程序无法启动崩溃。
- [x] **网格槽位拖拽与四向微调重排序**:
  - 实现了基于 Qt 拖拽协议的 `PreviewSlotButton`（`mouseMoveEvent` / `dragEnterEvent` / `dropEvent`）和 `▲ 上移`、`▼ 下移`、`◀ 左移`、`▶ 右移` 按钮微调，支持自由交换按钮网格位置。
- [x] **按钮图标与文本组合渲染**:
  - 支持配置按钮自定义图标/Emoji，悬浮按钮无缝渲染 `f"{icon} {label}"`。
- [x] **宏录制目标失去与恢复感知**:
  - 修复 `_should_capture_foreground` 绕过自身窗口检查导致 `on_target_lost` 从不触发的缺陷；加入 150ms 动态焦点轮询检测器，实时预警非目标窗口输入。
- [x] **悬浮面板透明度与全量属性持久化**:
  - 修复 `apply_config` 同步滑块位置及 `save_window_config` 完整保存 `buttons`、`actions`、`profiles`，防止布局编辑数据意外丢失。

---

## 3. 手工与真实软件集成测试

| 测试对象 | 测试场景 | 预期效果 | 实际结果 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| **Windows 记事本** | 点击【红兵】、连续输入、自动回车 | 字符 `rb` 立即打入记事本光标处，无夺焦，自动换行 | 完美输入，输入法候选框未被触发 | ✅ 通过 |
| **Windows 记事本** | 标点符号与特殊字符输入 (`.`, `,`, `-`, `/`, `;`) | 输入对应标点符号，不删除文本，不出快照 | 字符精准注入，无删除或 Insert 切换 | ✅ 通过 |
| **VS Code / 终端** | 执行程序员宏 (`git status` / `TODO` 注释) | 命令文本秒级注入，模板变量替换为系统今日日期 | 正常显示并执行，变量替换精准 | ✅ 通过 |
| **Labelme / 标注** | 执行【缺陷+下一张】(`defect` -> Enter -> Delay -> Right) | 文本输入后确认并切换至下一张图 | 流程平滑无卡顿，悬浮面板无卡死 | ✅ 通过 |
| **中文输入法环境** | 微软拼音/搜狗输入法激活状态下点击按钮 | 字符直接以 Unicode 注入，不弹出输入法拼音候选框 | 直接上屏，无拼音干扰 | ✅ 通过 |
| **物理键盘并发** | 点击悬浮按钮的同时在物理键盘上敲击文字 | 物理按键与虚拟输入不冲突、不吞字、按键正常响应 | 物理键盘完全畅通 | ✅ 通过 |
| **宏急停与取消** | 运行 300 步长宏时按下 `ESC` 或面板 `⏹停止` | 宏在下一毫秒切片立刻中止，状态栏提示“已取消” | 毫秒级中止，ESC键随即释放 | ✅ 通过 |
| **管理员权限窗口** | 针对以管理员身份运行的 CMD/PowerShell 窗口 | 悬浮窗状态栏浮现黄色叹号警告，提示特权隔离 | 正确探测并告警 | ✅ 通过 |

---

## 4. 打包与绿色免安装发布验证

- [x] 使用 PyInstaller 6.22.3 构建生成 `dist/QuickInput/` 绿色目录。
- [x] 生成独立可执行文件 `dist/QuickInput/QuickInput.exe`（大小约 2.0 MB）。
- [x] 内置预装 4 套场景包 `dist/QuickInput/packs/{chess, annotation, customer_service, programmer}`。
- [x] 提供 `README.txt` 使用指南与免杀说明。
- [x] 提供 `QuickInput_Debug.bat` 用于无 Python 环境下的控制台故障排查。
- [x] 单实例互斥体 (`Global\QuickInput_App_SingleInstance_Mutex_v1`) 生效，禁止多开。
