#!/usr/bin/env python3
"""
Wake-on-LAN Service - 部署版本
专门为Docker部署优化，避免复杂的导入问题
"""

import os
import sys
import time
import json
import secrets
import socket
import struct
import ipaddress
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# 设置环境变量
os.environ.setdefault('WOL_USERNAME', 'admin')
os.environ.setdefault('WOL_PASSWORD', 'admin123')
os.environ.setdefault('WOL_SESSION_SECRET', 'wake-on-lan-deploy-secret')

try:
    from fastapi import FastAPI, HTTPException, Request, Form
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
    import uvicorn
    import psutil
    print("✅ 所有依赖导入成功")
except ImportError as e:
    print(f"❌ 依赖导入失败: {e}")
    sys.exit(1)

# 应用配置
APP_VERSION = "2.0.0-deploy"
start_time = time.time()

# 简单的会话存储
sessions = {}

# IP白名单存储
ip_whitelist = {'127.0.0.1', '::1'}

# Wake-on-LAN功能
def send_magic_packet(mac_address: str, broadcast_ip: str = '255.255.255.255', port: int = 9):
    """发送魔术包唤醒设备"""
    mac_address = mac_address.replace(':', '').replace('-', '').upper()
    
    if len(mac_address) != 12:
        raise ValueError("无效的MAC地址格式")
    
    try:
        mac_bytes = bytes.fromhex(mac_address)
    except ValueError:
        raise ValueError("无效的MAC地址格式")
    
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        sock.sendto(magic_packet, (broadcast_ip, port))
        return True
    except Exception as e:
        raise Exception(f"发送魔术包失败: {str(e)}")
    finally:
        sock.close()

def get_network_interfaces():
    """获取网络接口信息"""
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
    
    return interfaces

def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    return request.client.host if request.client else "unknown"

def is_ip_in_whitelist(ip: str) -> bool:
    """检查IP是否在白名单中"""
    if not ip or ip == "unknown":
        return False
    
    try:
        client_ip = ipaddress.ip_address(ip)
        
        for whitelist_ip in ip_whitelist:
            try:
                if '/' in whitelist_ip:
                    network = ipaddress.ip_network(whitelist_ip, strict=False)
                    if client_ip in network:
                        return True
                else:
                    if client_ip == ipaddress.ip_address(whitelist_ip):
                        return True
            except ValueError:
                continue
        
        return False
    except ValueError:
        return False

def add_ip_to_whitelist(ip: str) -> bool:
    """添加IP到白名单"""
    try:
        if '/' in ip:
            ipaddress.ip_network(ip, strict=False)
        else:
            ipaddress.ip_address(ip)
        
        ip_whitelist.add(ip)
        return True
    except ValueError:
        return False

def remove_ip_from_whitelist(ip: str) -> bool:
    """从白名单移除IP"""
    if ip in ip_whitelist:
        ip_whitelist.remove(ip)
        return True
    return False

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

# 创建FastAPI应用
app = FastAPI(
    title="Wake-on-LAN Service (Deploy)",
    description="内网设备远程唤醒服务 - 部署版本",
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

# 简单的HTML页面
SIMPLE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake-on-LAN Service</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .section {{ margin: 20px 0; padding: 20px; background: #f9f9f9; border-radius: 5px; }}
        input, button {{ padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }}
        button {{ background: #007bff; color: white; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
        .result {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
        .success {{ background: #d4edda; color: #155724; }}
        .error {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 Wake-on-LAN Service</h1>
        <p style="text-align: center;">版本: {version} | 状态: 运行中</p>
        
        <div class="section">
            <h3>⚡ 设备唤醒</h3>
            <input type="text" id="macAddress" placeholder="MAC地址 (例: AA:BB:CC:DD:EE:FF)" style="width: 300px;">
            <button onclick="wakeDevice()">唤醒设备</button>
            <div id="wakeResult"></div>
        </div>
        
        <div class="section">
            <h3>🔗 API链接</h3>
            <p>
                <a href="/health">健康检查</a> | 
                <a href="/interfaces">网络接口</a> | 
                <a href="/docs">API文档</a>
            </p>
        </div>
        
        <div class="section">
            <h3>📋 使用说明</h3>
            <p>1. 输入目标设备的MAC地址</p>
            <p>2. 点击"唤醒设备"按钮</p>
            <p>3. 查看操作结果</p>
        </div>
    </div>
    
    <script>
        async function wakeDevice() {{
            const mac = document.getElementById('macAddress').value.trim();
            const resultDiv = document.getElementById('wakeResult');
            
            if (!mac) {{
                resultDiv.innerHTML = '<div class="result error">请输入MAC地址</div>';
                return;
            }}
            
            try {{
                const response = await fetch('/wake', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ mac_address: mac }})
                }});
                
                const data = await response.json();
                if (data.success) {{
                    resultDiv.innerHTML = `<div class="result success">✅ ${{data.message}}</div>`;
                }} else {{
                    resultDiv.innerHTML = `<div class="result error">❌ ${{data.message}}</div>`;
                }}
            }} catch (error) {{
                resultDiv.innerHTML = `<div class="result error">❌ 请求失败: ${{error.message}}</div>`;
            }}
        }}
    </script>
</body>
</html>"""

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def root():
    """首页"""
    return SIMPLE_HTML.format(version=APP_VERSION)

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
async def get_interfaces():
    """获取网络接口"""
    try:
        interfaces = get_network_interfaces()
        return {"interfaces": interfaces, "count": len(interfaces)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取网络接口失败: {str(e)}")

@app.post("/wake")
async def wake_device(wake_data: dict):
    """设备唤醒"""
    mac_address = wake_data.get("mac_address")
    if not mac_address:
        raise HTTPException(status_code=400, detail="缺少MAC地址")
    
    try:
        send_magic_packet(mac_address)
        return {
            "success": True,
            "message": f"成功向 {mac_address} 发送唤醒包",
            "mac_address": mac_address
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "mac_address": mac_address
        }

if __name__ == "__main__":
    print("🚀 启动Wake-on-LAN部署版本...")
    uvicorn.run(app, host="0.0.0.0", port=12345)
