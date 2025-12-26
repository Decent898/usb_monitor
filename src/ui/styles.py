#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序样式配置
定义整个应用的视觉风格和主题 - Material Design 3 风格
"""


class AppStyles:
    """应用程序样式配置类"""
    
    # Material Design 3 颜色系统
    # 主色调 - 蓝色系
    PRIMARY_COLOR = "#1976D2"  # 深蓝色
    PRIMARY_DARK = "#0D47A1"
    PRIMARY_LIGHT = "#BBDEFB"
    PRIMARY_CONTAINER = "#E3F2FD"
    
    # 次要色 - 青色系
    SECONDARY_COLOR = "#00897B"  # 青色
    SECONDARY_DARK = "#00695C"
    SECONDARY_LIGHT = "#B2DFDB"
    SECONDARY_CONTAINER = "#E0F2F1"
    
    # 强调色 - 橙色系
    ACCENT_COLOR = "#FB8C00"
    ACCENT_DARK = "#E65100"
    ACCENT_LIGHT = "#FFE0B2"
    
    # 危险色 - 红色系
    DANGER_COLOR = "#D32F2F"
    DANGER_DARK = "#B71C1C"
    DANGER_LIGHT = "#FFCDD2"
    
    # 紫色系
    PURPLE_COLOR = "#7B1FA2"
    PURPLE_DARK = "#4A148C"
    PURPLE_LIGHT = "#E1BEE7"
    
    # 文字颜色
    TEXT_PRIMARY = "#1C1B1F"      # 深灰色文字
    TEXT_SECONDARY = "#49454F"    # 中等灰色
    TEXT_DISABLED = "#9E9E9E"     # 禁用状态
    TEXT_WHITE = "#FFFFFF"
    TEXT_ON_PRIMARY = "#FFFFFF"   # 主色上的文字
    
    # 背景颜色
    BACKGROUND = "#F5F5F5"        # 浅灰背景
    SURFACE = "#FFFFFF"           # 表面/卡片背景
    SURFACE_VARIANT = "#E7E0EC"   # 表面变体
    
    # 边框和分隔线
    OUTLINE = "#CAC4D0"
    OUTLINE_VARIANT = "#E0E0E0"
    
    # 表格颜色
    TABLE_ROW_EVEN = "#FAFAFA"    # 偶数行
    TABLE_ROW_ODD = "#FFFFFF"     # 奇数行
    TABLE_HEADER = "#ECEFF1"      # 表头背景
    TABLE_SELECTED = "#E3F2FD"    # 选中行
    
    # 样式表
    @staticmethod
    def get_main_window_style() -> str:
        """获取主窗口样式"""
        return f"""
            QMainWindow {{
                background-color: {AppStyles.BACKGROUND};
            }}
            QWidget {{
                font-family: "Microsoft YaHei UI", "Segoe UI", "PingFang SC", sans-serif;
                font-size: 14px;
                color: {AppStyles.TEXT_PRIMARY};
                background-color: transparent;
            }}
            QLabel {{
                color: {AppStyles.TEXT_PRIMARY};
                background-color: transparent;
            }}
        """
    
    @staticmethod
    def get_header_style() -> str:
        """获取标题栏样式"""
        return f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {AppStyles.PRIMARY_COLOR},
                    stop:1 {AppStyles.PRIMARY_LIGHT});
                border-radius: 12px;
                padding: 24px;
            }}
            QLabel {{
                color: {AppStyles.TEXT_ON_PRIMARY};
                background: transparent;
            }}
        """
    
    @staticmethod
    def get_primary_button_style() -> str:
        """获取主按钮样式 - Material Design 3"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.SECONDARY_COLOR};
                color: {AppStyles.TEXT_ON_PRIMARY};
                padding: 14px 28px;
                border: none;
                border-radius: 20px;
                font-weight: 600;
                font-size: 14px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.SECONDARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.SECONDARY_DARK};
            }}
            QPushButton:disabled {{
                background-color: {AppStyles.OUTLINE_VARIANT};
                color: {AppStyles.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def get_secondary_button_style() -> str:
        """获取次按钮样式 - Material Design 3"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.PRIMARY_COLOR};
                color: {AppStyles.TEXT_ON_PRIMARY};
                padding: 14px 28px;
                border: none;
                border-radius: 20px;
                font-weight: 600;
                font-size: 14px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.PRIMARY_DARK};
            }}
        """
    
    @staticmethod
    def get_accent_button_style() -> str:
        """获取强调按钮样式 - Material Design 3"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.ACCENT_COLOR};
                color: {AppStyles.TEXT_ON_PRIMARY};
                padding: 14px 28px;
                border: none;
                border-radius: 20px;
                font-weight: 600;
                font-size: 14px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.ACCENT_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.ACCENT_DARK};
            }}
        """
    
    @staticmethod
    def get_danger_button_style() -> str:
        """获取危险按钮样式 - Material Design 3"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.DANGER_COLOR};
                color: {AppStyles.TEXT_ON_PRIMARY};
                border: none;
                border-radius: 16px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.DANGER_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.DANGER_DARK};
            }}
        """
    
    @staticmethod
    def get_purple_button_style() -> str:
        """获取紫色按钮样式 - Material Design 3"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.PURPLE_COLOR};
                color: {AppStyles.TEXT_ON_PRIMARY};
                padding: 14px 28px;
                border: none;
                border-radius: 20px;
                font-weight: 600;
                font-size: 14px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.PURPLE_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.PURPLE_DARK};
            }}
        """
    
    @staticmethod
    def get_table_style() -> str:
        """获取表格样式 - Material Design 3"""
        return f"""
            QTableWidget {{
                border: 1px solid {AppStyles.OUTLINE};
                border-radius: 12px;
                background-color: {AppStyles.SURFACE};
                gridline-color: {AppStyles.OUTLINE_VARIANT};
                selection-background-color: {AppStyles.TABLE_SELECTED};
                font-size: 14px;
                color: {AppStyles.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: 14px 12px;
                border-bottom: 1px solid {AppStyles.OUTLINE_VARIANT};
                color: {AppStyles.TEXT_PRIMARY};
                background-color: transparent;
            }}
            QTableWidget::item:alternate {{
                background-color: {AppStyles.TABLE_ROW_EVEN};
            }}
            QTableWidget::item:selected {{
                background-color: {AppStyles.TABLE_SELECTED};
                color: {AppStyles.PRIMARY_DARK};
            }}
            QHeaderView::section {{
                background-color: {AppStyles.TABLE_HEADER};
                padding: 16px 12px;
                border: none;
                border-bottom: 2px solid {AppStyles.PRIMARY_COLOR};
                font-weight: 700;
                font-size: 15px;
                color: {AppStyles.TEXT_PRIMARY};
            }}
        """
    
    @staticmethod
    def get_group_box_style() -> str:
        """获取分组框样式 - Material Design 3"""
        return f"""
            QGroupBox {{
                font-weight: 700;
                font-size: 16px;
                border: 2px solid {AppStyles.OUTLINE};
                border-radius: 16px;
                margin-top: 20px;
                padding: 20px 16px 16px 16px;
                background-color: {AppStyles.SURFACE};
                color: {AppStyles.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 12px;
                color: {AppStyles.PRIMARY_COLOR};
                background-color: {AppStyles.SURFACE};
            }}
        """
    
    @staticmethod
    def get_input_style() -> str:
        """获取输入框样式 - Material Design 3"""
        return f"""
            QLineEdit, QTextEdit {{
                border: 2px solid {AppStyles.OUTLINE};
                border-radius: 8px;
                padding: 12px 16px;
                background-color: {AppStyles.SURFACE};
                font-size: 14px;
                color: {AppStyles.TEXT_PRIMARY};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {AppStyles.PRIMARY_COLOR};
                border-width: 2px;
            }}
            QTextEdit {{
                padding: 14px;
            }}
        """
    
    @staticmethod
    def get_tab_widget_style() -> str:
        """获取标签页样式 - Material Design 3"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {AppStyles.OUTLINE};
                border-radius: 12px;
                background-color: {AppStyles.SURFACE};
                padding: 8px;
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {AppStyles.SURFACE_VARIANT};
                color: {AppStyles.TEXT_SECONDARY};
                padding: 16px 32px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                margin-right: 6px;
                font-weight: 700;
                font-size: 15px;
                min-height: 24px;
                border: 1px solid {AppStyles.OUTLINE};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {AppStyles.PRIMARY_COLOR};
                color: {AppStyles.TEXT_ON_PRIMARY};
                border-color: {AppStyles.PRIMARY_COLOR};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {AppStyles.PRIMARY_CONTAINER};
                color: {AppStyles.PRIMARY_DARK};
            }}
        """
    
    @staticmethod
    def get_progress_bar_style() -> str:
        """获取进度条样式 - Material Design 3"""
        return f"""
            QProgressBar {{
                border: 2px solid {AppStyles.OUTLINE};
                border-radius: 12px;
                text-align: center;
                background-color: {AppStyles.PRIMARY_CONTAINER};
                font-weight: 700;
                font-size: 14px;
                height: 36px;
                color: {AppStyles.TEXT_PRIMARY};
            }}
            QProgressBar::chunk {{
                background: {AppStyles.PRIMARY_COLOR};
                border-radius: 10px;
            }}
        """
    
    @staticmethod
    def get_user_badge_style() -> str:
        """获取用户徽章样式 - Material Design 3"""
        return f"""
            QLabel {{
                color: {AppStyles.TEXT_ON_PRIMARY};
                font-size: 15px;
                font-weight: 600;
                background-color: rgba(255, 255, 255, 0.3);
                padding: 12px 24px;
                border-radius: 24px;
            }}
        """
    
    @staticmethod
    def get_speed_label_style() -> str:
        """获取速度标签样式 - Material Design 3"""
        return f"""
            QLabel {{
                font-weight: 700;
                font-size: 15px;
                color: {AppStyles.PRIMARY_COLOR};
                background-color: {AppStyles.PRIMARY_CONTAINER};
                padding: 8px 16px;
                border-radius: 8px;
            }}
        """
    
    @staticmethod
    def get_checkbox_style() -> str:
        """获取复选框样式 - Material Design 3"""
        return f"""
            QCheckBox {{
                spacing: 12px;
                font-size: 14px;
                font-weight: 500;
                color: {AppStyles.TEXT_PRIMARY};
            }}
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
                border: 2px solid {AppStyles.OUTLINE};
                border-radius: 6px;
                background-color: {AppStyles.SURFACE};
            }}
            QCheckBox::indicator:checked {{
                background-color: {AppStyles.PRIMARY_COLOR};
                border-color: {AppStyles.PRIMARY_COLOR};
                image: url(none);
            }}
            QCheckBox::indicator:hover {{
                border-color: {AppStyles.PRIMARY_COLOR};
            }}
        """
