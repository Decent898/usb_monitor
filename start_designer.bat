@echo off
echo ============================================
echo    启动 Qt Designer 可视化界面设计器
echo ============================================
echo.

REM 激活虚拟环境
call .venv\Scripts\activate.bat

echo 正在启动 Qt Designer...
echo.

REM 尝试多种方式启动 Designer
python -m qt6_applications.Qt.designer 2>nul || (
    echo 尝试方式 1 失败，尝试方式 2...
    designer 2>nul || (
        echo 尝试方式 2 失败，尝试方式 3...
        pyqt6-tools designer 2>nul || (
            echo.
            echo [错误] 无法启动 Qt Designer
            echo 请确保已安装 pyqt6-tools:
            echo    pip install pyqt6-tools
            echo.
            pause
            exit /b 1
        )
    )
)

echo.
echo Qt Designer 已启动！
echo.
echo 使用说明:
echo 1. 打开 usb_manager.ui 文件进行编辑
echo 2. 保存后运行以下命令转换为 Python:
echo    pyuic6 usb_manager.ui -o usb_manager_ui.py
echo.
pause
