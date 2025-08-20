#!/usr/bin/env python3
"""
Wake-on-LAN 独立应用 - 美观版本
现代化的单页面应用设计，侧边导航，卡片布局
"""

import os
import sys
import time
import json
import secrets
import base64
import random
import string
import socket
import struct
import ipaddress
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
    import psutil
    import socket
    import struct
    import ipaddress
    print("✅ 所有依赖导入成功")
except ImportError as e:
    print(f"❌ 依赖导入失败: {e}")
    print("请安装依赖: pip install fastapi uvicorn psutil")
    sys.exit(1)

# 应用配置
APP_VERSION = "2.0.0-modern"
start_time = time.time()

# 简单的会话存储
sessions = {}

# IP白名单存储
ip_whitelist = {'127.0.0.1', '::1'}  # 默认包含本地回环地址

# 验证码存储 {session_id: {'code': 'ABCD', 'expires': datetime, 'attempts': 0}}
captcha_store = {}

# Wake-on-LAN功能
def send_magic_packet(mac_address: str, broadcast_ip: str = '255.255.255.255', port: int = 9):
    """发送魔术包唤醒设备"""
    # 清理MAC地址格式
    mac_address = mac_address.replace(':', '').replace('-', '').upper()
    
    # 验证MAC地址格式
    if len(mac_address) != 12:
        raise ValueError("无效的MAC地址格式")
    
    try:
        # 将MAC地址转换为字节
        mac_bytes = bytes.fromhex(mac_address)
    except ValueError:
        raise ValueError("无效的MAC地址格式")
    
    # 构造魔术包：6个0xFF + 16次重复的MAC地址
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    
    # 发送UDP包
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
                    # CIDR网段
                    network = ipaddress.ip_network(whitelist_ip, strict=False)
                    if client_ip in network:
                        return True
                else:
                    # 单个IP
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

# 验证码功能
def generate_captcha_code() -> str:
    """生成4位随机验证码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def create_captcha_image(code: str) -> str:
    """创建验证码图片的SVG格式，返回base64编码"""
    # 简单的SVG验证码
    svg_content = f'''
    <svg width="120" height="40" xmlns="http://www.w3.org/2000/svg">
        <rect width="120" height="40" fill="#f0f0f0" stroke="#ccc"/>
        <text x="60" y="25" font-family="Arial" font-size="18" font-weight="bold"
              text-anchor="middle" fill="#333">{code}</text>
        <!-- 添加一些干扰线 -->
        <line x1="10" y1="15" x2="110" y2="25" stroke="#999" stroke-width="1"/>
        <line x1="20" y1="30" x2="100" y2="10" stroke="#999" stroke-width="1"/>
    </svg>
    '''
    # 转换为base64
    svg_bytes = svg_content.encode('utf-8')
    svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"

def create_captcha_session() -> tuple[str, str]:
    """创建验证码会话，返回(session_id, image_data_url)"""
    session_id = secrets.token_urlsafe(16)
    code = generate_captcha_code()

    captcha_store[session_id] = {
        'code': code,
        'expires': datetime.utcnow() + timedelta(minutes=5),
        'attempts': 0
    }

    image_data = create_captcha_image(code)
    return session_id, image_data

def verify_captcha(session_id: str, user_input: str) -> bool:
    """验证验证码"""
    if session_id not in captcha_store:
        return False

    captcha_data = captcha_store[session_id]

    # 检查是否过期
    if datetime.utcnow() > captcha_data['expires']:
        del captcha_store[session_id]
        return False

    # 检查尝试次数
    if captcha_data['attempts'] >= 3:
        del captcha_store[session_id]
        return False

    # 验证码码
    captcha_data['attempts'] += 1

    if user_input.upper() == captcha_data['code']:
        del captcha_store[session_id]  # 验证成功后删除
        return True

    return False

def cleanup_expired_captchas():
    """清理过期的验证码"""
    now = datetime.utcnow()
    expired_keys = [k for k, v in captcha_store.items() if now > v['expires']]
    for key in expired_keys:
        del captcha_store[key]

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
    title="Wake-on-LAN Service (Modern)",
    description="内网设备远程唤醒服务 - 现代化版本",
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

# 登录页面模板
LOGIN_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake-on-LAN 登录</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px;
        }}
        .login-container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.2);
            padding: 50px;
            width: 100%;
            max-width: 450px;
            text-align: center;
        }}
        .login-header h1 {{
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .login-header p {{
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1em;
        }}
        .form-group {{
            margin-bottom: 25px;
            text-align: left;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }}
        input[type="text"], input[type="password"] {{
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.9);
        }}
        input[type="text"]:focus, input[type="password"]:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
            background: white;
        }}
        .login-button {{
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 10px;
        }}
        .login-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
        }}
        .info {{
            background: rgba(227, 242, 253, 0.8);
            border: 1px solid #bbdefb;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            font-size: 0.95em;
            color: #1565c0;
        }}
        .error {{
            background: rgba(248, 215, 218, 0.9);
            border: 1px solid #f5c6cb;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            color: #721c24;
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🌐 Wake-on-LAN</h1>
            <p>内网设备远程唤醒服务</p>
        </div>

        {error_message}

        <form method="post" action="/login">
            <div class="form-group">
                <label>用户名:</label>
                <input type="text" name="username" required placeholder="请输入用户名">
            </div>

            <div class="form-group">
                <label>密码:</label>
                <input type="password" name="password" required placeholder="请输入密码">
            </div>

            <div class="form-group">
                <label>验证码:</label>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="text" name="captcha" required placeholder="请输入验证码"
                           style="flex: 1;" maxlength="4">
                    <img src="{captcha_image}" alt="验证码"
                         style="border: 1px solid #ddd; border-radius: 4px; cursor: pointer;"
                         onclick="refreshCaptcha()" title="点击刷新验证码">
                </div>
                <small style="color: #666; font-size: 0.9em;">点击图片刷新验证码</small>
            </div>

            <input type="hidden" name="captcha_session" value="{captcha_session}">
            <button type="submit" class="login-button">登录</button>
        </form>

        <script>
            function refreshCaptcha() {{
                window.location.reload();
            }}
        </script>
    </div>
</body>
</html>"""

# 现代化主界面模板
MAIN_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake-on-LAN 管理界面</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        .app-container {{
            display: flex;
            min-height: 100vh;
        }}

        /* 侧边导航栏 */
        .sidebar {{
            width: 280px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
        }}

        .sidebar-header {{
            padding: 30px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }}

        .sidebar-header h1 {{
            font-size: 1.8em;
            margin-bottom: 5px;
        }}

        .sidebar-header p {{
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .nav-menu {{
            flex: 1;
            padding: 20px 0;
        }}

        .nav-item {{
            display: block;
            padding: 15px 25px;
            color: #555;
            text-decoration: none;
            border-left: 4px solid transparent;
            transition: all 0.3s ease;
            cursor: pointer;
        }}

        .nav-item:hover {{
            background: rgba(102, 126, 234, 0.1);
            border-left-color: #667eea;
            color: #667eea;
        }}

        .nav-item.active {{
            background: rgba(102, 126, 234, 0.15);
            border-left-color: #667eea;
            color: #667eea;
            font-weight: 600;
        }}

        .nav-item i {{
            margin-right: 12px;
            width: 20px;
            text-align: center;
        }}

        .sidebar-footer {{
            padding: 20px 25px;
            border-top: 1px solid #eee;
        }}

        .user-info {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }}

        .logout-btn {{
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }}

        .logout-btn:hover {{
            background: #c82333;
            transform: translateY(-1px);
        }}

        /* 主内容区域 */
        .main-content {{
            flex: 1;
            padding: 30px;
            overflow-y: auto;
        }}

        .content-header {{
            margin-bottom: 30px;
        }}

        .content-title {{
            font-size: 2.2em;
            color: white;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .content-subtitle {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1em;
        }}

        /* 标签页内容 */
        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
            animation: fadeIn 0.3s ease-in-out;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* 卡片样式 */
        .card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            margin-bottom: 25px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
        }}

        .card-header {{
            padding: 25px 30px 20px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-bottom: 1px solid #dee2e6;
        }}

        .card-header h3 {{
            color: #333;
            font-size: 1.4em;
            margin-bottom: 5px;
        }}

        .card-header p {{
            color: #666;
            font-size: 0.95em;
        }}

        .card-body {{
            padding: 30px;
        }}

        /* 网格布局 */
        .grid {{
            display: grid;
            gap: 25px;
        }}

        .grid-2 {{
            grid-template-columns: 1fr 1fr;
        }}

        .grid-3 {{
            grid-template-columns: 1fr 1fr 1fr;
        }}

        @media (max-width: 1024px) {{
            .grid-2, .grid-3 {{ grid-template-columns: 1fr; }}
        }}

        /* 表单样式 */
        .form-group {{
            margin-bottom: 20px;
        }}

        .form-group label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }}

        .form-group input, .form-group select, .form-group textarea {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: rgba(250, 251, 252, 0.8);
        }}

        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
            background: white;
        }}

        /* 按钮样式 */
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}

        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }}

        .btn-secondary {{
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
        }}

        .btn-danger {{
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        }}

        .btn-success {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }}

        .btn-sm {{
            padding: 8px 16px;
            font-size: 14px;
        }}

        /* 结果显示 */
        .result {{
            margin-top: 15px;
            padding: 15px 20px;
            border-radius: 12px;
            border-left: 4px solid;
        }}

        .result.success {{
            background: rgba(212, 237, 218, 0.8);
            border-left-color: #28a745;
            color: #155724;
        }}

        .result.error {{
            background: rgba(248, 215, 218, 0.8);
            border-left-color: #dc3545;
            color: #721c24;
        }}

        .result.info {{
            background: rgba(209, 236, 241, 0.8);
            border-left-color: #17a2b8;
            color: #0c5460;
        }}

        /* 加载动画 */
        .loading {{
            text-align: center;
            padding: 40px 20px;
        }}

        .spinner {{
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* 表格样式 */
        .table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .table th, .table td {{
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}

        .table th {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            font-weight: 600;
            color: #555;
        }}

        .table tr:hover {{
            background: rgba(102, 126, 234, 0.05);
        }}

        /* 状态标签 */
        .status-badge {{
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            display: inline-block;
        }}

        .status-badge.success {{
            background: rgba(212, 237, 218, 0.8);
            color: #155724;
        }}

        .status-badge.danger {{
            background: rgba(248, 215, 218, 0.8);
            color: #721c24;
        }}

        .status-badge.info {{
            background: rgba(209, 236, 241, 0.8);
            color: #0c5460;
        }}

        /* 空状态 */
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }}

        .empty-state i {{
            font-size: 4em;
            margin-bottom: 20px;
            opacity: 0.3;
        }}

        /* 响应式设计 */
        @media (max-width: 768px) {{
            .app-container {{
                flex-direction: column;
            }}

            .sidebar {{
                width: 100%;
                order: 2;
            }}

            .main-content {{
                order: 1;
                padding: 20px;
            }}

            .nav-menu {{
                display: flex;
                overflow-x: auto;
                padding: 10px 0;
            }}

            .nav-item {{
                white-space: nowrap;
                min-width: 120px;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <!-- 侧边导航栏 -->
        <div class="sidebar">
            <div class="sidebar-header">
                <h1>🌐 Wake-on-LAN</h1>
                <p>v{version}</p>
            </div>

            <nav class="nav-menu">
                <a class="nav-item active" onclick="showTab('wake')" id="nav-wake">
                    <i>⚡</i> 设备唤醒
                </a>
                <a class="nav-item" onclick="showTab('whitelist')" id="nav-whitelist">
                    <i>🛡️</i> IP白名单
                </a>
                <a class="nav-item" onclick="showTab('network')" id="nav-network">
                    <i>🌐</i> 网络接口
                </a>
                <a class="nav-item" onclick="showTab('api')" id="nav-api">
                    <i>🔗</i> API文档
                </a>
            </nav>

            <div class="sidebar-footer">
                <div class="user-info">
                    <div>
                        <strong>{username}</strong>
                        <div style="font-size: 0.8em; color: #666;">管理员</div>
                    </div>
                </div>
                <a href="/logout" class="logout-btn">退出登录</a>
            </div>
        </div>

        <!-- 主内容区域 -->
        <div class="main-content">
            <div class="content-header">
                <h1 class="content-title" id="pageTitle">设备唤醒</h1>
                <p class="content-subtitle" id="pageSubtitle">通过MAC地址远程唤醒网络设备</p>
            </div>

            <!-- 设备唤醒标签页 -->
            <div id="wake-tab" class="tab-content active">
                <div class="grid grid-2">
                    <div class="card">
                        <div class="card-header">
                            <h3>⚡ 简单唤醒</h3>
                            <p>输入MAC地址即可快速唤醒设备</p>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label for="simpleMac">MAC地址:</label>
                                <input type="text" id="simpleMac" placeholder="例: AA:BB:CC:DD:EE:FF"
                                       pattern="^([0-9A-Fa-f]{{2}}[:-]){{5}}([0-9A-Fa-f]{{2}})$">
                            </div>
                            <button class="btn" onclick="simpleWake()">
                                <span>⚡</span> 唤醒设备
                            </button>
                            <div id="simpleResult"></div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3>🔧 高级唤醒</h3>
                            <p>自定义网络参数进行精确唤醒</p>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label for="advancedMac">MAC地址:</label>
                                <input type="text" id="advancedMac" placeholder="例: AA:BB:CC:DD:EE:FF"
                                       pattern="^([0-9A-Fa-f]{{2}}[:-]){{5}}([0-9A-Fa-f]{{2}})$">
                            </div>
                            <div class="form-group">
                                <label for="interface">网络接口:</label>
                                <select id="interface">
                                    <option value="">自动选择</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="broadcast">广播地址:</label>
                                <input type="text" id="broadcast" placeholder="例: 192.168.1.255">
                            </div>
                            <div class="form-group">
                                <label for="port">端口:</label>
                                <input type="number" id="port" value="9" min="1" max="65535">
                            </div>
                            <button class="btn" onclick="advancedWake()">
                                <span>🚀</span> 高级唤醒
                            </button>
                            <div id="advancedResult"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- IP白名单标签页 -->
            <div id="whitelist-tab" class="tab-content">
                <div class="grid grid-2" style="margin-bottom: 30px;">
                    <div class="card">
                        <div class="card-header">
                            <h3>➕ 添加IP白名单</h3>
                            <p>添加可信IP地址到白名单</p>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label for="newIp">IP地址或CIDR网段:</label>
                                <input type="text" id="newIp" placeholder="例: 192.168.1.100 或 192.168.1.0/24">
                            </div>
                            <div class="form-group">
                                <label for="ipDescription">描述 (可选):</label>
                                <input type="text" id="ipDescription" placeholder="例: 办公室服务器">
                            </div>
                            <button class="btn" onclick="addIpToWhitelist()">
                                <span>➕</span> 添加到白名单
                            </button>
                            <div id="addIpResult"></div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3>📊 当前状态</h3>
                            <p>查看当前访问IP的白名单状态</p>
                        </div>
                        <div class="card-body">
                            <div id="currentIpStatus">
                                <div class="loading">
                                    <div class="spinner"></div>
                                    <p>正在检查当前IP状态...</p>
                                </div>
                            </div>
                            <button class="btn btn-secondary" onclick="checkCurrentIpStatus()">
                                <span>🔍</span> 检查当前IP
                            </button>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3>📋 白名单管理</h3>
                        <p>管理当前的IP白名单项目</p>
                    </div>
                    <div class="card-body">
                        <div id="whitelistTable">
                            <div class="loading">
                                <div class="spinner"></div>
                                <p>正在加载白名单...</p>
                            </div>
                        </div>
                        <button class="btn btn-secondary" onclick="loadWhitelist()">
                            <span>🔄</span> 刷新白名单
                        </button>
                    </div>
                </div>
            </div>

            <!-- 网络接口标签页 -->
            <div id="network-tab" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3>🌐 网络接口信息</h3>
                        <p>查看系统中所有可用的网络接口</p>
                    </div>
                    <div class="card-body">
                        <div id="interfacesList">
                            <div class="loading">
                                <div class="spinner"></div>
                                <p>正在加载网络接口...</p>
                            </div>
                        </div>
                        <button class="btn btn-secondary" onclick="loadInterfaces()">
                            <span>🔄</span> 刷新接口
                        </button>
                    </div>
                </div>
            </div>

            <!-- API文档标签页 -->
            <div id="api-tab" class="tab-content">
                <div class="grid grid-2">
                    <div class="card">
                        <div class="card-header">
                            <h3>📚 API文档</h3>
                            <p>查看完整的API接口文档</p>
                        </div>
                        <div class="card-body">
                            <div style="margin-bottom: 20px;">
                                <a href="/docs" target="_blank" class="btn" style="margin-right: 10px; margin-bottom: 10px;">
                                    <span>📖</span> Swagger UI
                                </a>
                                <a href="/redoc" target="_blank" class="btn btn-secondary" style="margin-bottom: 10px;">
                                    <span>📋</span> ReDoc
                                </a>
                            </div>
                            <div style="background: rgba(0,0,0,0.05); padding: 15px; border-radius: 8px;">
                                <h4 style="margin-bottom: 10px;">主要端点:</h4>
                                <ul style="list-style: none; padding: 0;">
                                    <li style="margin-bottom: 5px;"><code>POST /wake</code> - 简单设备唤醒</li>
                                    <li style="margin-bottom: 5px;"><code>POST /wake/advanced</code> - 高级设备唤醒</li>
                                    <li style="margin-bottom: 5px;"><code>GET /whitelist</code> - 获取IP白名单</li>
                                    <li style="margin-bottom: 5px;"><code>GET /interfaces</code> - 获取网络接口</li>
                                    <li style="margin-bottom: 5px;"><code>GET /health</code> - 健康检查</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3>🔧 系统信息</h3>
                            <p>查看服务运行状态和系统信息</p>
                        </div>
                        <div class="card-body">
                            <div id="systemInfo">
                                <div class="loading">
                                    <div class="spinner"></div>
                                    <p>正在加载系统信息...</p>
                                </div>
                            </div>
                            <button class="btn btn-secondary" onclick="loadSystemInfo()">
                                <span>🔄</span> 刷新信息
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {{
            loadInterfaces();
            loadWhitelist();
            checkCurrentIpStatus();
            loadSystemInfo();
        }});

        // 标签页切换功能
        function showTab(tabName) {{
            // 隐藏所有标签页内容
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));

            // 移除所有导航项的active类
            const navItems = document.querySelectorAll('.nav-item');
            navItems.forEach(item => item.classList.remove('active'));

            // 显示选中的标签页
            document.getElementById(tabName + '-tab').classList.add('active');
            document.getElementById('nav-' + tabName).classList.add('active');

            // 更新页面标题
            const titles = {{
                'wake': ['设备唤醒', '通过MAC地址远程唤醒网络设备'],
                'whitelist': ['IP白名单管理', '管理可免认证访问的IP地址'],
                'network': ['网络接口', '查看系统网络接口信息'],
                'api': ['API文档', '查看接口文档和系统信息']
            }};

            if (titles[tabName]) {{
                document.getElementById('pageTitle').textContent = titles[tabName][0];
                document.getElementById('pageSubtitle').textContent = titles[tabName][1];
            }}
        }}

        // 加载网络接口
        async function loadInterfaces() {{
            const interfacesDiv = document.getElementById('interfacesList');
            const interfaceSelect = document.getElementById('interface');

            interfacesDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在加载网络接口...</p></div>';

            try {{
                const response = await fetch('/interfaces');
                if (response.ok) {{
                    const data = await response.json();

                    // 更新接口列表显示
                    let html = '<div class="grid grid-2">';
                    data.interfaces.forEach(iface => {{
                        html += `<div class="card">`;
                        html += `<div class="card-header"><h3>🔌 ${{iface.name}}</h3></div>`;
                        html += `<div class="card-body">`;
                        iface.addresses.forEach(addr => {{
                            html += `<div style="margin-bottom: 10px; padding: 10px; background: rgba(0,0,0,0.05); border-radius: 8px;">`;
                            html += `<strong>${{addr.family}}:</strong> <code>${{addr.address}}</code><br>`;
                            if (addr.netmask) html += `<small>子网掩码: ${{addr.netmask}}</small><br>`;
                            if (addr.broadcast) html += `<small>广播地址: ${{addr.broadcast}}</small>`;
                            html += `</div>`;
                        }});
                        html += `</div></div>`;
                    }});
                    html += '</div>';
                    interfacesDiv.innerHTML = html;

                    // 更新接口选择下拉框
                    if (interfaceSelect) {{
                        interfaceSelect.innerHTML = '<option value="">自动选择</option>';
                        data.interfaces.forEach(iface => {{
                            interfaceSelect.innerHTML += `<option value="${{iface.name}}">${{iface.name}}</option>`;
                        }});
                    }}
                }} else {{
                    interfacesDiv.innerHTML = '<div class="result error">加载网络接口失败</div>';
                }}
            }} catch (error) {{
                interfacesDiv.innerHTML = `<div class="result error">加载网络接口失败: ${{error.message}}</div>`;
            }}
        }}

        // 加载系统信息
        async function loadSystemInfo() {{
            const systemDiv = document.getElementById('systemInfo');
            if (!systemDiv) return;

            systemDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在加载系统信息...</p></div>';

            try {{
                const response = await fetch('/health');
                if (response.ok) {{
                    const data = await response.json();

                    systemDiv.innerHTML = `
                        <div style="background: rgba(0,0,0,0.05); padding: 15px; border-radius: 8px;">
                            <h4 style="margin-bottom: 15px;">服务状态</h4>
                            <div style="margin-bottom: 10px;">
                                <span class="status-badge success">✅ ${{data.status}}</span>
                            </div>
                            <div style="margin-bottom: 8px;"><strong>版本:</strong> ${{data.version}}</div>
                            <div style="margin-bottom: 8px;"><strong>运行时间:</strong> ${{data.uptime}}</div>
                            <div style="margin-bottom: 8px;"><strong>会话数:</strong> ${{data.sessions || 0}}</div>
                            <div><strong>更新时间:</strong> ${{new Date(data.timestamp).toLocaleString()}}</div>
                        </div>
                    `;
                }} else {{
                    systemDiv.innerHTML = '<div class="result error">加载系统信息失败</div>';
                }}
            }} catch (error) {{
                systemDiv.innerHTML = `<div class="result error">加载系统信息失败: ${{error.message}}</div>`;
            }}
        }}

        // 简单唤醒
        async function simpleWake() {{
            const mac = document.getElementById('simpleMac').value.trim();
            const resultDiv = document.getElementById('simpleResult');

            if (!mac) {{
                resultDiv.innerHTML = '<div class="result error">请输入MAC地址</div>';
                return;
            }}

            if (!isValidMac(mac)) {{
                resultDiv.innerHTML = '<div class="result error">MAC地址格式不正确</div>';
                return;
            }}

            resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在发送唤醒包...</p></div>';

            try {{
                const response = await fetch('/wake', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ mac_address: mac }})
                }});

                const data = await response.json();
                if (response.ok && data.success) {{
                    resultDiv.innerHTML = `<div class="result success"><strong>✅ 唤醒成功!</strong><br>${{data.message}}</div>`;
                }} else {{
                    resultDiv.innerHTML = `<div class="result error"><strong>❌ 唤醒失败</strong><br>${{data.message || '未知错误'}}</div>`;
                }}
            }} catch (error) {{
                resultDiv.innerHTML = `<div class="result error"><strong>❌ 请求失败</strong><br>${{error.message}}</div>`;
            }}
        }}

        // 高级唤醒
        async function advancedWake() {{
            const mac = document.getElementById('advancedMac').value.trim();
            const interface = document.getElementById('interface').value;
            const broadcast = document.getElementById('broadcast').value.trim();
            const port = parseInt(document.getElementById('port').value);
            const resultDiv = document.getElementById('advancedResult');

            if (!mac) {{
                resultDiv.innerHTML = '<div class="result error">请输入MAC地址</div>';
                return;
            }}

            if (!isValidMac(mac)) {{
                resultDiv.innerHTML = '<div class="result error">MAC地址格式不正确</div>';
                return;
            }}

            resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在发送唤醒包...</p></div>';

            const requestData = {{ mac_address: mac }};
            if (interface) requestData.interface = interface;
            if (broadcast) requestData.broadcast_ip = broadcast;
            if (port && port !== 9) requestData.port = port;

            try {{
                const response = await fetch('/wake/advanced', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(requestData)
                }});

                const data = await response.json();
                if (response.ok && data.success) {{
                    resultDiv.innerHTML = `<div class="result success"><strong>✅ 高级唤醒成功!</strong><br>${{data.message}}</div>`;
                }} else {{
                    resultDiv.innerHTML = `<div class="result error"><strong>❌ 高级唤醒失败</strong><br>${{data.message || '未知错误'}}</div>`;
                }}
            }} catch (error) {{
                resultDiv.innerHTML = `<div class="result error"><strong>❌ 请求失败</strong><br>${{error.message}}</div>`;
            }}
        }}

        // 验证MAC地址格式
        function isValidMac(mac) {{
            const macRegex = /^([0-9A-Fa-f]{{2}}[:-]){{5}}([0-9A-Fa-f]{{2}})$/;
            return macRegex.test(mac);
        }}

        // IP白名单管理函数
        async function loadWhitelist() {{
            const whitelistDiv = document.getElementById('whitelistTable');
            if (!whitelistDiv) return;

            whitelistDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在加载白名单...</p></div>';

            try {{
                const response = await fetch('/whitelist');
                if (response.ok) {{
                    const data = await response.json();

                    if (data.length === 0) {{
                        whitelistDiv.innerHTML = `
                            <div class="empty-state">
                                <div style="font-size: 3em; margin-bottom: 20px;">🛡️</div>
                                <h3>暂无白名单IP</h3>
                                <p>添加IP地址到白名单后，这些IP可以无需登录直接调用API</p>
                            </div>
                        `;
                    }} else {{
                        let tableHtml = `
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>IP地址/网段</th>
                                        <th>添加时间</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;

                        data.forEach(ip => {{
                            tableHtml += `
                                <tr>
                                    <td><code>${{ip}}</code></td>
                                    <td>${{new Date().toLocaleString()}}</td>
                                    <td>
                                        <button class="btn btn-danger btn-sm" onclick="removeIpFromWhitelist('${{ip}}')">
                                            <span>🗑️</span> 移除
                                        </button>
                                    </td>
                                </tr>
                            `;
                        }});

                        tableHtml += '</tbody></table>';
                        whitelistDiv.innerHTML = tableHtml;
                    }}
                }} else {{
                    whitelistDiv.innerHTML = '<div class="result error">加载白名单失败</div>';
                }}
            }} catch (error) {{
                whitelistDiv.innerHTML = `<div class="result error">加载白名单失败: ${{error.message}}</div>`;
            }}
        }}

        async function addIpToWhitelist() {{
            const ip = document.getElementById('newIp').value.trim();
            const description = document.getElementById('ipDescription').value.trim();
            const resultDiv = document.getElementById('addIpResult');

            if (!ip) {{
                resultDiv.innerHTML = '<div class="result error">请输入IP地址或CIDR网段</div>';
                return;
            }}

            resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在添加到白名单...</p></div>';

            try {{
                const response = await fetch('/whitelist/add', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ ip: ip, description: description }})
                }});

                const data = await response.json();
                if (response.ok && data.success) {{
                    resultDiv.innerHTML = `<div class="result success"><strong>✅ 添加成功!</strong><br>${{data.message}}</div>`;

                    // 清空输入框
                    document.getElementById('newIp').value = '';
                    document.getElementById('ipDescription').value = '';

                    // 刷新白名单
                    loadWhitelist();
                    checkCurrentIpStatus();
                }} else {{
                    resultDiv.innerHTML = `<div class="result error"><strong>❌ 添加失败</strong><br>${{data.message || '未知错误'}}</div>`;
                }}
            }} catch (error) {{
                resultDiv.innerHTML = `<div class="result error"><strong>❌ 请求失败</strong><br>${{error.message}}</div>`;
            }}
        }}

        async function removeIpFromWhitelist(ip) {{
            if (!confirm(`确定要从白名单中移除 ${{ip}} 吗？`)) {{
                return;
            }}

            try {{
                const response = await fetch('/whitelist/remove', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ ip: ip }})
                }});

                const data = await response.json();
                if (response.ok && data.success) {{
                    loadWhitelist();
                    checkCurrentIpStatus();

                    const resultDiv = document.getElementById('addIpResult');
                    if (resultDiv) {{
                        resultDiv.innerHTML = `<div class="result success"><strong>✅ 移除成功!</strong><br>已从白名单移除 ${{ip}}</div>`;
                        setTimeout(() => {{ resultDiv.innerHTML = ''; }}, 3000);
                    }}
                }} else {{
                    alert(`移除失败: ${{data.message || '未知错误'}}`);
                }}
            }} catch (error) {{
                alert(`移除失败: ${{error.message}}`);
            }}
        }}

        async function checkCurrentIpStatus() {{
            const statusDiv = document.getElementById('currentIpStatus');
            if (!statusDiv) return;

            statusDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在检查当前IP状态...</p></div>';

            try {{
                const response = await fetch('/whitelist/check');
                const data = await response.json();

                const statusClass = data.in_whitelist ? 'success' : 'danger';
                const statusIcon = data.in_whitelist ? '✅' : '❌';

                statusDiv.innerHTML = `
                    <div style="background: rgba(0,0,0,0.05); padding: 15px; border-radius: 8px;">
                        <div style="margin-bottom: 10px;">
                            <strong>当前IP:</strong> <code>${{data.client_ip}}</code>
                        </div>
                        <div class="status-badge ${{statusClass}}">
                            ${{statusIcon}} ${{data.message}}
                        </div>
                    </div>
                `;
            }} catch (error) {{
                statusDiv.innerHTML = `<div class="result error">检查失败: ${{error.message}}</div>`;
            }}
        }}
    </script>
</body>
</html>"""

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """首页"""
    # 清理过期验证码
    cleanup_expired_captchas()

    session_id = request.cookies.get("session_id")
    session_data = verify_session(session_id) if session_id else None

    if session_data:
        return MAIN_PAGE.format(
            version=APP_VERSION,
            username=session_data["username"]
        )
    else:
        # 生成验证码
        captcha_session, captcha_image = create_captcha_session()
        return LOGIN_PAGE.format(
            captcha_session=captcha_session,
            captcha_image=captcha_image,
            error_message=""
        )

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...),
                captcha: str = Form(...), captcha_session: str = Form(...)):
    """登录处理 - 包含验证码验证和后台密码校验"""

    def create_error_response(error_msg: str):
        """创建错误响应"""
        captcha_session_new, captcha_image_new = create_captcha_session()
        error_html = f'<div class="error"><strong>登录失败:</strong> {error_msg}</div>'
        return LOGIN_PAGE.format(
            captcha_session=captcha_session_new,
            captcha_image=captcha_image_new,
            error_message=error_html
        )

    # 1. 验证码验证
    if not verify_captcha(captcha_session, captcha):
        return create_error_response("验证码错误或已过期")

    # 2. 后台用户名密码校验
    expected_username = os.getenv("WOL_USERNAME", "admin")
    expected_password = os.getenv("WOL_PASSWORD", "admin123")

    # 防止时序攻击的安全比较
    username_valid = secrets.compare_digest(username.encode(), expected_username.encode())
    password_valid = secrets.compare_digest(password.encode(), expected_password.encode())

    if username_valid and password_valid:
        # 登录成功
        session_id = create_session(username)
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie("session_id", session_id, max_age=3600, httponly=True, secure=False)
        return response
    else:
        # 登录失败 - 不透露具体是用户名还是密码错误
        return create_error_response("用户名或密码错误")

@app.get("/logout")
async def logout(request: Request):
    """退出登录"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_id")
    return response

@app.get("/captcha/refresh")
async def refresh_captcha():
    """刷新验证码"""
    cleanup_expired_captchas()
    captcha_session, captcha_image = create_captcha_session()
    return {
        "captcha_session": captcha_session,
        "captcha_image": captcha_image
    }

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
    client_ip = get_client_ip(request)

    # 检查认证：会话或白名单
    if not verify_session(session_id) and not is_ip_in_whitelist(client_ip):
        raise HTTPException(status_code=401, detail="需要登录")

    try:
        interfaces = get_network_interfaces()
        return {"interfaces": interfaces, "count": len(interfaces)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取网络接口失败: {str(e)}")

@app.post("/wake")
async def wake_device(request: Request, wake_data: dict):
    """简单设备唤醒"""
    session_id = request.cookies.get("session_id")
    client_ip = get_client_ip(request)

    # 检查认证：会话或白名单
    if not verify_session(session_id) and not is_ip_in_whitelist(client_ip):
        raise HTTPException(status_code=401, detail="需要登录")

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

@app.post("/wake/advanced")
async def wake_device_advanced(request: Request, wake_data: dict):
    """高级设备唤醒"""
    session_id = request.cookies.get("session_id")
    client_ip = get_client_ip(request)

    # 检查认证：会话或白名单
    if not verify_session(session_id) and not is_ip_in_whitelist(client_ip):
        raise HTTPException(status_code=401, detail="需要登录")

    mac_address = wake_data.get("mac_address")
    broadcast_ip = wake_data.get("broadcast_ip", "255.255.255.255")
    port = wake_data.get("port", 9)
    interface = wake_data.get("interface")

    if not mac_address:
        raise HTTPException(status_code=400, detail="缺少MAC地址")

    try:
        send_magic_packet(mac_address, broadcast_ip, port)
        return {
            "success": True,
            "message": f"成功向 {mac_address} 发送高级唤醒包",
            "mac_address": mac_address,
            "broadcast_ip": broadcast_ip,
            "port": port,
            "interface": interface
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "mac_address": mac_address
        }

# IP白名单管理API
@app.get("/whitelist")
async def get_whitelist(request: Request):
    """获取IP白名单列表"""
    session_id = request.cookies.get("session_id")
    if not verify_session(session_id):
        raise HTTPException(status_code=401, detail="需要登录")

    return sorted(list(ip_whitelist))

@app.post("/whitelist/add")
async def add_ip_whitelist(request: Request, ip_data: dict):
    """添加IP到白名单"""
    session_id = request.cookies.get("session_id")
    if not verify_session(session_id):
        raise HTTPException(status_code=401, detail="需要登录")

    ip = ip_data.get("ip")
    if not ip:
        raise HTTPException(status_code=400, detail="缺少IP地址")

    if add_ip_to_whitelist(ip):
        return {
            "success": True,
            "message": f"成功添加IP {ip} 到白名单",
            "ip": ip,
            "whitelist": sorted(list(ip_whitelist))
        }
    else:
        return {
            "success": False,
            "message": f"添加IP {ip} 失败，可能是无效的IP格式",
            "ip": ip
        }

@app.post("/whitelist/remove")
async def remove_ip_whitelist(request: Request, ip_data: dict):
    """从白名单移除IP"""
    session_id = request.cookies.get("session_id")
    if not verify_session(session_id):
        raise HTTPException(status_code=401, detail="需要登录")

    ip = ip_data.get("ip")
    if not ip:
        raise HTTPException(status_code=400, detail="缺少IP地址")

    if remove_ip_from_whitelist(ip):
        return {
            "success": True,
            "message": f"成功从白名单移除IP {ip}",
            "ip": ip,
            "whitelist": sorted(list(ip_whitelist))
        }
    else:
        return {
            "success": False,
            "message": f"移除IP {ip} 失败，IP不在白名单中",
            "ip": ip
        }

@app.get("/whitelist/check")
async def check_ip_whitelist(request: Request):
    """检查IP白名单状态"""
    client_ip = get_client_ip(request)
    in_whitelist = is_ip_in_whitelist(client_ip)

    return {
        "client_ip": client_ip,
        "in_whitelist": in_whitelist,
        "message": "IP在白名单中，可免认证访问" if in_whitelist else "IP不在白名单中，需要登录认证"
    }

def main():
    """主函数"""
    print("=" * 60)
    print("🌐 Wake-on-LAN 现代化服务启动")
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
