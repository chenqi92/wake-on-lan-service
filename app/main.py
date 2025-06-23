from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import time
import os
from datetime import datetime, timedelta
from app.models import (
    WakeRequest, AdvancedWakeRequest, WakeResponse,
    InterfacesResponse, HealthResponse
)
from app.network_utils import get_network_interfaces
from app.wake_on_lan import wake_device_simple, wake_device_advanced

# 应用启动时间
start_time = time.time()

# 创建FastAPI应用
app = FastAPI(
    title="Wake-on-LAN Service",
    description="内网设备唤醒服务 - 支持通过MAC地址唤醒网络设备",
    version="1.0.1",
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

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse, summary="Web界面", description="Wake-on-LAN Web管理界面")
async def web_interface():
    """Web管理界面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake-on-LAN 管理界面</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

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

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
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

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }

        input, select, button {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            white-space: pre-wrap;
        }

        .result.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }

        .result.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }

        .interfaces-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 15px;
            background: white;
        }

        .interface-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
        }

        .interface-item:hover {
            background: #f8f9fa;
        }

        .interface-item:last-child {
            border-bottom: none;
        }

        .interface-name {
            font-weight: 600;
            color: #667eea;
        }

        .interface-details {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-online {
            background: #28a745;
        }

        .status-offline {
            background: #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Wake-on-LAN 管理界面</h1>
            <p>内网设备远程唤醒服务 v1.0.1</p>
        </div>

        <div class="content">
            <!-- 服务状态 -->
            <div class="section">
                <h2>📊 服务状态</h2>
                <div id="serviceStatus">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>正在检查服务状态...</p>
                    </div>
                </div>
                <button onclick="checkServiceStatus()">刷新状态</button>
            </div>

            <!-- 网络接口 -->
            <div class="section">
                <h2>🔌 网络接口</h2>
                <div id="interfacesList">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>正在加载网络接口...</p>
                    </div>
                </div>
                <button onclick="loadInterfaces()">刷新接口</button>
            </div>

            <!-- 设备唤醒 -->
            <div class="section">
                <h2>⚡ 设备唤醒</h2>
                <div class="grid">
                    <!-- 简单唤醒 -->
                    <div>
                        <h3>简单唤醒</h3>
                        <div class="form-group">
                            <label for="simpleMac">MAC地址:</label>
                            <input type="text" id="simpleMac" placeholder="例: AA:BB:CC:DD:EE:FF"
                                   pattern="^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$">
                        </div>
                        <button onclick="simpleWake()">唤醒设备</button>
                        <div id="simpleResult"></div>
                    </div>

                    <!-- 高级唤醒 -->
                    <div>
                        <h3>高级唤醒</h3>
                        <div class="form-group">
                            <label for="advancedMac">MAC地址:</label>
                            <input type="text" id="advancedMac" placeholder="例: AA:BB:CC:DD:EE:FF"
                                   pattern="^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$">
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
        </div>
    </div>

    <script>
        // API基础URL
        const API_BASE = '';

        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {
            checkServiceStatus();
            loadInterfaces();
        });

        // 检查服务状态
        async function checkServiceStatus() {
            const statusDiv = document.getElementById('serviceStatus');
            statusDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在检查服务状态...</p></div>';

            try {
                const response = await fetch(`${API_BASE}/health`);
                const data = await response.json();

                statusDiv.innerHTML = `
                    <div class="result success">
                        <span class="status-indicator status-online"></span>
                        <strong>服务运行正常</strong><br>
                        版本: ${data.version}<br>
                        运行时间: ${data.uptime}<br>
                        状态: ${data.status}
                    </div>
                `;
            } catch (error) {
                statusDiv.innerHTML = `
                    <div class="result error">
                        <span class="status-indicator status-offline"></span>
                        <strong>服务连接失败</strong><br>
                        错误: ${error.message}
                    </div>
                `;
            }
        }

        // 加载网络接口
        async function loadInterfaces() {
            const interfacesDiv = document.getElementById('interfacesList');
            const interfaceSelect = document.getElementById('interface');

            interfacesDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在加载网络接口...</p></div>';

            try {
                const response = await fetch(`${API_BASE}/interfaces`);
                const data = await response.json();

                // 更新接口列表显示
                let interfacesHtml = `<div class="interfaces-list">`;
                interfacesHtml += `<p><strong>找到 ${data.count} 个网络接口:</strong></p>`;

                data.interfaces.forEach(iface => {
                    interfacesHtml += `
                        <div class="interface-item" onclick="selectInterface('${iface.name}', '${iface.broadcast || ''}')">
                            <div class="interface-name">${iface.name}</div>
                            <div class="interface-details">
                                IP: ${iface.ip_address} |
                                子网掩码: ${iface.netmask} |
                                广播: ${iface.broadcast || 'N/A'} |
                                MAC: ${iface.mac_address || 'N/A'}
                            </div>
                        </div>
                    `;
                });
                interfacesHtml += `</div>`;
                interfacesDiv.innerHTML = interfacesHtml;

                // 更新接口选择下拉框
                interfaceSelect.innerHTML = '<option value="">自动选择</option>';
                data.interfaces.forEach(iface => {
                    interfaceSelect.innerHTML += `<option value="${iface.name}">${iface.name} (${iface.ip_address})</option>`;
                });

            } catch (error) {
                interfacesDiv.innerHTML = `
                    <div class="result error">
                        <strong>加载网络接口失败</strong><br>
                        错误: ${error.message}
                    </div>
                `;
            }
        }

        // 选择网络接口
        function selectInterface(name, broadcast) {
            document.getElementById('interface').value = name;
            if (broadcast) {
                document.getElementById('broadcast').value = broadcast;
            }
        }

        // 简单唤醒
        async function simpleWake() {
            const macAddress = document.getElementById('simpleMac').value.trim();
            const resultDiv = document.getElementById('simpleResult');

            if (!macAddress) {
                resultDiv.innerHTML = '<div class="result error">请输入MAC地址</div>';
                return;
            }

            if (!isValidMac(macAddress)) {
                resultDiv.innerHTML = '<div class="result error">MAC地址格式无效，请使用 AA:BB:CC:DD:EE:FF 格式</div>';
                return;
            }

            resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在唤醒设备...</p></div>';

            try {
                const response = await fetch(`${API_BASE}/wake`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        mac_address: macAddress
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <strong>✅ 唤醒成功!</strong><br>
                            消息: ${data.message}<br>
                            使用接口: ${data.interface_used}<br>
                            广播地址: ${data.broadcast_address}<br>
                            目标MAC: ${data.mac_address}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <strong>❌ 唤醒失败</strong><br>
                            错误: ${data.detail}
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="result error">
                        <strong>❌ 请求失败</strong><br>
                        错误: ${error.message}
                    </div>
                `;
            }
        }

        // 高级唤醒
        async function advancedWake() {
            const macAddress = document.getElementById('advancedMac').value.trim();
            const interface = document.getElementById('interface').value;
            const broadcast = document.getElementById('broadcast').value.trim();
            const port = parseInt(document.getElementById('port').value);
            const resultDiv = document.getElementById('advancedResult');

            if (!macAddress) {
                resultDiv.innerHTML = '<div class="result error">请输入MAC地址</div>';
                return;
            }

            if (!isValidMac(macAddress)) {
                resultDiv.innerHTML = '<div class="result error">MAC地址格式无效，请使用 AA:BB:CC:DD:EE:FF 格式</div>';
                return;
            }

            resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在执行高级唤醒...</p></div>';

            const requestBody = {
                mac_address: macAddress,
                port: port
            };

            if (interface) requestBody.interface = interface;
            if (broadcast) requestBody.broadcast_address = broadcast;

            try {
                const response = await fetch(`${API_BASE}/wake/advanced`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();

                if (response.ok) {
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <strong>✅ 高级唤醒成功!</strong><br>
                            消息: ${data.message}<br>
                            使用接口: ${data.interface_used}<br>
                            广播地址: ${data.broadcast_address}<br>
                            目标MAC: ${data.mac_address}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <strong>❌ 高级唤醒失败</strong><br>
                            错误: ${data.detail}
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="result error">
                        <strong>❌ 请求失败</strong><br>
                        错误: ${error.message}
                    </div>
                `;
            }
        }

        // 验证MAC地址格式
        function isValidMac(mac) {
            const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
            return macRegex.test(mac);
        }
    </script>
</body>
</html>
    """


@app.get("/api", summary="API信息", description="服务API信息，返回基本信息")
async def api_info():
    """根路径接口"""
    return {
        "service": "Wake-on-LAN Service",
        "version": "1.0.1",
        "description": "内网设备唤醒服务",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, summary="健康检查", description="检查服务运行状态")
async def health_check():
    """健康检查接口"""
    uptime_seconds = time.time() - start_time
    uptime_str = str(timedelta(seconds=int(uptime_seconds)))
    
    return HealthResponse(
        status="healthy",
        version="1.0.1",
        uptime=uptime_str
    )


@app.get("/interfaces", response_model=InterfacesResponse, summary="查询网络接口", description="获取所有可用的网络接口信息")
async def get_interfaces():
    """获取所有网络接口信息"""
    try:
        interfaces = get_network_interfaces()
        return InterfacesResponse(
            interfaces=interfaces,
            count=len(interfaces)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取网络接口失败: {str(e)}")


@app.post("/wake", response_model=WakeResponse, summary="简单唤醒", description="使用默认设置唤醒设备，只需提供MAC地址")
async def wake_device(request: WakeRequest):
    """简单设备唤醒接口"""
    try:
        success, message, interface_used, broadcast_used = wake_device_simple(request.mac_address)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return WakeResponse(
            success=success,
            message=message,
            mac_address=request.mac_address,
            interface_used=interface_used,
            broadcast_address=broadcast_used
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"唤醒设备失败: {str(e)}")


@app.post("/wake/advanced", response_model=WakeResponse, summary="高级唤醒", description="高级唤醒功能，支持指定网络接口、广播地址等参数")
async def wake_device_advanced_endpoint(request: AdvancedWakeRequest):
    """高级设备唤醒接口"""
    try:
        success, message, interface_used, broadcast_used = wake_device_advanced(
            mac_address=request.mac_address,
            interface_name=request.interface,
            broadcast_address=request.broadcast_address,
            port=request.port
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return WakeResponse(
            success=success,
            message=message,
            mac_address=request.mac_address,
            interface_used=interface_used,
            broadcast_address=broadcast_used
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"唤醒设备失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "12345"))
    
    print(f"启动Wake-on-LAN服务...")
    print(f"服务地址: http://{host}:{port}")
    print(f"API文档: http://{host}:{port}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        access_log=True
    )
