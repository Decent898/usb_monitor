#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口
USB 设备管理器 - macOS 版本
"""

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import USBManagerWindow


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("USB 设备管理器")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("USB Monitor")
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = USBManagerWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
