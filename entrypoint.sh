#!/bin/bash

# Wake-on-LAN Service 启动脚本
# 提供更健壮的启动和错误处理

set -e

# 默认配置
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="12345"

# 从环境变量获取配置
HOST=${HOST:-$DEFAULT_HOST}
PORT=${PORT:-$DEFAULT_PORT}

echo "=========================================="
echo "Wake-on-LAN Service 启动中..."
echo "=========================================="
echo "主机: $HOST"
echo "端口: $PORT"
echo "用户: $(whoami)"
echo "工作目录: $(pwd)"
echo "Python版本: $(python --version)"
echo "=========================================="

# 检查网络接口访问权限
echo "检查网络接口访问权限..."
python -c "
import psutil
try:
    interfaces = psutil.net_if_addrs()
    print(f'发现 {len(interfaces)} 个网络接口')
    for name in list(interfaces.keys())[:3]:  # 只显示前3个
        print(f'  - {name}')
    if len(interfaces) > 3:
        print(f'  ... 还有 {len(interfaces) - 3} 个接口')
except Exception as e:
    print(f'警告: 无法访问网络接口: {e}')
    print('这可能会影响WOL功能，但服务仍会启动')
"

# 检查端口是否可用
echo "检查端口 $PORT 是否可用..."
if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
    echo "警告: 端口 $PORT 可能已被占用"
else
    echo "端口 $PORT 可用"
fi

# 启动应用前的最后检查
echo "验证应用模块..."

# 按优先级尝试不同的应用版本
APP_MODULE="app.main_deploy:app"

echo "尝试部署版本应用..."
if python -c "from app.main_deploy import app; print('✓ 部署版本应用加载成功')" 2>/dev/null; then
    echo "✓ 部署版本应用验证通过"
    APP_MODULE="app.main_deploy:app"
elif [ -f "/app/standalone_app_v2.py" ]; then
    echo "尝试现代化应用..."
    if python -c "from standalone_app_v2 import app; print('✓ 现代化应用加载成功')" 2>/dev/null; then
        echo "✓ 现代化应用验证通过"
        APP_MODULE="standalone_app_v2:app"
    else
        echo "✗ 现代化应用加载失败，尝试原始应用..."
        if python -c "from app.main import app; print('✓ 原始应用加载成功')" 2>/dev/null; then
            echo "✓ 原始应用验证通过"
            APP_MODULE="app.main:app"
        else
            echo "✗ 原始应用也加载失败，使用简化应用..."
            APP_MODULE="app.main_simple:app"
        fi
    fi
else
    echo "尝试原始应用..."
    if python -c "from app.main import app; print('✓ 原始应用加载成功')" 2>/dev/null; then
        echo "✓ 原始应用验证通过"
        APP_MODULE="app.main:app"
    else
        echo "✗ 原始应用加载失败，使用简化应用..."
        APP_MODULE="app.main_simple:app"
    fi
fi

echo "使用应用模块: $APP_MODULE"

echo "=========================================="
echo "启动 Wake-on-LAN 服务..."
echo "API文档: http://$HOST:$PORT/docs"
echo "健康检查: http://$HOST:$PORT/health"
echo "=========================================="

# 启动应用，添加更多的错误处理和重试机制
exec python -m uvicorn "$APP_MODULE" \
    --host "$HOST" \
    --port "$PORT" \
    --access-log \
    --log-level info \
    --no-server-header \
    --date-header \
    --timeout-keep-alive 30
