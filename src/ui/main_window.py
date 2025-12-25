#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口界面
USB 设备管理器的主界面
"""

import getpass
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
    QLineEdit, QFileDialog, QMessageBox, QGroupBox, QCheckBox,
    QTabWidget, QProgressBar, QHeaderView, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from ..core.usb_scanner import USBScanner
from ..core.drive_manager import DriveManager
from ..core.file_transfer import FileTransferThread
from .styles import AppStyles


class USBManagerWindow(QMainWindow):
    """USB 设备管理器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔌 USB 设备管理器 - macOS")
        self.setGeometry(100, 100, 1500, 950)
        
        # 数据
        self.selected_drive = None
        self.transfer_thread = None
        
        # 应用全局样式
        self.setStyleSheet(AppStyles.get_main_window_style())
        
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
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题栏
        self.create_header(main_layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(AppStyles.get_tab_widget_style())
        main_layout.addWidget(tab_widget)
        
        # USB 设备标签页
        usb_tab = QWidget()
        usb_layout = QVBoxLayout(usb_tab)
        usb_layout.setContentsMargins(10, 10, 10, 10)
        self.create_usb_devices_section(usb_layout)
        tab_widget.addTab(usb_tab, "🔌 USB 设备")
        
        # U 盘管理标签页
        drive_tab = QWidget()
        drive_layout = QVBoxLayout(drive_tab)
        drive_layout.setContentsMargins(10, 10, 10, 10)
        self.create_drive_management_section(drive_layout)
        tab_widget.addTab(drive_tab, "💾 U 盘管理")
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("🟢 就绪")
    
    def create_header(self, layout):
        """创建标题栏"""
        header_frame = QWidget()
        header_frame.setStyleSheet(AppStyles.get_header_style())
        header_layout = QHBoxLayout(header_frame)
        
        # 标题
        title_label = QLabel("🔌 USB 设备管理器")
        title_font = QFont()
        title_font.setPointSize(26)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 用户信息
        user_label = QLabel(f"👤 用户: {getpass.getuser()}")
        user_label.setStyleSheet(AppStyles.get_user_badge_style())
        header_layout.addWidget(user_label)
        
        layout.addWidget(header_frame)
    
    def create_usb_devices_section(self, layout):
        """创建 USB 设备区域"""
        # 刷新按钮
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 刷新设备列表")
        refresh_btn.clicked.connect(self.scan_usb_devices)
        refresh_btn.setStyleSheet(AppStyles.get_primary_button_style())
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.usb_table.setStyleSheet(AppStyles.get_table_style())
        self.usb_table.setAlternatingRowColors(True)
        layout.addWidget(self.usb_table)
    
    def create_drive_management_section(self, layout):
        """创建 U 盘管理区域"""
        # U 盘列表
        drives_group = QGroupBox("📀 已挂载的 U 盘")
        drives_group.setStyleSheet(AppStyles.get_group_box_style())
        drives_layout = QVBoxLayout()
        
        # 刷新按钮
        btn_layout = QHBoxLayout()
        refresh_drive_btn = QPushButton("🔄 刷新 U 盘列表")
        refresh_drive_btn.clicked.connect(self.scan_mounted_drives)
        refresh_drive_btn.setStyleSheet(AppStyles.get_secondary_button_style())
        refresh_drive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.drives_table.setStyleSheet(AppStyles.get_table_style())
        self.drives_table.setAlternatingRowColors(True)
        drives_layout.addWidget(self.drives_table)
        
        drives_group.setLayout(drives_layout)
        layout.addWidget(drives_group)
        
        # 文件操作区域
        file_ops_group = QGroupBox("📝 文件操作")
        file_ops_group.setStyleSheet(AppStyles.get_group_box_style())
        file_ops_layout = QVBoxLayout()
        
        # 写入文本文件
        text_write_group = QGroupBox("✍️ 写入文本文件")
        text_write_group.setStyleSheet(AppStyles.get_group_box_style())
        text_write_layout = QVBoxLayout()
        
        filename_layout = QHBoxLayout()
        filename_label = QLabel("📄 文件名:")
        filename_label.setStyleSheet("font-weight: 600;")
        filename_layout.addWidget(filename_label)
        self.filename_input = QLineEdit("test.txt")
        self.filename_input.setStyleSheet(AppStyles.get_input_style())
        filename_layout.addWidget(self.filename_input)
        text_write_layout.addLayout(filename_layout)
        
        self.text_content = QTextEdit()
        self.text_content.setPlaceholderText("在此输入要写入的文本内容...")
        self.text_content.setMaximumHeight(120)
        self.text_content.setStyleSheet(AppStyles.get_input_style())
        text_write_layout.addWidget(self.text_content)
        
        write_btn = QPushButton("💾 写入文本文件")
        write_btn.clicked.connect(self.write_text_file)
        write_btn.setStyleSheet(AppStyles.get_purple_button_style())
        write_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        text_write_layout.addWidget(write_btn)
        
        text_write_group.setLayout(text_write_layout)
        file_ops_layout.addWidget(text_write_group)
        
        # 文件上传
        upload_layout = QHBoxLayout()
        upload_btn = QPushButton("📤 上传文件到 U 盘")
        upload_btn.clicked.connect(self.upload_file)
        upload_btn.setStyleSheet(AppStyles.get_accent_button_style())
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_layout.addWidget(upload_btn)
        
        self.show_hidden_check = QCheckBox("👁️ 显示隐藏文件")
        self.show_hidden_check.stateChanged.connect(self.refresh_file_list)
        self.show_hidden_check.setStyleSheet(AppStyles.get_checkbox_style())
        upload_layout.addWidget(self.show_hidden_check)
        
        upload_layout.addStretch()
        file_ops_layout.addLayout(upload_layout)
        
        # 传输进度
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(AppStyles.get_progress_bar_style())
        progress_layout.addWidget(self.progress_bar)
        
        self.speed_label = QLabel("传输速度: 0 MB/s")
        self.speed_label.setVisible(False)
        self.speed_label.setStyleSheet(AppStyles.get_speed_label_style())
        progress_layout.addWidget(self.speed_label)
        
        file_ops_layout.addLayout(progress_layout)
        
        file_ops_group.setLayout(file_ops_layout)
        layout.addWidget(file_ops_group)
        
        # 文件列表
        files_group = QGroupBox("📂 文件列表")
        files_group.setStyleSheet(AppStyles.get_group_box_style())
        files_layout = QVBoxLayout()
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels([
            "文件名", "类型", "大小", "操作"
        ])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_table.setStyleSheet(AppStyles.get_table_style())
        self.files_table.setAlternatingRowColors(True)
        files_layout.addWidget(self.files_table)
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
    
    def scan_usb_devices(self):
        """扫描 USB 设备"""
        self.status_bar.showMessage("🔍 正在扫描 USB 设备...")
        
        devices = USBScanner.scan_devices()
        
        # 更新表格
        self.usb_table.setRowCount(len(devices))
        for i, device in enumerate(devices):
            self.usb_table.setItem(i, 0, QTableWidgetItem(device['name']))
            self.usb_table.setItem(i, 1, QTableWidgetItem(device['manufacturer']))
            self.usb_table.setItem(i, 2, QTableWidgetItem(device['serial']))
            self.usb_table.setItem(i, 3, QTableWidgetItem(device['bus']))
            self.usb_table.setItem(i, 4, QTableWidgetItem(device['speed']))
            self.usb_table.setItem(i, 5, QTableWidgetItem(device['vid_pid']))
        
        self.status_bar.showMessage(f"✅ 已找到 {len(devices)} 个 USB 设备")
    
    def scan_mounted_drives(self):
        """扫描已挂载的 U 盘"""
        self.status_bar.showMessage("🔍 正在扫描 U 盘...")
        
        drives = DriveManager.scan_mounted_drives()
        
        # 更新表格
        self.drives_table.setRowCount(len(drives))
        for i, drive in enumerate(drives):
            self.drives_table.setItem(i, 0, QTableWidgetItem(drive['name']))
            self.drives_table.setItem(i, 1, QTableWidgetItem(drive['path']))
            self.drives_table.setItem(i, 2, QTableWidgetItem(drive['filesystem']))
            self.drives_table.setItem(i, 3, QTableWidgetItem(drive['total']))
            self.drives_table.setItem(i, 4, QTableWidgetItem(drive['used']))
            self.drives_table.setItem(i, 5, QTableWidgetItem(drive['free']))
        
        self.status_bar.showMessage(f"✅ 已找到 {len(drives)} 个 U 盘")
    
    def on_drive_selected(self):
        """选择 U 盘"""
        selected_rows = self.drives_table.selectedItems()
        if selected_rows:
            row = self.drives_table.currentRow()
            self.selected_drive = self.drives_table.item(row, 1).text()
            self.status_bar.showMessage(f"📌 已选择: {self.selected_drive}")
            self.refresh_file_list()
    
    def refresh_file_list(self):
        """刷新文件列表"""
        if not self.selected_drive:
            self.files_table.setRowCount(0)
            return
        
        show_hidden = self.show_hidden_check.isChecked()
        files = DriveManager.list_files(self.selected_drive, show_hidden)
        
        # 更新表格
        self.files_table.setRowCount(len(files))
        for i, file in enumerate(files):
            self.files_table.setItem(i, 0, QTableWidgetItem(file['name']))
            self.files_table.setItem(i, 1, QTableWidgetItem(file['type']))
            self.files_table.setItem(i, 2, QTableWidgetItem(file['size']))
            
            # 添加删除按钮
            if not file['is_dir']:
                delete_btn = QPushButton("🗑️ 删除")
                delete_btn.setStyleSheet(AppStyles.get_danger_button_style())
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.clicked.connect(lambda checked, p=file['path']: self.delete_file(p))
                self.files_table.setCellWidget(i, 3, delete_btn)
    
    def write_text_file(self):
        """写入文本文件"""
        if not self.selected_drive:
            QMessageBox.warning(self, "⚠️ 提示", "请先选择一个 U 盘")
            return
        
        filename = self.filename_input.text().strip()
        content = self.text_content.toPlainText()
        
        if not filename:
            QMessageBox.warning(self, "⚠️ 提示", "请输入文件名")
            return
        
        if not content:
            QMessageBox.warning(self, "⚠️ 提示", "请输入文本内容")
            return
        
        if DriveManager.write_text_file(self.selected_drive, filename, content):
            QMessageBox.information(self, "✅ 成功", f"文件已写入: {filename}")
            self.text_content.clear()
            self.refresh_file_list()
        else:
            QMessageBox.critical(self, "❌ 错误", "写入文件失败")
    
    def upload_file(self):
        """上传文件"""
        if not self.selected_drive:
            QMessageBox.warning(self, "⚠️ 提示", "请先选择一个 U 盘")
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
        self.speed_label.setText(f"⚡ 传输速度: {speed}")
    
    def transfer_finished(self, success, message):
        """传输完成"""
        self.progress_bar.setVisible(False)
        self.speed_label.setVisible(False)
        
        if success:
            QMessageBox.information(self, "✅ 成功", message)
            self.refresh_file_list()
        else:
            QMessageBox.critical(self, "❌ 错误", message)
    
    def delete_file(self, file_path):
        """删除文件"""
        reply = QMessageBox.question(
            self,
            "🗑️ 确认删除",
            f"确定要删除文件吗?\n\n{Path(file_path).name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if DriveManager.delete_file(file_path):
                QMessageBox.information(self, "✅ 成功", "文件已删除")
                self.refresh_file_list()
            else:
                QMessageBox.critical(self, "❌ 错误", "删除文件失败")
    
    def auto_refresh(self):
        """自动刷新"""
        self.scan_mounted_drives()
    
    def refresh_all(self):
        """刷新所有数据"""
        self.scan_usb_devices()
        self.scan_mounted_drives()
