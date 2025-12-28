#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口界面 - 使用 Qt Designer UI 文件
基于 usb_manager.ui 生成，可在 Designer 中可视化编辑
"""

import getpass
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QMessageBox, QPushButton, QHeaderView
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from .usb_manager_ui import Ui_MainWindow
from ..core.usb_scanner import USBScanner
from ..core.drive_manager import DriveManager
from ..core.file_transfer import FileTransferThread
from .styles import AppStyles


class USBManagerWindow(QMainWindow):
    """USB 设备管理器主窗口 - 使用 UI 文件版本"""
    
    def __init__(self):
        super().__init__()
        
        # 加载 UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # 数据
        self.selected_drive = None
        self.transfer_thread = None
        
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
        
        # 隐藏进度相关控件
        self.ui.progressBar.setVisible(False)
        self.ui.speedLabel.setVisible(False)

        # 设置表格列宽自适应 - 让所有表格的列充满宽度
        self.ui.usbTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.drivesTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.filesTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def connect_signals(self):
        """连接信号和槽"""
        self.ui.refreshUsbBtn.clicked.connect(self.scan_usb_devices)
        self.ui.refreshDriveBtn.clicked.connect(self.scan_mounted_drives)
        self.ui.writeTextBtn.clicked.connect(self.write_text_file)
        self.ui.uploadFileBtn.clicked.connect(self.upload_file)
        self.ui.showHiddenCheck.stateChanged.connect(self.refresh_file_list)
        self.ui.drivesTable.itemSelectionChanged.connect(self.on_drive_selected)

    def create_table_item(self, text):
        """创建一个带有工具提示的表格项"""
        item_text = str(text)
        item = QTableWidgetItem(item_text)
        # 设置工具提示，当鼠标悬停时显示完整内容
        item.setToolTip(item_text)
        return item
    
    def scan_usb_devices(self):
        """扫描 USB 设备"""
        self.statusBar().showMessage("🔄 正在扫描 USB 设备...")
        devices = USBScanner.scan_devices()
        
        self.ui.usbTable.setRowCount(len(devices))
        
        for row, device in enumerate(devices):
            self.ui.usbTable.setItem(row, 0, self.create_table_item(device['name']))
            self.ui.usbTable.setItem(row, 1, self.create_table_item(device['manufacturer']))
            self.ui.usbTable.setItem(row, 2, self.create_table_item(device['serial']))
            self.ui.usbTable.setItem(row, 3, self.create_table_item(device['bus']))
            self.ui.usbTable.setItem(row, 4, self.create_table_item(device['speed']))
            self.ui.usbTable.setItem(row, 5, self.create_table_item(device['vid_pid']))
        
        self.statusBar().showMessage(f"✅ 找到 {len(devices)} 个 USB 设备")
    
    def scan_mounted_drives(self):
        """扫描已挂载的驱动器"""
        self.statusBar().showMessage("🔄 正在扫描 U 盘...")
        drives = DriveManager.scan_mounted_drives()
        
        self.ui.drivesTable.setRowCount(len(drives))
        
        for row, drive in enumerate(drives):
            self.ui.drivesTable.setItem(row, 0, self.create_table_item(drive['name']))
            self.ui.drivesTable.setItem(row, 1, self.create_table_item(drive['path']))
            self.ui.drivesTable.setItem(row, 2, self.create_table_item(drive['filesystem']))
            self.ui.drivesTable.setItem(row, 3, self.create_table_item(drive['total']))
            self.ui.drivesTable.setItem(row, 4, self.create_table_item(drive['used']))
            self.ui.drivesTable.setItem(row, 5, self.create_table_item(drive['free']))
        
        self.statusBar().showMessage(f"✅ 找到 {len(drives)} 个存储设备")
    
    def on_drive_selected(self):
        """驱动器选中事件"""
        selected_items = self.ui.drivesTable.selectedItems()
        if selected_items:
            # 获取选中行的信息
            row = selected_items[0].row()
            name = self.ui.drivesTable.item(row, 0).text()
            drive_path = self.ui.drivesTable.item(row, 1).text()
            
            self.selected_drive = drive_path
            self.refresh_file_list()
            
            # 更新界面上的选中状态标签
            status_text = f"📂 当前设备: {name} ({drive_path})"
            self.ui.selectedDriveLabel1.setText(status_text)
            self.ui.selectedDriveLabel2.setText(status_text)
            self.ui.selectedDriveLabel1.setStyleSheet("color: #00695C; font-weight: bold; padding-left: 5px;")
            self.ui.selectedDriveLabel2.setStyleSheet("color: #00695C; font-weight: bold; padding-left: 5px;")
            
            self.statusBar().showMessage(f"📁 已选择: {drive_path}")
        else:
            # 未选中任何设备时重置
            self.selected_drive = None
            self.ui.filesTable.setRowCount(0)
            
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
            
            # 添加删除按钮
            if not file_info['is_dir']:
                delete_btn = QPushButton("🗑️ 删除")
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        
        # 显示进度条
        self.ui.progressBar.setVisible(True)
        self.ui.speedLabel.setVisible(True)
        self.ui.progressBar.setValue(0)
        
        # 创建传输线程
        self.transfer_thread = FileTransferThread(str(source_path), str(dest_path))
        self.transfer_thread.progress.connect(self.update_progress)
        self.transfer_thread.finished.connect(self.transfer_finished)
        self.transfer_thread.start()
        
        self.statusBar().showMessage(f"📤 正在上传: {source_path.name}")
    
    def update_progress(self, progress_percent, speed_text):
        """更新进度和速度"""
        self.ui.progressBar.setValue(progress_percent)
        self.ui.speedLabel.setText(f"传输速度: {speed_text}")
    
    def transfer_finished(self, success, message):
        """传输完成"""
        self.ui.progressBar.setVisible(False)
        self.ui.speedLabel.setVisible(False)
        self.refresh_file_list()
        
        if success:
            QMessageBox.information(self, "成功", message)
            self.statusBar().showMessage(f"✅ {message}")
        else:
            QMessageBox.warning(self, "失败", message)
            self.statusBar().showMessage(f"❌ {message}")
    
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