"""
Wake-on-LAN Service - 修复版本
内网设备远程唤醒服务，支持通过MAC地址唤醒网络设备
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

# 应用版本
APP_VERSION = "1.0.1"

# 应用启动时间
start_time = time.time()

# 设置环境变量默认值
os.environ.setdefault('WOL_USERNAME', 'admin')
os.environ.setdefault('WOL_PASSWORD', 'admin123')
os.environ.setdefault('WOL_SESSION_SECRET', 'your-secret-key-change-this')

# 创建FastAPI应用
app = FastAPI(
    title="Wake-on-LAN Service",
    description="内网设备远程唤醒服务 - 支持通过MAC地址唤醒网络设备",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建静态文件目录
static_dir = Path("app/static")
static_dir.mkdir(exist_ok=True)

# 挂载静态文件
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception as e:
    print(f"警告: 静态文件目录挂载失败: {e}")

# 简单的登录页面HTML
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake-on-LAN 登录</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .login-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            width: 100%;
            max-width: 400px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .login-header h1 {
            color: #333;
            font-size: 2em;
            margin-bottom: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .login-button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .login-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .info {
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9em;
            color: #1565c0;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🌐 Wake-on-LAN</h1>
            <p>内网设备远程唤醒服务</p>
        </div>

        <div class="info">
            <strong>测试账号:</strong><br>
            用户名: admin<br>
            密码: admin123
        </div>

        <form action="/login" method="post">
            <div class="form-group">
                <label for="username">用户名:</label>
                <input type="text" id="username" name="username" required value="admin">
            </div>

            <div class="form-group">
                <label for="password">密码:</label>
                <input type="password" id="password" name="password" required value="admin123">
            </div>

            <button type="submit" class="login-button">登录</button>
        </form>
    </div>
</body>
</html>
"""

# 主界面HTML
MAIN_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake-on-LAN 管理界面</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .content {
            padding: 40px;
        }
        .section {
            margin-bottom: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }
        .section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Wake-on-LAN 管理界面</h1>
            <p>内网设备远程唤醒服务 v""" + APP_VERSION + """</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>🎉 登录成功!</h2>
                <div class="success">
                    <strong>欢迎使用 Wake-on-LAN 服务!</strong><br>
                    服务正在正常运行，您可以通过API进行设备唤醒操作。
                </div>
                
                <h3>📋 可用功能:</h3>
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li>设备唤醒 (Wake-on-LAN)</li>
                    <li>网络接口查询</li>
                    <li>IP白名单管理</li>
                    <li>API接口调用</li>
                </ul>
                
                <h3>🔗 相关链接:</h3>
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li><a href="/health">健康检查</a></li>
                    <li><a href="/docs">API文档</a></li>
                    <li><a href="/logout">退出登录</a></li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""

# 路由定义
@app.get("/", response_class=HTMLResponse, summary="Web界面", description="Wake-on-LAN Web管理界面")
async def web_interface(request: Request):
    """Web管理界面"""
    # 简单的会话检查
    if request.cookies.get("logged_in") == "true":
        return MAIN_HTML
    else:
        return LOGIN_HTML

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """处理登录"""
    expected_username = os.getenv("WOL_USERNAME", "admin")
    expected_password = os.getenv("WOL_PASSWORD", "admin123")
    
    if username == expected_username and password == expected_password:
        # 登录成功，设置cookie并重定向
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie("logged_in", "true", max_age=3600)  # 1小时
        return response
    else:
        # 登录失败，返回登录页面
        return LOGIN_HTML.replace(
            '<div class="info">',
            '<div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; border-radius: 8px; padding: 15px; margin-bottom: 20px;"><strong>登录失败:</strong> 用户名或密码错误</div><div class="info">'
        )

@app.get("/logout")
async def logout():
    """退出登录"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("logged_in")
    return response

@app.get("/health", summary="健康检查", description="检查服务运行状态")
async def health_check():
    """健康检查接口"""
    uptime_seconds = int(time.time() - start_time)
    uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
    
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "uptime": uptime_str,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/interfaces", summary="查询网络接口", description="获取所有可用的网络接口信息")
async def get_interfaces(request: Request):
    """获取所有网络接口信息"""
    # 简单的认证检查
    if request.cookies.get("logged_in") != "true":
        raise HTTPException(status_code=401, detail="需要登录")
    
    try:
        import psutil
        interfaces = []
        
        for name, addrs in psutil.net_if_addrs().items():
            interface_info = {"name": name, "addresses": []}
            
            for addr in addrs:
                if addr.family.name in ['AF_INET', 'AF_INET6']:
                    interface_info["addresses"].append({
                        "family": addr.family.name,
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    })
            
            if interface_info["addresses"]:
                interfaces.append(interface_info)
        
        return {
            "interfaces": interfaces,
            "count": len(interfaces)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取网络接口失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12345)
