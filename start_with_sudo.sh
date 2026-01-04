#!/bin/bash
# USB 监控程序管理员启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "USB 监控程序 - 管理员模式启动"
echo "=========================================="
echo ""
echo "此模式可以清除系统缓存，获得更准确的测速结果"
echo "需要输入管理员密码"
echo ""

# 检查虚拟环境
if [ -d "venv" ]; then
    PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
else
    PYTHON_PATH="python3"
fi

echo "使用 Python: $PYTHON_PATH"
echo ""

# 使用 sudo 启动程序
sudo "$PYTHON_PATH" "$SCRIPT_DIR/main.py"
