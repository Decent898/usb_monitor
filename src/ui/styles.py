#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序样式配置
定义整个应用的视觉风格和主题
"""


class AppStyles:
    """应用程序样式配置类"""
    
    # 颜色定义
    PRIMARY_COLOR = "#2196F3"  # 主色调 - 蓝色
    PRIMARY_DARK = "#0b7dda"
    PRIMARY_LIGHT = "#64B5F6"
    
    SECONDARY_COLOR = "#4CAF50"  # 次要色 - 绿色
    SECONDARY_DARK = "#45a049"
    
    ACCENT_COLOR = "#FF9800"  # 强调色 - 橙色
    ACCENT_DARK = "#F57C00"
    
    DANGER_COLOR = "#f44336"  # 危险色 - 红色
    DANGER_DARK = "#da190b"
    
    PURPLE_COLOR = "#9C27B0"  # 紫色
    PURPLE_DARK = "#7B1FA2"
    
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_WHITE = "#FFFFFF"
    
    BACKGROUND = "#FAFAFA"
    CARD_BACKGROUND = "#FFFFFF"
    
    # 样式表
    @staticmethod
    def get_main_window_style() -> str:
        """获取主窗口样式"""
        return f"""
            QMainWindow {{
                background-color: {AppStyles.BACKGROUND};
            }}
            QWidget {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB";
                font-size: 13px;
                color: {AppStyles.TEXT_PRIMARY};
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
                padding: 20px;
            }}
            QLabel {{
                color: {AppStyles.TEXT_WHITE};
                background: transparent;
            }}
        """
    
    @staticmethod
    def get_primary_button_style() -> str:
        """获取主按钮样式"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.SECONDARY_COLOR};
                color: {AppStyles.TEXT_WHITE};
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.SECONDARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.SECONDARY_DARK};
                padding-top: 12px;
                padding-bottom: 8px;
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #999999;
            }}
        """
    
    @staticmethod
    def get_secondary_button_style() -> str:
        """获取次按钮样式"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.PRIMARY_COLOR};
                color: {AppStyles.TEXT_WHITE};
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.PRIMARY_DARK};
                padding-top: 12px;
                padding-bottom: 8px;
            }}
        """
    
    @staticmethod
    def get_accent_button_style() -> str:
        """获取强调按钮样式"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.ACCENT_COLOR};
                color: {AppStyles.TEXT_WHITE};
                padding: 12px 25px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.ACCENT_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.ACCENT_DARK};
                padding-top: 14px;
                padding-bottom: 10px;
            }}
        """
    
    @staticmethod
    def get_danger_button_style() -> str:
        """获取危险按钮样式"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.DANGER_COLOR};
                color: {AppStyles.TEXT_WHITE};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.DANGER_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.DANGER_DARK};
                padding-top: 8px;
                padding-bottom: 4px;
            }}
        """
    
    @staticmethod
    def get_purple_button_style() -> str:
        """获取紫色按钮样式"""
        return f"""
            QPushButton {{
                background-color: {AppStyles.PURPLE_COLOR};
                color: {AppStyles.TEXT_WHITE};
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {AppStyles.PURPLE_DARK};
            }}
            QPushButton:pressed {{
                background-color: {AppStyles.PURPLE_DARK};
                padding-top: 12px;
                padding-bottom: 8px;
            }}
        """
    
    @staticmethod
    def get_table_style() -> str:
        """获取表格样式"""
        return f"""
            QTableWidget {{
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: {AppStyles.CARD_BACKGROUND};
                gridline-color: #F5F5F5;
                selection-background-color: {AppStyles.PRIMARY_LIGHT};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #F0F0F0;
            }}
            QTableWidget::item:selected {{
                background-color: {AppStyles.PRIMARY_LIGHT};
                color: {AppStyles.TEXT_WHITE};
            }}
            QHeaderView::section {{
                background-color: #F5F5F5;
                padding: 12px;
                border: none;
                border-bottom: 2px solid {AppStyles.PRIMARY_COLOR};
                font-weight: 600;
                font-size: 13px;
                color: {AppStyles.TEXT_PRIMARY};
            }}
        """
    
    @staticmethod
    def get_group_box_style() -> str:
        """获取分组框样式"""
        return f"""
            QGroupBox {{
                font-weight: 600;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: {AppStyles.CARD_BACKGROUND};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: {AppStyles.PRIMARY_COLOR};
            }}
        """
    
    @staticmethod
    def get_input_style() -> str:
        """获取输入框样式"""
        return f"""
            QLineEdit, QTextEdit {{
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: {AppStyles.CARD_BACKGROUND};
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {AppStyles.PRIMARY_COLOR};
            }}
            QTextEdit {{
                padding: 10px;
            }}
        """
    
    @staticmethod
    def get_tab_widget_style() -> str:
        """获取标签页样式"""
        return f"""
            QTabWidget::pane {{
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: {AppStyles.CARD_BACKGROUND};
                padding: 5px;
            }}
            QTabBar::tab {{
                background-color: #F5F5F5;
                color: {AppStyles.TEXT_SECONDARY};
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {AppStyles.PRIMARY_COLOR};
                color: {AppStyles.TEXT_WHITE};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {AppStyles.PRIMARY_LIGHT};
                color: {AppStyles.TEXT_WHITE};
            }}
        """
    
    @staticmethod
    def get_progress_bar_style() -> str:
        """获取进度条样式"""
        return f"""
            QProgressBar {{
                border: 2px solid {AppStyles.PRIMARY_COLOR};
                border-radius: 6px;
                text-align: center;
                background-color: #F5F5F5;
                font-weight: 600;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {AppStyles.PRIMARY_COLOR},
                    stop:1 {AppStyles.PRIMARY_LIGHT});
                border-radius: 4px;
            }}
        """
    
    @staticmethod
    def get_user_badge_style() -> str:
        """获取用户徽章样式"""
        return f"""
            QLabel {{
                color: {AppStyles.TEXT_WHITE};
                font-size: 13px;
                font-weight: 500;
                background-color: rgba(255, 255, 255, 0.25);
                padding: 10px 20px;
                border-radius: 20px;
            }}
        """
    
    @staticmethod
    def get_speed_label_style() -> str:
        """获取速度标签样式"""
        return f"""
            QLabel {{
                font-weight: 600;
                font-size: 14px;
                color: {AppStyles.PRIMARY_COLOR};
                padding: 5px;
            }}
        """
    
    @staticmethod
    def get_checkbox_style() -> str:
        """获取复选框样式"""
        return f"""
            QCheckBox {{
                spacing: 8px;
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {AppStyles.PRIMARY_COLOR};
                border-radius: 4px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {AppStyles.PRIMARY_COLOR};
                image: url(none);
            }}
        """
