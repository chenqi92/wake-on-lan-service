# 故障排除指南

## 🚨 常见问题

### 1. 访问根路径 `/` 显示 404 错误

**症状**: 浏览器访问 `http://localhost:12345/` 时显示 404 Not Found

**可能原因**:
1. 应用启动失败
2. 依赖包缺失
3. 模块导入错误
4. 环境变量未设置

**解决步骤**:

#### 步骤 1: 检查应用是否正常启动
```bash
# 运行调试脚本
python debug_app.py

# 或运行简单测试
python simple_test.py
```

#### 步骤 2: 检查依赖包
```bash
# 安装所有依赖
pip install -r requirements.txt

# 检查关键依赖
pip list | grep -E "(fastapi|uvicorn|pillow|jose|passlib)"
```

#### 步骤 3: 设置环境变量
```bash
# Linux/Mac
export WOL_USERNAME=admin
export WOL_PASSWORD=admin123
export WOL_SESSION_SECRET=your-secret-key

# Windows
set WOL_USERNAME=admin
set WOL_PASSWORD=admin123
set WOL_SESSION_SECRET=your-secret-key
```

#### 步骤 4: 手动启动应用
```bash
# 启动应用
uvicorn app.main:app --host 0.0.0.0 --port 12345 --reload

# 检查日志输出
```

#### 步骤 5: 测试基本端点
```bash
# 健康检查
curl http://localhost:12345/health

# API信息
curl http://localhost:12345/api

# 验证码
curl http://localhost:12345/api/captcha
```

### 2. Docker容器启动失败

**症状**: 容器无法启动或立即退出

**解决步骤**:

```bash
# 检查容器日志
docker logs wake-on-lan-service

# 检查容器状态
docker ps -a

# 重新构建镜像
docker build -t wake-on-lan-test .

# 使用调试模式启动
docker run -it --rm \
  -e WOL_USERNAME=admin \
  -e WOL_PASSWORD=admin123 \
  -e WOL_SESSION_SECRET=test-secret \
  wake-on-lan-test bash
```

### 3. 登录功能异常

**症状**: 无法登录或验证码不显示

**检查项目**:

1. **验证码API**:
```bash
curl http://localhost:12345/api/captcha
```

2. **登录API**:
```bash
# 先获取验证码ID，然后测试登录
curl -X POST http://localhost:12345/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","captcha_id":"test","captcha_text":"1234"}'
```

3. **环境变量**:
```bash
# 检查环境变量是否正确设置
echo $WOL_USERNAME
echo $WOL_PASSWORD
```

### 4. 网络接口访问失败

**症状**: 无法获取网络接口或WOL功能失败

**解决方案**:

1. **检查权限**:
```bash
# Docker需要特殊权限
docker run --cap-add NET_ADMIN --cap-add NET_RAW ...
```

2. **检查网络模式**:
```bash
# 使用host网络模式
docker run --network host ...
```

3. **测试网络接口**:
```bash
# 在容器内测试
docker exec -it wake-on-lan-service python -c "
from app.network_utils import get_network_interfaces
print(get_network_interfaces())
"
```

## 🔧 调试工具

### 1. 调试脚本

项目提供了多个调试脚本：

- `debug_app.py` - 全面的应用调试
- `simple_test.py` - 简单功能测试
- `test_imports.py` - 导入测试
- `quick_test.py` - 快速端到端测试

### 2. 日志级别

```bash
# 启用详细日志
uvicorn app.main:app --log-level debug

# 或在Docker中
docker run -e LOG_LEVEL=debug ...
```

### 3. 开发模式

```bash
# 启用自动重载
uvicorn app.main:app --reload

# 启用调试模式
uvicorn app.main:app --debug
```

## 🚀 快速修复

### 最小可用版本

如果遇到复杂问题，可以使用最小版本：

```python
# minimal_app.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Wake-on-LAN</title></head>
    <body>
        <h1>Wake-on-LAN Service</h1>
        <p>服务正在运行</p>
        <a href="/docs">API文档</a>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok"}
```

启动最小版本：
```bash
uvicorn minimal_app:app --host 0.0.0.0 --port 12345
```

### 重置到工作状态

```bash
# 1. 清理环境
docker stop wake-on-lan-service
docker rm wake-on-lan-service
docker rmi wake-on-lan-test

# 2. 重新安装依赖
pip uninstall -y -r requirements.txt
pip install -r requirements.txt

# 3. 重新构建
docker build -t wake-on-lan-test .

# 4. 测试启动
python simple_test.py
```

## 📞 获取帮助

如果问题仍然存在：

1. **收集信息**:
```bash
# 系统信息
python --version
docker --version
pip list

# 运行完整诊断
python debug_app.py > debug_output.txt 2>&1
```

2. **提交Issue**:
- 访问: https://github.com/chenqi92/wake-on-lan-service/issues
- 包含调试输出和错误信息
- 说明操作系统和环境

3. **社区支持**:
- 查看现有Issues
- 参考文档和示例
- 使用测试脚本验证问题
