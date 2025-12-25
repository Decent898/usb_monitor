# API 文档

## 核心模块 API

### USBScanner

USB 设备扫描器类，负责扫描和解析 USB 设备信息。

#### 方法

##### `scan_devices(timeout: int = 10) -> List[Dict[str, str]]`

扫描所有 USB 设备。

**参数:**
- `timeout` (int): 超时时间（秒），默认 10 秒

**返回:**
- `List[Dict[str, str]]`: 设备信息列表

**返回的字典格式:**
```python
{
    'name': str,          # 设备名称
    'manufacturer': str,  # 制造商
    'serial': str,        # 序列号
    'bus': str,          # USB 总线
    'speed': str,        # 传输速度
    'vid_pid': str       # VID:PID
}
```

**示例:**
```python
from src.core.usb_scanner import USBScanner

devices = USBScanner.scan_devices()
for device in devices:
    print(f"设备: {device['name']}, 制造商: {device['manufacturer']}")
```

---

### DriveManager

存储设备管理器类，负责管理 U 盘和存储设备的操作。

#### 方法

##### `scan_mounted_drives() -> List[Dict[str, str]]`

扫描已挂载的 U 盘。

**返回:**
- `List[Dict[str, str]]`: 驱动器信息列表

**返回的字典格式:**
```python
{
    'name': str,         # 设备名称
    'path': str,         # 挂载路径
    'filesystem': str,   # 文件系统类型
    'total': str,        # 总容量（格式化字符串）
    'used': str,         # 已使用（格式化字符串）
    'free': str,         # 可用空间（格式化字符串）
    'total_bytes': int,  # 总容量（字节）
    'used_bytes': int,   # 已使用（字节）
    'free_bytes': int    # 可用空间（字节）
}
```

**示例:**
```python
from src.core.drive_manager import DriveManager

drives = DriveManager.scan_mounted_drives()
for drive in drives:
    print(f"U盘: {drive['name']}, 可用: {drive['free']}")
```

---

##### `list_files(drive_path: str, show_hidden: bool = False) -> List[Dict[str, str]]`

列出驱动器中的文件。

**参数:**
- `drive_path` (str): 驱动器路径
- `show_hidden` (bool): 是否显示隐藏文件，默认 False

**返回:**
- `List[Dict[str, str]]`: 文件信息列表

**返回的字典格式:**
```python
{
    'name': str,     # 文件名
    'type': str,     # 类型（📁 文件夹 或 📄 文件）
    'size': str,     # 大小（格式化字符串）
    'path': str,     # 完整路径
    'is_dir': bool   # 是否为目录
}
```

**示例:**
```python
files = DriveManager.list_files('/Volumes/MyUSB', show_hidden=True)
for file in files:
    print(f"{file['name']} - {file['size']}")
```

---

##### `write_text_file(drive_path: str, filename: str, content: str) -> bool`

写入文本文件到 U 盘。

**参数:**
- `drive_path` (str): 驱动器路径
- `filename` (str): 文件名
- `content` (str): 文件内容

**返回:**
- `bool`: 是否成功

**示例:**
```python
success = DriveManager.write_text_file(
    '/Volumes/MyUSB',
    'test.txt',
    'Hello, World!'
)
if success:
    print("文件写入成功")
```

---

##### `delete_file(file_path: str) -> bool`

删除文件。

**参数:**
- `file_path` (str): 文件路径

**返回:**
- `bool`: 是否成功

**示例:**
```python
success = DriveManager.delete_file('/Volumes/MyUSB/test.txt')
if success:
    print("文件删除成功")
```

---

### FileTransferThread

文件传输线程类，负责异步文件传输。

#### 构造函数

```python
FileTransferThread(source: str, destination: str, chunk_size: int = 1024 * 1024)
```

**参数:**
- `source` (str): 源文件路径
- `destination` (str): 目标文件路径
- `chunk_size` (int): 每次读取的块大小（字节），默认 1MB

#### 信号

##### `progress` - pyqtSignal(int, str)

传输进度信号。

**参数:**
- `int`: 进度百分比 (0-100)
- `str`: 传输速度字符串（如 "5.23 MB/s"）

---

##### `finished` - pyqtSignal(bool, str)

传输完成信号。

**参数:**
- `bool`: 是否成功
- `str`: 消息字符串

#### 方法

##### `run()`

执行文件传输（由 QThread 自动调用）。

---

##### `cancel()`

取消正在进行的传输。

**示例:**
```python
from src.core.file_transfer import FileTransferThread

# 创建传输线程
transfer = FileTransferThread(
    '/path/to/source.zip',
    '/Volumes/MyUSB/destination.zip'
)

# 连接信号
transfer.progress.connect(lambda progress, speed: 
    print(f"进度: {progress}%, 速度: {speed}"))
transfer.finished.connect(lambda success, msg: 
    print(f"完成: {msg}"))

# 开始传输
transfer.start()

# 取消传输（如需要）
# transfer.cancel()
```

---

## UI 模块 API

### AppStyles

应用程序样式配置类。

#### 颜色常量

```python
PRIMARY_COLOR = "#2196F3"     # 主色调 - 蓝色
PRIMARY_DARK = "#0b7dda"
PRIMARY_LIGHT = "#64B5F6"

SECONDARY_COLOR = "#4CAF50"   # 次要色 - 绿色
SECONDARY_DARK = "#45a049"

ACCENT_COLOR = "#FF9800"      # 强调色 - 橙色
ACCENT_DARK = "#F57C00"

DANGER_COLOR = "#f44336"      # 危险色 - 红色
DANGER_DARK = "#da190b"

PURPLE_COLOR = "#9C27B0"      # 紫色
PURPLE_DARK = "#7B1FA2"
```

#### 方法

所有方法都是静态方法，返回 CSS 样式字符串：

- `get_main_window_style() -> str`: 主窗口样式
- `get_header_style() -> str`: 标题栏样式
- `get_primary_button_style() -> str`: 主按钮样式
- `get_secondary_button_style() -> str`: 次按钮样式
- `get_accent_button_style() -> str`: 强调按钮样式
- `get_danger_button_style() -> str`: 危险按钮样式
- `get_purple_button_style() -> str`: 紫色按钮样式
- `get_table_style() -> str`: 表格样式
- `get_group_box_style() -> str`: 分组框样式
- `get_input_style() -> str`: 输入框样式
- `get_tab_widget_style() -> str`: 标签页样式
- `get_progress_bar_style() -> str`: 进度条样式
- `get_user_badge_style() -> str`: 用户徽章样式
- `get_speed_label_style() -> str`: 速度标签样式
- `get_checkbox_style() -> str`: 复选框样式

**示例:**
```python
from src.ui.styles import AppStyles

# 获取按钮样式
button.setStyleSheet(AppStyles.get_primary_button_style())

# 自定义颜色
AppStyles.PRIMARY_COLOR = "#FF5722"
```

---

### USBManagerWindow

主窗口类。

#### 构造函数

```python
USBManagerWindow()
```

#### 主要方法

##### `scan_usb_devices()`

扫描并显示 USB 设备。

---

##### `scan_mounted_drives()`

扫描并显示已挂载的 U 盘。

---

##### `refresh_all()`

刷新所有数据（USB 设备和 U 盘）。

---

##### `write_text_file()`

写入文本文件到选中的 U 盘。

---

##### `upload_file()`

上传文件到选中的 U 盘（带进度显示）。

---

##### `delete_file(file_path: str)`

删除指定文件。

**参数:**
- `file_path` (str): 要删除的文件路径

---

## 配置文件

### settings.ini

应用程序配置文件位于 `config/settings.ini`。

```ini
[app]
name = USB 设备管理器
version = 1.0.0
author = Your Name

[ui]
window_width = 1500
window_height = 950
auto_refresh_interval = 3000

[transfer]
chunk_size = 1048576

[scanner]
scan_timeout = 10
```

**配置说明:**
- `window_width`, `window_height`: 窗口默认大小
- `auto_refresh_interval`: 自动刷新间隔（毫秒）
- `chunk_size`: 文件传输块大小（字节）
- `scan_timeout`: USB 扫描超时时间（秒）
