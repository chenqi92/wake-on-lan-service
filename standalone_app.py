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
APP_VERSION = "1.0.1-standalone"
start_time = time.time()

# 简单的会话存储
sessions = {}

# IP白名单存储
ip_whitelist = {'127.0.0.1', '::1'}  # 默认包含本地回环地址

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

# HTML模板 - 使用双花括号避免格式化冲突
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
        .container {{
            background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px; width: 100%; max-width: 400px;
        }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #333; font-size: 2em; margin-bottom: 10px; }}
        .form-group {{ margin-bottom: 20px; }}
        label {{ display: block; margin-bottom: 8px; font-weight: 600; color: #555; }}
        input {{ width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 8px; font-size: 16px; }}
        input:focus {{ outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }}
        button {{
            width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;
        }}
        button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3); }}
        .info {{ background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 15px; margin-bottom: 20px; color: #1565c0; }}
        .error {{ background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 15px; margin-bottom: 20px; color: #721c24; }}
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
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px;
        }}
        .container {{
            max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; display: flex; justify-content: space-between; align-items: center;
        }}
        .header h1 {{ font-size: 2.5em; }}
        .logout-btn {{
            background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3);
            padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 0.9em;
        }}
        .content {{ padding: 40px; }}
        .section {{
            margin-bottom: 40px; padding: 30px; background: #f8f9fa; border-radius: 10px;
            border-left: 5px solid #667eea;
        }}
        .section h2 {{ color: #333; margin-bottom: 20px; font-size: 1.5em; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
        @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}

        .form-group {{ margin-bottom: 20px; }}
        .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; color: #555; }}
        .form-group input, .form-group select {{
            width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 8px;
            font-size: 16px; transition: all 0.3s ease;
        }}
        .form-group input:focus, .form-group select:focus {{
            outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; padding: 12px 24px; border-radius: 8px;
            font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.3s ease;
        }}
        button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3); }}

        .result {{ margin-top: 15px; padding: 15px; border-radius: 8px; }}
        .result.success {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
        .result.error {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
        .result.info {{ background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }}

        .loading {{ text-align: center; padding: 20px; }}
        .spinner {{ border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%;
                   width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 10px; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}

        .whitelist-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; background: white;
                           border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .whitelist-table th, .whitelist-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        .whitelist-table th {{ background: #f8f9fa; font-weight: 600; color: #555; }}
        .whitelist-table tr:hover {{ background: #f8f9fa; }}

        .remove-btn {{ background: #dc3545; color: white; border: none; padding: 6px 12px;
                      border-radius: 4px; cursor: pointer; font-size: 12px; }}
        .remove-btn:hover {{ background: #c82333; }}

        .ip-status {{ padding: 8px 12px; border-radius: 6px; font-weight: 600; display: inline-block; margin-top: 10px; }}
        .ip-status.in-whitelist {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .ip-status.not-in-whitelist {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}

        .empty-whitelist {{ text-align: center; padding: 40px; color: #666; font-style: italic; }}
        .api-link {{ color: #667eea; text-decoration: none; margin-right: 20px; }}
        .api-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🌐 Wake-on-LAN</h1>
                <p>内网设备远程唤醒服务 v{version}</p>
            </div>
            <div>
                <span id="userInfo">当前用户: <strong>{username}</strong></span>
                <a href="/logout" class="logout-btn" style="margin-left: 15px;">退出登录</a>
            </div>
        </div>
        <div class="content">
            <!-- IP白名单管理 -->
            <div class="section">
                <h2>🛡️ IP白名单管理</h2>
                <p style="margin-bottom: 20px; color: #666;">白名单中的IP地址可以无需登录直接调用API接口</p>

                <div class="grid" style="margin-bottom: 30px;">
                    <div>
                        <h3>添加IP到白名单</h3>
                        <div class="form-group">
                            <label for="newIp">IP地址或CIDR网段:</label>
                            <input type="text" id="newIp" placeholder="例: 192.168.1.100 或 192.168.1.0/24">
                        </div>
                        <div class="form-group">
                            <label for="ipDescription">描述 (可选):</label>
                            <input type="text" id="ipDescription" placeholder="例: 办公室服务器">
                        </div>
                        <button onclick="addIpToWhitelist()">添加到白名单</button>
                        <div id="addIpResult"></div>
                    </div>

                    <div>
                        <h3>当前状态</h3>
                        <div id="currentIpStatus">
                            <div class="loading">
                                <div class="spinner"></div>
                                <p>正在检查当前IP状态...</p>
                            </div>
                        </div>
                        <button onclick="checkCurrentIpStatus()">检查当前IP</button>
                    </div>
                </div>

                <div>
                    <h3>当前白名单</h3>
                    <div id="whitelistTable">
                        <div class="loading">
                            <div class="spinner"></div>
                            <p>正在加载白名单...</p>
                        </div>
                    </div>
                    <button onclick="loadWhitelist()">刷新白名单</button>
                </div>
            </div>

            <!-- 设备唤醒 -->
            <div class="section">
                <h2>⚡ 设备唤醒</h2>
                <div class="grid">
                    <div>
                        <h3>简单唤醒</h3>
                        <div class="form-group">
                            <label for="simpleMac">MAC地址:</label>
                            <input type="text" id="simpleMac" placeholder="例: AA:BB:CC:DD:EE:FF"
                                   pattern="^([0-9A-Fa-f]{{2}}[:-]){{5}}([0-9A-Fa-f]{{2}})$">
                        </div>
                        <button onclick="simpleWake()">唤醒设备</button>
                        <div id="simpleResult"></div>
                    </div>

                    <div>
                        <h3>高级唤醒</h3>
                        <div class="form-group">
                            <label for="advancedMac">MAC地址:</label>
                            <input type="text" id="advancedMac" placeholder="例: AA:BB:CC:DD:EE:FF"
                                   pattern="^([0-9A-Fa-f]{{2}}[:-]){{5}}([0-9A-Fa-f]{{2}})$">
                        </div>
                        <div class="form-group">
                            <label for="interface">网络接口 (可选):</label>
                            <select id="interface">
                                <option value="">自动选择</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="broadcast">广播地址 (可选):</label>
                            <input type="text" id="broadcast" placeholder="例: 192.168.1.255">
                        </div>
                        <div class="form-group">
                            <label for="port">端口:</label>
                            <input type="number" id="port" value="9" min="1" max="65535">
                        </div>
                        <button onclick="advancedWake()">高级唤醒</button>
                        <div id="advancedResult"></div>
                    </div>
                </div>
            </div>

            <!-- 网络接口信息 -->
            <div class="section">
                <h2>🌐 网络接口</h2>
                <div id="interfacesList">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>正在加载网络接口...</p>
                    </div>
                </div>
                <button onclick="loadInterfaces()">刷新接口</button>
            </div>

            <!-- API接口 -->
            <div class="section">
                <h2>🔗 API接口</h2>
                <p style="margin: 15px 0;">
                    <a href="/health" class="api-link">健康检查</a>
                    <a href="/interfaces" class="api-link">网络接口</a>
                    <a href="/docs" class="api-link">API文档</a>
                    <a href="/redoc" class="api-link">ReDoc文档</a>
                </p>
            </div>
        </div>
    </div>

    <script>
        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {{
            loadInterfaces();
            loadWhitelist();
            checkCurrentIpStatus();
        }});

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
                    let html = '<div style="display: grid; gap: 15px;">';
                    data.interfaces.forEach(iface => {{
                        html += `<div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e1e5e9;">`;
                        html += `<h4 style="color: #333; margin-bottom: 10px;">🔌 ${{iface.name}}</h4>`;
                        iface.addresses.forEach(addr => {{
                            html += `<div style="margin-left: 15px; margin-bottom: 5px;">`;
                            html += `<strong>${{addr.family}}:</strong> ${{addr.address}}`;
                            if (addr.netmask) html += ` / ${{addr.netmask}}`;
                            if (addr.broadcast) html += ` (广播: ${{addr.broadcast}})`;
                            html += `</div>`;
                        }});
                        html += `</div>`;
                    }});
                    html += '</div>';
                    interfacesDiv.innerHTML = html;

                    // 更新接口选择下拉框
                    interfaceSelect.innerHTML = '<option value="">自动选择</option>';
                    data.interfaces.forEach(iface => {{
                        interfaceSelect.innerHTML += `<option value="${{iface.name}}">${{iface.name}}</option>`;
                    }});
                }} else {{
                    interfacesDiv.innerHTML = '<div class="result error">加载网络接口失败</div>';
                }}
            }} catch (error) {{
                interfacesDiv.innerHTML = `<div class="result error">加载网络接口失败: ${{error.message}}</div>`;
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
            whitelistDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在加载白名单...</p></div>';

            try {{
                const response = await fetch('/whitelist');
                if (response.ok) {{
                    const data = await response.json();

                    if (data.length === 0) {{
                        whitelistDiv.innerHTML = `
                            <div class="empty-whitelist">
                                <p>暂无白名单IP</p>
                                <small>添加IP地址到白名单后，这些IP可以无需登录直接调用API</small>
                            </div>
                        `;
                    }} else {{
                        let tableHtml = `
                            <table class="whitelist-table">
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
                                        <button class="remove-btn" onclick="removeIpFromWhitelist('${{ip}}')">
                                            移除
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
                    resultDiv.innerHTML = `<div class="result success"><strong>✅ 移除成功!</strong><br>已从白名单移除 ${{ip}}</div>`;
                    setTimeout(() => {{ resultDiv.innerHTML = ''; }}, 3000);
                }} else {{
                    alert(`移除失败: ${{data.message || '未知错误'}}`);
                }}
            }} catch (error) {{
                alert(`移除失败: ${{error.message}}`);
            }}
        }}

        async function checkCurrentIpStatus() {{
            const statusDiv = document.getElementById('currentIpStatus');
            statusDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在检查当前IP状态...</p></div>';

            try {{
                const response = await fetch('/whitelist/check');
                const data = await response.json();

                const statusClass = data.in_whitelist ? 'in-whitelist' : 'not-in-whitelist';
                const statusIcon = data.in_whitelist ? '✅' : '❌';

                statusDiv.innerHTML = `
                    <div>
                        <p><strong>当前IP:</strong> <code>${{data.client_ip}}</code></p>
                        <div class="ip-status ${{statusClass}}">
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
