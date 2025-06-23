#!/bin/bash

# Wake-on-LAN Service 快速启动脚本

set -e

echo "🚀 启动 Wake-on-LAN Service"
echo "================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install -r requirements.txt

# 启动服务
echo "🌟 启动服务..."
echo "服务将在 http://localhost:8000 启动"
echo "API文档: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务"
echo "================================"

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
