@echo off
REM Wake-on-LAN Service 快速启动脚本 (Windows)

echo 🚀 启动 Wake-on-LAN Service
echo ================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装Python
    pause
    exit /b 1
)

REM 检查是否存在虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate

REM 安装依赖
echo 📥 安装依赖...
pip install -r requirements.txt

REM 启动服务
echo 🌟 启动服务...
echo 服务将在 http://localhost:8000 启动
echo API文档: http://localhost:8000/docs
echo 按 Ctrl+C 停止服务
echo ================================

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
