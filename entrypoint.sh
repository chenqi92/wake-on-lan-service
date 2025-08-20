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
python -c "
try:
    from app.main import app
    print('✓ 应用模块加载成功')
except Exception as e:
    print(f'✗ 应用模块加载失败: {e}')
    exit(1)
"

echo "=========================================="
echo "启动 Wake-on-LAN 服务..."
echo "API文档: http://$HOST:$PORT/docs"
echo "健康检查: http://$HOST:$PORT/health"
echo "=========================================="

# 启动应用，添加更多的错误处理和重试机制
exec python -m uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --access-log \
    --log-level info \
    --no-server-header \
    --date-header \
    --timeout-keep-alive 30
