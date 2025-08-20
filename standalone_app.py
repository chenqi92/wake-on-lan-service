#!/usr/bin/env python3
"""
Wake-on-LAN 独立应用 - 单文件版本
可以直接运行，无需复杂的模块导入
"""

import os
import sys
import time
import json
import secrets
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from io import BytesIO

# 设置环境变量
os.environ.setdefault('WOL_USERNAME', 'admin')
os.environ.setdefault('WOL_PASSWORD', 'admin123')
os.environ.setdefault('WOL_SESSION_SECRET', 'standalone-secret-key')

try:
    from fastapi import FastAPI, HTTPException, Depends, Request, Form
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
    from fastapi.security import HTTPBearer
    import uvicorn
    print("✅ 所有依赖导入成功")
except ImportError as e:
    print(f"❌ 依赖导入失败: {e}")
    print("请安装依赖: pip install fastapi uvicorn")
    sys.exit(1)

# 应用配置
APP_VERSION = "1.0.1-standalone"
start_time = time.time()

# 简单的会话存储
sessions = {}

# 创建FastAPI应用
app = FastAPI(
    title="Wake-on-LAN Service (Standalone)",
    description="内网设备远程唤醒服务 - 独立版本",
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

# HTML模板
LOGIN_PAGE = """<!DOCTYPE html>
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
            min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px;
        }
        .container {
            background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px; width: 100%; max-width: 400px;
        }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #333; font-size: 2em; margin-bottom: 10px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #555; }
        input { width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 8px; font-size: 16px; }
        input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        button {
            width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3); }
        .info { background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 15px; margin-bottom: 20px; color: #1565c0; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 15px; margin-bottom: 20px; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Wake-on-LAN</h1>
            <p>内网设备远程唤醒服务</p>
        </div>
        {error_message}
        <div class="info">
            <strong>默认账号:</strong><br>
            用户名: {username}<br>
            密码: {password}
        </div>
        <form method="post" action="/login">
            <div class="form-group">
                <label>用户名:</label>
                <input type="text" name="username" required value="{username}">
            </div>
            <div class="form-group">
                <label>密码:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">登录</button>
        </form>
    </div>
</body>
</html>"""

MAIN_PAGE = """<!DOCTYPE html>
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
            min-height: 100vh; padding: 20px;
        }
        .container {
            max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; display: flex; justify-content: space-between; align-items: center;
        }
        .header h1 { font-size: 2.5em; }
        .logout-btn {
            background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3);
            padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 0.9em;
        }
        .content { padding: 40px; }
        .section {
            margin-bottom: 40px; padding: 30px; background: #f8f9fa; border-radius: 10px;
            border-left: 5px solid #667eea;
        }
        .section h2 { color: #333; margin-bottom: 20px; font-size: 1.5em; }
        .success {
            background: #d4edda; border: 1px solid #c3e6cb; color: #155724;
            padding: 15px; border-radius: 8px; margin: 20px 0;
        }
        .api-link { color: #667eea; text-decoration: none; margin-right: 20px; }
        .api-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🌐 Wake-on-LAN</h1>
                <p>内网设备远程唤醒服务 v{version}</p>
            </div>
            <a href="/logout" class="logout-btn">退出登录</a>
        </div>
        <div class="content">
            <div class="section">
                <h2>🎉 登录成功!</h2>
                <div class="success">
                    <strong>欢迎使用 Wake-on-LAN 服务!</strong><br>
                    服务正在正常运行，当前用户: <strong>{username}</strong>
                </div>
                <h3>📋 可用功能:</h3>
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li>✅ 用户认证和会话管理</li>
                    <li>✅ 网络接口查询</li>
                    <li>✅ 健康检查接口</li>
                    <li>✅ API文档自动生成</li>
                    <li>🔄 设备唤醒功能 (开发中)</li>
                    <li>🔄 IP白名单管理 (开发中)</li>
                </ul>
                <h3>🔗 API接口:</h3>
                <p style="margin: 15px 0;">
                    <a href="/health" class="api-link">健康检查</a>
                    <a href="/interfaces" class="api-link">网络接口</a>
                    <a href="/docs" class="api-link">API文档</a>
                    <a href="/redoc" class="api-link">ReDoc文档</a>
                </p>
            </div>
        </div>
    </div>
</body>
</html>"""

def create_session(username: str) -> str:
    """创建会话"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "username": username,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    return session_id

def verify_session(session_id: str) -> Optional[Dict[str, Any]]:
    """验证会话"""
    if session_id not in sessions:
        return None
    
    session_data = sessions[session_id]
    if datetime.utcnow() > session_data["expires_at"]:
        del sessions[session_id]
        return None
    
    return session_data

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """首页"""
    session_id = request.cookies.get("session_id")
    session_data = verify_session(session_id) if session_id else None
    
    if session_data:
        return MAIN_PAGE.format(
            version=APP_VERSION,
            username=session_data["username"]
        )
    else:
        return LOGIN_PAGE.format(
            username=os.getenv("WOL_USERNAME", "admin"),
            password=os.getenv("WOL_PASSWORD", "admin123"),
            error_message=""
        )

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """登录处理"""
    expected_username = os.getenv("WOL_USERNAME", "admin")
    expected_password = os.getenv("WOL_PASSWORD", "admin123")
    
    if username == expected_username and password == expected_password:
        session_id = create_session(username)
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie("session_id", session_id, max_age=3600, httponly=True)
        return response
    else:
        error_html = '<div class="error"><strong>登录失败:</strong> 用户名或密码错误</div>'
        return LOGIN_PAGE.format(
            username=username,
            password="",
            error_message=error_html
        )

@app.get("/logout")
async def logout(request: Request):
    """退出登录"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_id")
    return response

@app.get("/health")
async def health():
    """健康检查"""
    uptime_seconds = int(time.time() - start_time)
    uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
    
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "uptime": uptime_str,
        "timestamp": datetime.utcnow().isoformat(),
        "sessions": len(sessions)
    }

@app.get("/interfaces")
async def get_interfaces(request: Request):
    """获取网络接口"""
    session_id = request.cookies.get("session_id")
    if not verify_session(session_id):
        raise HTTPException(status_code=401, detail="需要登录")
    
    try:
        import psutil
        interfaces = []
        
        for name, addrs in psutil.net_if_addrs().items():
            interface_info = {"name": name, "addresses": []}
            
            for addr in addrs:
                if hasattr(addr, 'family') and addr.family.name in ['AF_INET', 'AF_INET6']:
                    interface_info["addresses"].append({
                        "family": addr.family.name,
                        "address": addr.address,
                        "netmask": getattr(addr, 'netmask', None),
                        "broadcast": getattr(addr, 'broadcast', None)
                    })
            
            if interface_info["addresses"]:
                interfaces.append(interface_info)
        
        return {"interfaces": interfaces, "count": len(interfaces)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取网络接口失败: {str(e)}")

def main():
    """主函数"""
    print("=" * 60)
    print("🌐 Wake-on-LAN 独立服务启动")
    print("=" * 60)
    print(f"版本: {APP_VERSION}")
    print(f"用户名: {os.getenv('WOL_USERNAME', 'admin')}")
    print(f"密码: {os.getenv('WOL_PASSWORD', 'admin123')}")
    print("-" * 60)
    print("🚀 启动服务器...")
    print("🌐 访问地址: http://localhost:12345")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=12345,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
