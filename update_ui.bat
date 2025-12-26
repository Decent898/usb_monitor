@echo off
echo ============================================
echo    UI 文件转换工具
echo ============================================
echo.

REM 激活虚拟环境
call .venv\Scripts\activate.bat

echo 正在转换 usb_manager.ui 为 Python 代码...
echo.

python -m PyQt6.uic.pyuic usb_manager.ui -o src/ui/usb_manager_ui.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 转换成功！
    echo.
    echo UI 文件已更新为: src\ui\usb_manager_ui.py
    echo.
    echo 现在可以运行程序查看效果:
    echo    python main.py
) else (
    echo.
    echo ❌ 转换失败！
    echo 请检查错误信息
)

echo.
pause
