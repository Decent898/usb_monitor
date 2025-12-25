# 🔌 USB 设备管理器

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

一个功能强大、界面美观的 macOS USB 设备监控和管理工具

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用指南](#使用指南) • [项目结构](#项目结构) • [开发说明](#开发说明)

</div>

---

## 📋 目录

- [功能特性](#功能特性)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [开发说明](#开发说明)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## ✨ 功能特性

### 🔍 USB 设备监控
- ✅ 实时扫描和显示所有连接的 USB 设备
- ✅ 显示设备详细信息（名称、制造商、序列号、USB 总线、传输速度、VID/PID）
- ✅ 自动刷新设备列表（每 3 秒）
- ✅ 支持 USB 2.0、USB 3.0 及更高版本设备

### 💾 U 盘管理
- ✅ 自动检测已挂载的 U 盘和存储设备
- ✅ 显示磁盘使用情况（总容量、已使用、可用空间）
- ✅ 显示文件系统类型（FAT32、exFAT、NTFS 等）
- ✅ 文件浏览器功能（支持显示/隐藏文件）

### 📁 文件操作
- ✅ 文本文件写入功能
- ✅ 文件上传到 U 盘（带进度条）
- ✅ 实时显示传输速度
- ✅ 文件删除功能
- ✅ 大文件传输支持

### 🎨 现代化界面
- ✅ Material Design 风格
- ✅ 直观的标签页布局
- ✅ 丰富的视觉反馈
- ✅ 响应式按钮和表格
- ✅ 优雅的颜色搭配

---

## 💻 系统要求

- **操作系统**: macOS 10.13 (High Sierra) 或更高版本
- **Python**: 3.8 或更高版本
- **依赖**: PyQt6 6.4.0 或更高版本

---

## 🚀 快速开始

### 1️⃣ 克隆项目

```bash
git clone <repository-url>
cd usb_monitor
```

### 2️⃣ 创建虚拟环境（推荐）

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 4️⃣ 运行程序

```bash
python3 main.py
```

---

## 📖 使用指南

### USB 设备监控

1. 启动应用程序后，会自动扫描并显示所有 USB 设备
2. 点击 **"🔄 刷新设备列表"** 按钮手动刷新
3. 在表格中查看设备的详细信息：
   - **设备名称**: USB 设备的名称
   - **制造商**: 设备制造商
   - **序列号**: 设备唯一序列号
   - **USB 总线**: 设备所在的 USB 总线
   - **传输速度**: USB 传输速度（如 480 Mb/s）
   - **VID:PID**: 供应商 ID 和产品 ID

### U 盘文件管理

#### 选择 U 盘
1. 切换到 **"💾 U 盘管理"** 标签页
2. 在 U 盘列表中点击选择要操作的 U 盘
3. 文件列表会自动刷新显示该 U 盘的内容

#### 写入文本文件
1. 在 **"✍️ 写入文本文件"** 区域输入文件名
2. 在文本框中输入内容
3. 点击 **"💾 写入文本文件"** 按钮

#### 上传文件
1. 点击 **"📤 上传文件到 U 盘"** 按钮
2. 选择要上传的文件
3. 查看实时进度条和传输速度

#### 删除文件
1. 在文件列表中找到要删除的文件
2. 点击对应的 **"🗑️ 删除"** 按钮
3. 确认删除操作

#### 显示隐藏文件
- 勾选 **"👁️ 显示隐藏文件"** 复选框即可显示以 `.` 开头的隐藏文件

---

## 📁 项目结构

```
usb_monitor/
│
├── main.py                 # 程序入口
├── usb_manager.py          # 原始版本（已重构）
├── requirements.txt        # Python 依赖
├── .gitignore             # Git 忽略文件
│
├── src/                   # 源代码目录
│   ├── __init__.py
│   │
│   ├── core/              # 核心功能模块
│   │   ├── __init__.py
│   │   ├── usb_scanner.py      # USB 设备扫描器
│   │   ├── drive_manager.py    # 存储设备管理器
│   │   └── file_transfer.py    # 文件传输线程
│   │
│   ├── ui/                # 用户界面模块
│   │   ├── __init__.py
│   │   ├── main_window.py      # 主窗口
│   │   └── styles.py           # 样式配置
│   │
│   └── utils/             # 工具函数模块
│       └── __init__.py
│
├── config/                # 配置文件目录
│   └── settings.ini       # 应用配置
│
├── resources/             # 资源文件目录
│   └── (图标、图片等)
│
└── docs/                  # 文档目录
    ├── API.md            # API 文档
    ├── ARCHITECTURE.md   # 架构说明
    └── CHANGELOG.md      # 更新日志
```

### 模块说明

#### `src/core/` - 核心功能模块

- **`usb_scanner.py`**: USB 设备扫描器
  - 使用 `system_profiler` 命令获取 USB 设备信息
  - 递归解析 USB 设备树
  - 提取设备详细信息

- **`drive_manager.py`**: 存储设备管理器
  - 扫描 `/Volumes` 目录下的挂载设备
  - 获取磁盘使用情况
  - 文件列表、读写、删除操作

- **`file_transfer.py`**: 文件传输线程
  - 异步文件传输
  - 实时进度和速度计算
  - 支持取消操作

#### `src/ui/` - 用户界面模块

- **`main_window.py`**: 主窗口界面
  - 标签页布局
  - 表格显示
  - 事件处理

- **`styles.py`**: 样式配置
  - Material Design 风格
  - 颜色主题定义
  - 组件样式表

---

## 🛠️ 技术栈

- **GUI 框架**: PyQt6
- **编程语言**: Python 3.8+
- **系统调用**: 
  - `system_profiler` - USB 设备信息
  - `diskutil` - 磁盘信息
- **设计风格**: Material Design

---

## 🔧 开发说明

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd usb_monitor

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装开发依赖
pip install -r requirements.txt
```

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用类型注解
- 编写详细的文档字符串
- 保持函数简洁，单一职责

### 添加新功能

1. 在相应的模块中添加功能代码
2. 更新文档
3. 编写测试用例
4. 提交 Pull Request

### 自定义样式

编辑 `src/ui/styles.py` 文件中的 `AppStyles` 类来自定义颜色和样式：

```python
# 修改主色调
PRIMARY_COLOR = "#2196F3"  # 蓝色
SECONDARY_COLOR = "#4CAF50"  # 绿色
ACCENT_COLOR = "#FF9800"  # 橙色
```

---

## ❓ 常见问题

### Q1: 程序无法检测到 USB 设备？
**A**: 确保你有权限运行 `system_profiler` 命令。某些安全设置可能会限制访问。

### Q2: 无法读取 U 盘内容？
**A**: 检查 U 盘是否已正确挂载到 `/Volumes` 目录。某些加密的 U 盘可能无法直接访问。

### Q3: 文件传输速度很慢？
**A**: 传输速度取决于 USB 接口版本和 U 盘本身的速度。可以在 `config/settings.ini` 中调整块大小。

### Q4: 如何更改自动刷新间隔？
**A**: 修改 `config/settings.ini` 中的 `auto_refresh_interval` 值（单位：毫秒）。

---

## 📝 更新日志

### Version 1.0.0 (2025-12-25)

#### ✨ 新功能
- 🎉 初始版本发布
- ✅ USB 设备实时监控
- ✅ U 盘文件管理
- ✅ 文件上传下载
- ✅ Material Design 界面

#### 🔧 改进
- 📦 模块化代码结构
- 🎨 美化用户界面
- 📖 完善项目文档

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👨‍💻 作者

**Your Name**

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 🙏 致谢

- PyQt6 团队提供优秀的 GUI 框架
- Material Design 设计规范
- macOS 开发者社区

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star！**

Made with ❤️ on macOS

</div>
