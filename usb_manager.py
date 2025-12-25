#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB 设备管理器 - macOS 版本 (PyQt6)
支持 USB 设备检测、U 盘文件操作、传输速度显示等功能
"""

import sys
import os
import subprocess
import shutil
import time
import getpass
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                             QTableWidgetItem, QTextEdit, QLineEdit, QFileDialog,
                             QMessageBox, QGroupBox, QCheckBox, QTabWidget,
                             QProgressBar, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor

class FileTransferThread(QThread):
    """文件传输线程"""
    progress = pyqtSignal(int, str)  # 进度和速度
    finished = pyqtSignal(bool, str)  # 成功与否和消息
    
    def __init__(self, source, destination):
        super().__init__()
        self.source = source
        self.destination = destination
        
    def run(self):
        try:
            file_size = os.path.getsize(self.source)
            start_time = time.time()
            
            with open(self.source, 'rb') as src:
                with open(self.destination, 'wb') as dst:
                    copied = 0
                    chunk_size = 1024 * 1024  # 1MB
                    
                    while True:
                        chunk = src.read(chunk_size)
                        if not chunk:
                            break
                        dst.write(chunk)
                        copied += len(chunk)
                        
                        # 计算进度和速度
                        progress = int((copied / file_size) * 100)
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            speed = (copied / elapsed) / (1024 * 1024)  # MB/s
                            self.progress.emit(progress, f"{speed:.2f} MB/s")
                        
            self.finished.emit(True, f"文件上传成功: {os.path.basename(self.source)}")
        except Exception as e:
            self.finished.emit(False, f"文件传输失败: {str(e)}")

class USBManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USB 设备管理器 - macOS")
        self.setGeometry(100, 100, 1400, 900)
        
        # 数据
        self.selected_drive = None
        self.transfer_thread = None
        
        # 创建界面
        self.init_ui()
        
        # 启动定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(3000)  # 每3秒刷新
        
        # 初始加载
        self.refresh_all()
        
    def init_ui(self):
        """初始化界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题栏
        self.create_header(main_layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # USB 设备标签页
        usb_tab = QWidget()
        usb_layout = QVBoxLayout(usb_tab)
        self.create_usb_devices_section(usb_layout)
        tab_widget.addTab(usb_tab, "🔌 USB 设备")
        
        # U 盘管理标签页
        drive_tab = QWidget()
        drive_layout = QVBoxLayout(drive_tab)
        self.create_drive_management_section(drive_layout)
        tab_widget.addTab(drive_tab, "💾 U 盘管理")
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def create_header(self, layout):
        """创建标题栏"""
        header_frame = QWidget()
        header_frame.setStyleSheet("background-color: #2196F3; border-radius: 10px; padding: 15px;")
        header_layout = QHBoxLayout(header_frame)
        
        # 标题
        title_label = QLabel("🔌 USB 设备管理器")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 用户信息
        user_label = QLabel(f"👤 当前用户: {getpass.getuser()}")
        user_label.setStyleSheet("color: white; font-size: 14px; background-color: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 5px;")
        header_layout.addWidget(user_label)
        
        layout.addWidget(header_frame)
        
    def create_usb_devices_section(self, layout):
        """创建 USB 设备区域"""
        # 刷新按钮
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 刷新设备列表")
        refresh_btn.clicked.connect(self.scan_usb_devices)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # USB 设备表格
        self.usb_table = QTableWidget()
        self.usb_table.setColumnCount(6)
        self.usb_table.setHorizontalHeaderLabels([
            "设备名称", "制造商", "序列号", "USB 总线", "传输速度", "VID:PID"
        ])
        self.usb_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.usb_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.usb_table)
        
    def create_drive_management_section(self, layout):
        """创建 U 盘管理区域"""
        # 上半部分：U 盘列表
        drives_group = QGroupBox("📀 已挂载的 U 盘")
        drives_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        drives_layout = QVBoxLayout()
        
        # 刷新按钮
        btn_layout = QHBoxLayout()
        refresh_drive_btn = QPushButton("🔄 刷新 U 盘列表")
        refresh_drive_btn.clicked.connect(self.scan_mounted_drives)
        refresh_drive_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        btn_layout.addWidget(refresh_drive_btn)
        btn_layout.addStretch()
        drives_layout.addLayout(btn_layout)
        
        # U 盘列表表格
        self.drives_table = QTableWidget()
        self.drives_table.setColumnCount(6)
        self.drives_table.setHorizontalHeaderLabels([
            "设备名称", "挂载路径", "文件系统", "总容量", "已使用", "可用空间"
        ])
        self.drives_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.drives_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.drives_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.drives_table.itemSelectionChanged.connect(self.on_drive_selected)
        self.drives_table.setMaximumHeight(200)
        drives_layout.addWidget(self.drives_table)
        
        drives_group.setLayout(drives_layout)
        layout.addWidget(drives_group)
        
        # 文件操作区域
        file_ops_group = QGroupBox("📝 文件操作")
        file_ops_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        file_ops_layout = QVBoxLayout()
        
        # 写入文本文件
        text_write_group = QGroupBox("✍️ 写入文本文件")
        text_write_layout = QVBoxLayout()
        
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("文件名:"))
        self.filename_input = QLineEdit("test.txt")
        filename_layout.addWidget(self.filename_input)
        text_write_layout.addLayout(filename_layout)
        
        self.text_content = QTextEdit()
        self.text_content.setPlaceholderText("输入要写入的文本内容...")
        self.text_content.setMaximumHeight(100)
        text_write_layout.addWidget(self.text_content)
        
        write_btn = QPushButton("💾 写入文本文件")
        write_btn.clicked.connect(self.write_text_file)
        write_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        text_write_layout.addWidget(write_btn)
        
        text_write_group.setLayout(text_write_layout)
        file_ops_layout.addWidget(text_write_group)
        
        # 文件上传
        upload_layout = QHBoxLayout()
        upload_btn = QPushButton("📤 上传文件到 U 盘")
        upload_btn.clicked.connect(self.upload_file)
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        upload_layout.addWidget(upload_btn)
        
        self.show_hidden_check = QCheckBox("显示隐藏文件")
        self.show_hidden_check.stateChanged.connect(self.refresh_file_list)
        upload_layout.addWidget(self.show_hidden_check)
        
        upload_layout.addStretch()
        file_ops_layout.addLayout(upload_layout)
        
        # 传输进度
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.speed_label = QLabel("传输速度: 0 MB/s")
        self.speed_label.setVisible(False)
        self.speed_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        progress_layout.addWidget(self.speed_label)
        
        file_ops_layout.addLayout(progress_layout)
        
        file_ops_group.setLayout(file_ops_layout)
        layout.addWidget(file_ops_group)
        
        # 文件列表
        files_group = QGroupBox("📂 文件列表")
        files_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        files_layout = QVBoxLayout()
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels([
            "文件名", "类型", "大小", "操作"
        ])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        files_layout.addWidget(self.files_table)
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
    def scan_usb_devices(self):
        """扫描 USB 设备"""
        self.statusBar().showMessage("正在扫描 USB 设备...")
        
        try:
            # 使用 system_profiler 获取 USB 设备信息
            result = subprocess.run(
                ['system_profiler', 'SPUSBDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                devices = []
                
                # 解析 USB 设备
                def parse_usb_items(items, bus_name="USB"):
                    for item in items:
                        device_info = {
                            'name': item.get('_name', 'Unknown Device'),
                            'manufacturer': item.get('manufacturer', 'N/A'),
                            'serial': item.get('serial_num', 'N/A'),
                            'bus': bus_name,
                            'speed': item.get('device_speed', 'N/A'),
                            'vid_pid': f"{item.get('vendor_id', 'N/A')}:{item.get('product_id', 'N/A')}"
                        }
                        devices.append(device_info)
                        
                        # 递归解析子设备
                        if '_items' in item:
                            parse_usb_items(item['_items'], item.get('_name', bus_name))
                
                if 'SPUSBDataType' in data:
                    for bus in data['SPUSBDataType']:
                        if '_items' in bus:
                            parse_usb_items(bus['_items'], bus.get('_name', 'USB'))
                
                # 更新表格
                self.usb_table.setRowCount(len(devices))
                for i, device in enumerate(devices):
                    self.usb_table.setItem(i, 0, QTableWidgetItem(device['name']))
                    self.usb_table.setItem(i, 1, QTableWidgetItem(device['manufacturer']))
                    self.usb_table.setItem(i, 2, QTableWidgetItem(device['serial']))
                    self.usb_table.setItem(i, 3, QTableWidgetItem(device['bus']))
                    self.usb_table.setItem(i, 4, QTableWidgetItem(device['speed']))
                    self.usb_table.setItem(i, 5, QTableWidgetItem(device['vid_pid']))
                
                self.statusBar().showMessage(f"已找到 {len(devices)} 个 USB 设备")
            else:
                self.statusBar().showMessage("扫描 USB 设备失败")
                
        except Exception as e:
            self.statusBar().showMessage(f"扫描 USB 设备出错: {str(e)}")
            
    def scan_mounted_drives(self):
        """扫描已挂载的 U 盘"""
        self.statusBar().showMessage("正在扫描 U 盘...")
        
        try:
            # 获取所有挂载的卷
            volumes_path = Path('/Volumes')
            drives = []
            
            for volume in volumes_path.iterdir():
                if volume.name == 'Macintosh HD' or volume.name.startswith('.'):
                    continue
                    
                if volume.is_dir():
                    # 获取磁盘使用情况
                    try:
                        stat = shutil.disk_usage(str(volume))
                        total_gb = stat.total / (1024**3)
                        used_gb = stat.used / (1024**3)
                        free_gb = stat.free / (1024**3)
                        
                        # 获取文件系统类型
                        result = subprocess.run(
                            ['diskutil', 'info', str(volume)],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        filesystem = "Unknown"
                        if result.returncode == 0:
                            for line in result.stdout.split('\n'):
                                if 'File System Personality' in line or 'Type (Bundle)' in line:
                                    filesystem = line.split(':')[-1].strip()
                                    break
                        
                        drives.append({
                            'name': volume.name,
                            'path': str(volume),
                            'filesystem': filesystem,
                            'total': f"{total_gb:.2f} GB",
                            'used': f"{used_gb:.2f} GB",
                            'free': f"{free_gb:.2f} GB"
                        })
                    except:
                        continue
            
            # 更新表格
            self.drives_table.setRowCount(len(drives))
            for i, drive in enumerate(drives):
                self.drives_table.setItem(i, 0, QTableWidgetItem(drive['name']))
                self.drives_table.setItem(i, 1, QTableWidgetItem(drive['path']))
                self.drives_table.setItem(i, 2, QTableWidgetItem(drive['filesystem']))
                self.drives_table.setItem(i, 3, QTableWidgetItem(drive['total']))
                self.drives_table.setItem(i, 4, QTableWidgetItem(drive['used']))
                self.drives_table.setItem(i, 5, QTableWidgetItem(drive['free']))
            
            self.statusBar().showMessage(f"已找到 {len(drives)} 个 U 盘")
            
        except Exception as e:
            self.statusBar().showMessage(f"扫描 U 盘出错: {str(e)}")
            
    def on_drive_selected(self):
        """选择 U 盘"""
        selected_rows = self.drives_table.selectedItems()
        if selected_rows:
            row = self.drives_table.currentRow()
            self.selected_drive = self.drives_table.item(row, 1).text()
            self.statusBar().showMessage(f"已选择: {self.selected_drive}")
            self.refresh_file_list()
            
    def refresh_file_list(self):
        """刷新文件列表"""
        if not self.selected_drive:
            self.files_table.setRowCount(0)
            return
            
        try:
            path = Path(self.selected_drive)
            files = []
            
            for item in path.iterdir():
                if not self.show_hidden_check.isChecked() and item.name.startswith('.'):
                    continue
                    
                file_type = "📁 文件夹" if item.is_dir() else "📄 文件"
                size = "N/A"
                
                if item.is_file():
                    size_bytes = item.stat().st_size
                    if size_bytes < 1024:
                        size = f"{size_bytes} B"
                    elif size_bytes < 1024**2:
                        size = f"{size_bytes/1024:.2f} KB"
                    elif size_bytes < 1024**3:
                        size = f"{size_bytes/(1024**2):.2f} MB"
                    else:
                        size = f"{size_bytes/(1024**3):.2f} GB"
                
                files.append({
                    'name': item.name,
                    'type': file_type,
                    'size': size,
                    'path': str(item)
                })
            
            # 更新表格
            self.files_table.setRowCount(len(files))
            for i, file in enumerate(files):
                self.files_table.setItem(i, 0, QTableWidgetItem(file['name']))
                self.files_table.setItem(i, 1, QTableWidgetItem(file['type']))
                self.files_table.setItem(i, 2, QTableWidgetItem(file['size']))
                
                # 添加删除按钮
                if "📄" in file['type']:
                    delete_btn = QPushButton("🗑️ 删除")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f44336;
                            color: white;
                            border: none;
                            border-radius: 3px;
                            padding: 5px 10px;
                        }
                        QPushButton:hover {
                            background-color: #da190b;
                        }
                    """)
                    delete_btn.clicked.connect(lambda checked, p=file['path']: self.delete_file(p))
                    self.files_table.setCellWidget(i, 3, delete_btn)
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取文件列表失败: {str(e)}")
            
    def write_text_file(self):
        """写入文本文件"""
        if not self.selected_drive:
            QMessageBox.warning(self, "提示", "请先选择一个 U 盘")
            return
            
        filename = self.filename_input.text().strip()
        content = self.text_content.toPlainText()
        
        if not filename:
            QMessageBox.warning(self, "提示", "请输入文件名")
            return
            
        if not content:
            QMessageBox.warning(self, "提示", "请输入文本内容")
            return
            
        try:
            file_path = Path(self.selected_drive) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            QMessageBox.information(self, "成功", f"文件已写入: {filename}")
            self.text_content.clear()
            self.refresh_file_list()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"写入文件失败: {str(e)}")
            
    def upload_file(self):
        """上传文件"""
        if not self.selected_drive:
            QMessageBox.warning(self, "提示", "请先选择一个 U 盘")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if not file_path:
            return
            
        destination = Path(self.selected_drive) / Path(file_path).name
        
        # 显示进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.speed_label.setVisible(True)
        
        # 创建传输线程
        self.transfer_thread = FileTransferThread(file_path, str(destination))
        self.transfer_thread.progress.connect(self.update_transfer_progress)
        self.transfer_thread.finished.connect(self.transfer_finished)
        self.transfer_thread.start()
        
    def update_transfer_progress(self, progress, speed):
        """更新传输进度"""
        self.progress_bar.setValue(progress)
        self.speed_label.setText(f"传输速度: {speed}")
        
    def transfer_finished(self, success, message):
        """传输完成"""
        self.progress_bar.setVisible(False)
        self.speed_label.setVisible(False)
        
        if success:
            QMessageBox.information(self, "成功", message)
            self.refresh_file_list()
        else:
            QMessageBox.critical(self, "错误", message)
            
    def delete_file(self, file_path):
        """删除文件"""
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除文件吗?\n{Path(file_path).name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(file_path)
                QMessageBox.information(self, "成功", "文件已删除")
                self.refresh_file_list()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除文件失败: {str(e)}")
                
    def auto_refresh(self):
        """自动刷新"""
        self.scan_mounted_drives()
        
    def refresh_all(self):
        """刷新所有数据"""
        self.scan_usb_devices()
        self.scan_mounted_drives()

def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = USBManagerWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()