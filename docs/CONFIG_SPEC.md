# QuickInput 配置格式规范文档 (Config Specification)

## 1. 配置文件存储路径与版本机制

QuickInput 的主配置文件默认保存在用户应用数据目录中：
- Windows: `%APPDATA%\QuickInput\config.json`
- 备用路径: 程序同级目录 `data/config.json`
- 自动备份目录: `%APPDATA%\QuickInput\backups/`
- 日志目录: `%APPDATA%\QuickInput\logs/`

配置文件使用 `schema_version` 字段标记配置格式版本（当前版本为 `2`），支持向后兼容与平滑迁移。

### 容灾与原子写入保障
1. **原子保存**: 所有配置写入均采用“写入临时文件 (`cfg_tmp_*.json`) -> `os.replace` 原子替换”机制，杜绝断电或进程中断导致的 JSON 半写损坏。
2. **损坏自动恢复**: 若配置文件因外部篡改出现 JSON 解析失败，系统会自动将损坏文件备份至 `backups/config_corrupted_<timestamp>.json`，并自动重置为默认合法配置，保证软件绝对不会崩溃或无法启动。
3. **v1 到 v2 自动迁移**: 系统检测到 schema_version 为 1 时，自动将旧版本全局透明度、全局自动回车及按钮级确认/回车配置平滑迁移到布局级设置中。

---

## 2. 根字段结构定义

```json
{
  "schema_version": 2,
  "window": {
    "x": 350,
    "y": 250,
    "opacity": 0.95,
    "always_on_top": true,
    "layout_mode": "horizontal",
    "button_size": "compact"
  },
  "active_layout_id": "chess",
  "hotkeys": {
    "toggle_visible": "ALT+Q",
    "emergency_stop": "ESC"
  },
  "settings": {
    "auto_profile_switch": true,
    "target_mode": "auto",
    "record_delays": true
  },
  "layouts": {},
  "buttons": {},
  "actions": {},
  "profiles": []
}
```

### 字段说明
- `window`: 控制悬浮面板的几何位置、透明度、置顶状态及尺寸模式。
- `active_layout_id`: 当前激活的布局唯一标识符。
- `hotkeys`:
  - `toggle_visible`: 全局呼出 / 隐藏面板热键（默认 `ALT+Q`）。
  - `emergency_stop`: 全局紧急停止正在执行的宏热键（默认 `ESC`）。
- `settings`:
  - `auto_profile_switch`: 是否根据前台目标软件自动切换绑定的布局。
  - `target_mode`: `auto`（自动跟踪最近前台窗口）或 `locked`（锁定目标窗口）。
- `layouts`: 布局字典，键为 `layout_id`。
- `buttons`: 按钮字典，键为 `button_id`。
- `actions`: 动作字典，键为 `action_id`。
- `profiles`: 应用程序自动绑定规则列表。

---

## 3. 布局对象 (Layout) 结构

```json
{
  "id": "annotation",
  "name": "图片与数据标注",
  "orientation": "horizontal",
  "rows": 2,
  "columns": 4,
  "description": "2x4 紧凑标注工作流",
  "buttons": [
    { "button_id": "btn_defect", "row": 0, "column": 0 },
    { "button_id": "btn_normal", "row": 0, "column": 1 },
    { "button_id": "btn_bg", "row": 0, "column": 2 },
    { "button_id": "btn_save", "row": 0, "column": 3 }
  ],
  "settings": {
    "opacity": 0.95,
    "show_labels": true,
    "button_size": "compact",
    "always_on_top": true,
    "auto_enter_default": false,
    "confirm_before_action": false
  }
}
```

---

## 4. 按钮对象 (Button) 结构

```json
{
  "id": "btn_defect",
  "label": "⚠ 缺陷\n+下一张",
  "action_id": "act_defect_next",
  "icon": "缺陷",
  "color": "#D32F2F",
  "tooltip": "输入 defect 并跳到下一张",
  "auto_enter": null
}
```

---

## 5. 应用绑定规则 (Profile) 结构

```json
{
  "id": "prof_1",
  "name": "Labelme自动适配",
  "process": "labelme.exe",
  "window_title_contains": "",
  "layout_id": "annotation",
  "enabled": true
}
```

---

## 6. 按钮包 (.qipack) 格式规范

`.qipack` 为标准 ZIP 压缩包，解压后包含以下规范文件：
```text
my_pack.qipack/
├── manifest.json   (元数据描述)
├── actions.json    (动作集合)
├── layouts.json    (布局定义)
├── buttons.json    (按钮定义)
├── icons/          (可选图标资源)
└── README.md       (说明文档)
```
所有导入包均经过严格的路径穿透防护（禁止 `../` 和绝对路径）与 schema 校验。
