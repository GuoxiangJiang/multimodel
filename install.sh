#!/bin/bash
# 安装脚本 - 本地 AI 智能文献与图像管理助手

echo "==================================="
echo "开始安装依赖包..."
echo "==================================="
echo ""

echo "检查 Python 版本..."
python --version

echo ""
echo "安装依赖包（这可能需要几分钟）..."
pip install -r requirements.txt

echo ""
echo "==================================="
echo "安装完成！"
echo "==================================="
echo ""
echo "首次运行时会自动下载模型文件（约500MB）"
echo "请使用以下命令测试："
echo "  python main.py --help"
echo ""

