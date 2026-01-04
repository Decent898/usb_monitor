#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口界面 - 使用 Qt Designer UI 文件
基于 usb_manager.ui 生成，可在 Designer 中可视化编辑
"""

import getpass
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QTableWidgetItem, QFileDialog, QMessageBox, 
    QPushButton, QHeaderView, QWidget, QHBoxLayout, QLabel, QInputDialog, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from .usb_manager_ui import Ui_MainWindow
from ..core.usb_scanner import USBScanner
from ..core.drive_manager import DriveManager
from ..core.file_transfer import FileTransferThread
from ..core.speed_tester import SpeedTestThread
from .styles import AppStyles


class USBManagerWindow(QMainWindow):
    """USB 设备管理器主窗口 - 使用 UI 文件版本"""
    
    def __init__(self):
        super().__init__()
        
        # 加载 UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # --- 新增：UI 动态优化 ---
        
        # 1. 在 USB 刷新按钮旁添加加载提示标签
        self.usbLoadingLabel = QLabel("⏳ 正在扫描硬件信息...")
        self.usbLoadingLabel.setStyleSheet("color: #E65100; font-weight: bold; margin-left: 10px;")
        self.usbLoadingLabel.setVisible(False)
        # 将标签插入到按钮和弹簧之间 (index 1)
        self.ui.horizontalLayout_2.insertWidget(1, self.usbLoadingLabel)
        
        # 2. 在 U盘刷新按钮旁添加加载提示标签
        self.driveLoadingLabel = QLabel("⏳ 正在读取磁盘信息...")
        self.driveLoadingLabel.setStyleSheet("color: #E65100; font-weight: bold; margin-left: 10px;")
        self.driveLoadingLabel.setVisible(False)
        self.ui.horizontalLayout_3.insertWidget(1, self.driveLoadingLabel)

        # 3. 手动添加取消按钮 (用于文件传输)
        self.cancelBtn = QPushButton("✖ 取消")
        self.cancelBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancelBtn.setVisible(False)  # 默认隐藏
        self.cancelBtn.setFixedSize(80, 30)
        # 将按钮添加到进度条布局中 (horizontalLayout_6 包含 progressBar 和 speedLabel)
        self.ui.horizontalLayout_6.addWidget(self.cancelBtn)
        
        # 数据
        self.selected_drive = None
        self.transfer_thread = None
        self.speed_test_thread = None  # 测速线程
        self.speed_test_results = {}   # 新增：用于存储测速结果 {device_key: result_text}
        
        # 应用样式
        self.apply_styles()
        
        # 连接信号
        self.connect_signals()
        
        # 更新用户信息
        self.ui.userLabel.setText(f"👤 用户: {getpass.getuser()}")
        
        # 启动定时器 - Windows上改为10秒，避免卡顿
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000)  # 每10秒刷新（避免频繁扫描导致卡顿）
        
        # 初始加载
        self.refresh_all()
    
    def apply_styles(self):
        """应用最小样式 - 只设置必要的功能，保持 UI 文件原样"""
        # 更新用户标签文字颜色使其在标题栏中可见
        self.ui.headerWidget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {AppStyles.PRIMARY_COLOR},
                    stop:1 {AppStyles.PRIMARY_LIGHT});
                border-radius: 12px;
            }}
            QLabel {{
                color: white;
                background: transparent;
            }}
        """)
        
        # 设置按钮鼠标样式
        self.ui.refreshUsbBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.refreshDriveBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.writeTextBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.uploadFileBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置取消按钮样式 (使用危险色)
        self.cancelBtn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #B71C1C; }
            QPushButton:disabled { background-color: #E0E0E0; color: #9E9E9E; }
        """)
        
        # 隐藏进度相关控件
        self.ui.progressBar.setVisible(False)
        self.ui.speedLabel.setVisible(False)

        # --- 优化表格列宽设置 ---
        
        # 1. USB 设备表
        usb_header = self.ui.usbTable.horizontalHeader()
        # 设置为交互模式，允许用户手动拖动列宽
        usb_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # 让最后一列自动填充剩余空间
        usb_header.setStretchLastSection(True)
        
        # 设置特定列的初始宽度
        self.ui.usbTable.setColumnWidth(0, 200)  # 设备名称
        self.ui.usbTable.setColumnWidth(1, 150)  # 制造商
        self.ui.usbTable.setColumnWidth(2, 120)  # 序列号
        self.ui.usbTable.setColumnWidth(3, 100)  # 总线
        self.ui.usbTable.setColumnWidth(4, 350)  # 传输速度 (增加宽度以容纳长文本)
        self.ui.usbTable.setColumnWidth(5, 120)  # VID:PID

        # 2. U盘列表
        drive_header = self.ui.drivesTable.horizontalHeader()
        drive_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        drive_header.setStretchLastSection(True)
        self.ui.drivesTable.setColumnWidth(0, 200) # 设备名称
        
        # 3. 文件列表
        file_header = self.ui.filesTable.horizontalHeader()
        file_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # 文件名自动拉伸
        file_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        file_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        file_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        
        self.ui.filesTable.setColumnWidth(1, 120)  # 类型
        self.ui.filesTable.setColumnWidth(2, 100)  # 大小
        self.ui.filesTable.setColumnWidth(3, 100)  # 操作
    
    def connect_signals(self):
        """连接信号和槽"""
        self.ui.refreshUsbBtn.clicked.connect(self.scan_usb_devices)
        self.ui.refreshDriveBtn.clicked.connect(self.scan_mounted_drives)
        self.ui.writeTextBtn.clicked.connect(self.write_text_file)
        self.ui.uploadFileBtn.clicked.connect(self.upload_file)
        self.ui.showHiddenCheck.stateChanged.connect(self.refresh_file_list)
        self.ui.drivesTable.itemSelectionChanged.connect(self.on_drive_selected)
        
        # 连接取消按钮
        self.cancelBtn.clicked.connect(self.cancel_transfer)

    def create_table_item(self, text):
        """创建一个带有工具提示的表格项"""
        item_text = str(text) if text else ""
        item = QTableWidgetItem(item_text)
        # 设置工具提示，当鼠标悬停时显示完整内容
        item.setToolTip(item_text)
        return item
    
    def create_speed_test_widget(self, initial_text, device_info, device_key):
        """
        创建包含 '文本 + 按钮' 的自定义 Widget
        用于 USB 传输速度列
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # 显示速度的标签
        label = QLabel(initial_text)
        label.setToolTip(initial_text)
        
        # 测速按钮
        btn = QPushButton("🚀 测速")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(60, 24)
        # 简单样式
        btn.setStyleSheet("""
            QPushButton {
                background-color: #00897B; 
                color: white; 
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #00695C; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        
        # 连接点击事件
        btn.clicked.connect(lambda: self.start_speed_test(device_info, label, btn, device_key))
        
        layout.addWidget(label)
        layout.addWidget(btn)
        
        # 让 Label 占据剩余空间
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)
        
        return widget

    def scan_usb_devices(self):
        """扫描 USB 设备"""
        # 1. UI 状态：开始扫描
        self.ui.refreshUsbBtn.setEnabled(False)
        self.usbLoadingLabel.setVisible(True)
        self.statusBar().showMessage("🔄 正在扫描 USB 设备，这可能需要几秒钟...")
        
        # 强制刷新 UI 事件循环，确保 Loading 提示立即显示
        QApplication.processEvents()
        
        try:
            # 2. 执行扫描
            devices = USBScanner.scan_devices()
            
            # 3. 更新表格
            self.ui.usbTable.setRowCount(len(devices))
            
            for row, device in enumerate(devices):
                self.ui.usbTable.setItem(row, 0, self.create_table_item(device['name']))
                self.ui.usbTable.setItem(row, 1, self.create_table_item(device['manufacturer']))
                self.ui.usbTable.setItem(row, 2, self.create_table_item(device['serial']))
                self.ui.usbTable.setItem(row, 3, self.create_table_item(device['bus']))
                
                # 移除当前单元格的旧 Widget
                self.ui.usbTable.removeCellWidget(row, 4)
                
                # 生成唯一的设备 Key
                serial = device.get('serial', 'N/A')
                if serial and serial != 'N/A':
                    device_key = serial
                else:
                    device_key = f"{device['name']}_{device['vid_pid']}"
                
                # 如果是存储设备，显示测速按钮
                device_name_lower = device['name'].lower()
                is_storage_device = (device['bus'] == 'USB Storage' or 'Storage' in device['bus'] or
                                   any(keyword in device_name_lower for keyword in ['mass storage', 'disk', 'storage', 'flash', 'card reader']))
                
                if is_storage_device:
                    # 检查是否有历史测速结果
                    display_text = self.speed_test_results.get(device_key, device['speed'])
                    speed_widget = self.create_speed_test_widget(display_text, device, device_key)
                    self.ui.usbTable.setCellWidget(row, 4, speed_widget)
                    
                    # 显式设置一个空的 Item，清除底层可能存在的文本
                    self.ui.usbTable.setItem(row, 4, QTableWidgetItem(""))
                else:
                    # 普通设备只显示文本
                    self.ui.usbTable.setItem(row, 4, self.create_table_item(device['speed']))
                
                self.ui.usbTable.setItem(row, 5, self.create_table_item(device['vid_pid']))
            
            # 4. 完成状态提示
            msg = f"✅ 刷新完成: 找到 {len(devices)} 个 USB 设备"
            self.statusBar().showMessage(msg)
            
        finally:
            # 5. UI 状态：恢复
            self.usbLoadingLabel.setVisible(False)
            self.ui.refreshUsbBtn.setEnabled(True)
    
    def start_speed_test(self, device_info, label_widget, btn_widget, device_key):
        """开始测速流程"""
        self.timer.stop()
        
        try:
            mounted_drives = DriveManager.scan_mounted_drives()
            
            if not mounted_drives:
                QMessageBox.warning(self, "无法测速", "未检测到已挂载的 U 盘卷。\n请确保 U 盘已正确格式化并分配了盘符。")
                self.timer.start(10000)
                return

            target_path = None
            
            if len(mounted_drives) == 1:
                drive = mounted_drives[0]
                reply = QMessageBox.question(
                    self, "确认测速目标", 
                    f"准备对以下磁盘进行测速，是否继续？\n\n名称: {drive['name']}\n路径: {drive['path']}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    target_path = drive['path']
                else:
                    self.timer.start(10000)
                    return
            else:
                drive_names = [f"{d['name']} ({d['path']})" for d in mounted_drives]
                item, ok = QInputDialog.getItem(
                    self, "选择测速目标", 
                    f"检测到多个 U 盘，请选择对应 '{device_info['name']}' 的挂载路径:", 
                    drive_names, 0, False
                )
                if ok and item:
                    selected_idx = drive_names.index(item)
                    target_path = mounted_drives[selected_idx]['path']
                else:
                    self.timer.start(10000)
                    return

            if not target_path:
                self.timer.start(10000)
                return

            try:
                original_text = label_widget.text()
                btn_widget.setEnabled(False)
                btn_widget.setText("测试中...")
                label_widget.setText("准备中...")
            except RuntimeError:
                self.timer.start(10000)
                return
            
            self.speed_test_thread = SpeedTestThread(target_path)
            
            def on_progress(status, percent):
                try:
                    label_widget.setText(status)
                except RuntimeError:
                    pass 
            
            def on_finished(result_text):
                try:
                    label_widget.setText(result_text)
                    label_widget.setToolTip(result_text)
                    btn_widget.setText("🚀 测速")
                    btn_widget.setEnabled(True)
                    self.speed_test_results[device_key] = result_text
                    QMessageBox.information(self, "测速完成", f"设备: {device_info['name']}\n{result_text}")
                except RuntimeError:
                    pass
                finally:
                    self.timer.start(10000)
            
            def on_error(err_msg):
                try:
                    label_widget.setText("测试失败")
                    btn_widget.setText("重试")
                    btn_widget.setEnabled(True)
                    QMessageBox.critical(self, "测速失败", err_msg)
                except RuntimeError:
                    pass
                finally:
                    self.timer.start(10000)

            self.speed_test_thread.progress_update.connect(on_progress)
            self.speed_test_thread.test_finished.connect(on_finished)
            self.speed_test_thread.error_occurred.connect(on_error)
            
            self.speed_test_thread.start()
            
        except Exception as e:
            print(f"Error starting speed test: {e}")
            self.timer.start(10000)

    def scan_mounted_drives(self):
        """扫描已挂载的驱动器"""
        # 1. UI 状态：开始扫描
        self.ui.refreshDriveBtn.setEnabled(False)
        self.driveLoadingLabel.setVisible(True)
        self.statusBar().showMessage("🔄 正在读取磁盘信息...")
        QApplication.processEvents()
        
        try:
            drives = DriveManager.scan_mounted_drives()
            
            self.ui.drivesTable.setRowCount(len(drives))
            
            for row, drive in enumerate(drives):
                # 获取驱动器信息，如果为空则显示默认值
                name = drive['name'] if drive['name'] else "未知设备"
                fs = drive['filesystem'] if drive['filesystem'] else "未知"
                
                self.ui.drivesTable.setItem(row, 0, self.create_table_item(name))
                self.ui.drivesTable.setItem(row, 1, self.create_table_item(drive['path']))
                self.ui.drivesTable.setItem(row, 2, self.create_table_item(fs))
                self.ui.drivesTable.setItem(row, 3, self.create_table_item(drive['total']))
                self.ui.drivesTable.setItem(row, 4, self.create_table_item(drive['used']))
                self.ui.drivesTable.setItem(row, 5, self.create_table_item(drive['free']))
            
            # 4. 完成状态提示
            msg = f"✅ 刷新完成: 找到 {len(drives)} 个存储卷"
            self.statusBar().showMessage(msg)
            
        finally:
            # 5. UI 状态：恢复
            self.driveLoadingLabel.setVisible(False)
            self.ui.refreshDriveBtn.setEnabled(True)
    
    def on_drive_selected(self):
        """驱动器选中事件"""
        selected_items = self.ui.drivesTable.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            name = self.ui.drivesTable.item(row, 0).text()
            drive_path = self.ui.drivesTable.item(row, 1).text()
            
            self.selected_drive = drive_path
            self.refresh_file_list()
            
            if hasattr(self.ui, 'selectedDriveLabel1'):
                status_text = f"📂 当前设备: {name} ({drive_path})"
                self.ui.selectedDriveLabel1.setText(status_text)
                self.ui.selectedDriveLabel2.setText(status_text)
                self.ui.selectedDriveLabel1.setStyleSheet("color: #00695C; font-weight: bold; padding-left: 5px;")
                self.ui.selectedDriveLabel2.setStyleSheet("color: #00695C; font-weight: bold; padding-left: 5px;")
            
            self.statusBar().showMessage(f"📁 已选择: {drive_path}")
        else:
            self.selected_drive = None
            self.ui.filesTable.setRowCount(0)
            
            if hasattr(self.ui, 'selectedDriveLabel1'):
                reset_text = "当前设备: 未选择"
                self.ui.selectedDriveLabel1.setText(reset_text)
                self.ui.selectedDriveLabel2.setText(reset_text)
                self.ui.selectedDriveLabel1.setStyleSheet("color: #666; font-weight: bold; padding-left: 5px;")
                self.ui.selectedDriveLabel2.setStyleSheet("color: #666; font-weight: bold; padding-left: 5px;")
    
    def refresh_file_list(self):
        """刷新文件列表"""
        if not self.selected_drive:
            return
        
        show_hidden = self.ui.showHiddenCheck.isChecked()
        files = DriveManager.list_files(self.selected_drive, show_hidden)
        
        self.ui.filesTable.setRowCount(len(files))
        
        for row, file_info in enumerate(files):
            self.ui.filesTable.setItem(row, 0, self.create_table_item(file_info['name']))
            self.ui.filesTable.setItem(row, 1, self.create_table_item(file_info['type']))
            self.ui.filesTable.setItem(row, 2, self.create_table_item(file_info['size']))
            
            # 无论是不是文件，都先移除可能存在的旧按钮
            self.ui.filesTable.removeCellWidget(row, 3)
            
            if not file_info['is_dir']:
                delete_btn = QPushButton("🗑️ 删除")
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                # 使用 lambda 参数默认值 path=file_info['path'] 确保绑定的是当前循环的文件路径
                delete_btn.clicked.connect(lambda checked, path=file_info['path']: self.delete_file(path))
                self.ui.filesTable.setCellWidget(row, 3, delete_btn)
    
    def write_text_file(self):
        """写入文本文件"""
        if not self.selected_drive:
            QMessageBox.warning(self, "警告", "请先选择一个 U 盘")
            return
        
        filename = self.ui.filenameInput.text()
        content = self.ui.textContent.toPlainText()
        
        if not filename:
            QMessageBox.warning(self, "警告", "请输入文件名")
            return
        
        if DriveManager.write_text_file(self.selected_drive, filename, content):
            QMessageBox.information(self, "成功", f"文件 '{filename}' 写入成功！")
            self.refresh_file_list()
            self.statusBar().showMessage(f"✅ 文件 '{filename}' 写入成功")
        else:
            QMessageBox.critical(self, "错误", "文件写入失败")
            self.statusBar().showMessage("❌ 文件写入失败")
    
    def upload_file(self):
        """上传文件到 U 盘"""
        if not self.selected_drive:
            QMessageBox.warning(self, "警告", "请先选择一个 U 盘")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要上传的文件", "", "所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        source_path = Path(file_path)
        dest_path = Path(self.selected_drive) / source_path.name
        
        # 显示进度条和取消按钮
        self.ui.progressBar.setVisible(True)
        self.ui.speedLabel.setVisible(True)
        self.cancelBtn.setVisible(True)
        self.cancelBtn.setEnabled(True)
        self.cancelBtn.setText("✖ 取消")
        self.ui.progressBar.setValue(0)
        
        # 禁用上传按钮防止重复操作
        self.ui.uploadFileBtn.setEnabled(False)
        
        # 创建传输线程
        self.transfer_thread = FileTransferThread(str(source_path), str(dest_path))
        self.transfer_thread.progress.connect(self.update_progress)
        self.transfer_thread.finished.connect(self.transfer_finished)
        self.transfer_thread.start()
        
        self.statusBar().showMessage(f"📤 正在上传: {source_path.name}")
    
    def cancel_transfer(self):
        """取消当前传输"""
        if self.transfer_thread and self.transfer_thread.isRunning():
            self.cancelBtn.setText("正在停止...")
            self.cancelBtn.setEnabled(False)
            self.transfer_thread.cancel()
            self.statusBar().showMessage("正在取消传输...")

    def update_progress(self, value, speed):
        """更新进度"""
        self.ui.progressBar.setValue(value)
        self.ui.speedLabel.setText(f"传输速度: {speed}")
    
    def transfer_finished(self, success, message):
        """传输完成"""
        self.ui.progressBar.setVisible(False)
        self.ui.speedLabel.setVisible(False)
        self.cancelBtn.setVisible(False)
        self.ui.uploadFileBtn.setEnabled(True)
        
        if success:
            self.refresh_file_list()
            QMessageBox.information(self, "成功", "文件上传成功！")
            self.statusBar().showMessage("✅ 文件上传成功")
        else:
            # 如果是用户取消的，提示不同
            if "取消" in message:
                self.statusBar().showMessage(f"⚠️ {message}")
                QMessageBox.information(self, "已取消", "文件传输已取消")
            else:
                QMessageBox.critical(self, "错误", f"文件上传失败: {message}")
                self.statusBar().showMessage(f"❌ 上传失败: {message}")
            self.refresh_file_list() # 刷新以移除可能残留的部分文件
    
    def delete_file(self, file_path):
        """删除文件"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除文件吗？\n{file_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if DriveManager.delete_file(file_path):
                self.refresh_file_list()
                self.statusBar().showMessage(f"✅ 文件已删除: {Path(file_path).name}")
            else:
                QMessageBox.critical(self, "错误", "文件删除失败")
                self.statusBar().showMessage("❌ 文件删除失败")
    
    def auto_refresh(self):
        """自动刷新"""
        # 如果当前在 USB 设备标签页，刷新 USB 设备
        if self.ui.tabWidget.currentIndex() == 0:
            self.scan_usb_devices()
    
    def refresh_all(self):
        """刷新所有数据"""
        self.scan_usb_devices()
        self.scan_mounted_drives()