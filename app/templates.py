"""
HTML模板模块 - 包含登录界面和主界面的HTML模板
"""


def get_login_template(app_version: str) -> str:
    """获取登录界面HTML模板"""
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake-on-LAN 登录</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .login-container {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            width: 100%;
            max-width: 400px;
        }}

        .login-header {{
            text-align: center;
            margin-bottom: 30px;
        }}

        .login-header h1 {{
            color: #333;
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .login-header p {{
            color: #666;
            font-size: 0.9em;
        }}

        .form-group {{
            margin-bottom: 20px;
        }}

        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }}

        input[type="text"], input[type="password"] {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: all 0.3s ease;
        }}

        input[type="text"]:focus, input[type="password"]:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        .captcha-group {{
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }}

        .captcha-input {{
            flex: 1;
        }}

        .captcha-image {{
            width: 120px;
            height: 40px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8f9fa;
        }}

        .captcha-image img {{
            max-width: 100%;
            max-height: 100%;
            border-radius: 6px;
        }}

        .refresh-captcha {{
            background: #f8f9fa;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            padding: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .refresh-captcha:hover {{
            background: #e9ecef;
            border-color: #667eea;
        }}

        .login-button {{
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
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .login-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }}

        .login-button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}

        .alert {{
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }}

        .alert-error {{
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }}

        .alert-success {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}

        .loading {{
            display: none;
            text-align: center;
            padding: 20px;
        }}

        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e1e5e9;
            color: #666;
            font-size: 0.8em;
        }}

        .env-info {{
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9em;
            color: #1565c0;
        }}

        .env-info strong {{
            display: block;
            margin-bottom: 5px;
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🌐 Wake-on-LAN</h1>
            <p>内网设备远程唤醒服务 v{app_version}</p>
        </div>

        <div class="env-info">
            <strong>环境变量配置说明：</strong>
            WOL_USERNAME: 登录用户名<br>
            WOL_PASSWORD: 登录密码<br>
            WOL_SESSION_SECRET: 会话密钥
        </div>

        <div id="alertContainer"></div>

        <form id="loginForm">
            <div class="form-group">
                <label for="username">用户名:</label>
                <input type="text" id="username" name="username" required>
            </div>

            <div class="form-group">
                <label for="password">密码:</label>
                <input type="password" id="password" name="password" required>
            </div>

            <div class="form-group">
                <label for="captcha">验证码:</label>
                <div class="captcha-group">
                    <div class="captcha-input">
                        <input type="text" id="captcha" name="captcha" required maxlength="4" placeholder="请输入验证码">
                    </div>
                    <div class="captcha-image" id="captchaImage" onclick="refreshCaptcha()">
                        <span>点击加载</span>
                    </div>
                    <button type="button" class="refresh-captcha" onclick="refreshCaptcha()" title="刷新验证码">
                        🔄
                    </button>
                </div>
            </div>

            <button type="submit" class="login-button" id="loginButton">登录</button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>正在登录...</p>
        </div>

        <div class="footer">
            <p>请使用环境变量配置的账号密码登录</p>
        </div>
    </div>

    <script>
        let currentCaptchaId = null;

        // 页面加载时获取验证码
        document.addEventListener('DOMContentLoaded', function() {{
            refreshCaptcha();
        }});

        // 刷新验证码
        async function refreshCaptcha() {{
            try {{
                const response = await fetch('/api/captcha');
                const data = await response.json();
                
                currentCaptchaId = data.captcha_id;
                document.getElementById('captchaImage').innerHTML = 
                    `<img src="${{data.captcha_image}}" alt="验证码">`;
                document.getElementById('captcha').value = '';
            }} catch (error) {{
                showAlert('获取验证码失败: ' + error.message, 'error');
            }}
        }}

        // 显示提示信息
        function showAlert(message, type = 'error') {{
            const alertContainer = document.getElementById('alertContainer');
            alertContainer.innerHTML = `
                <div class="alert alert-${{type}}">
                    ${{message}}
                </div>
            `;
            
            // 3秒后自动隐藏
            setTimeout(() => {{
                alertContainer.innerHTML = '';
            }}, 3000);
        }}

        // 处理登录表单提交
        document.getElementById('loginForm').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            if (!currentCaptchaId) {{
                showAlert('请先获取验证码', 'error');
                return;
            }
            
            const formData = new FormData(this);
            const loginData = {{
                username: formData.get('username'),
                password: formData.get('password'),
                captcha_id: currentCaptchaId,
                captcha_text: formData.get('captcha')
            }};
            
            // 显示加载状态
            document.getElementById('loading').style.display = 'block';
            document.getElementById('loginButton').disabled = true;
            
            try {{
                const response = await fetch('/api/login', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(loginData)
                }});
                
                const result = await response.json();
                
                if (response.ok && result.success) {{
                    showAlert('登录成功，正在跳转...', 'success');
                    
                    // 设置cookie并跳转
                    document.cookie = `access_token=${{result.access_token}}; path=/; max-age=86400; SameSite=Strict`;
                    
                    setTimeout(() => {{
                        window.location.href = '/';
                    }}, 1000);
                }} else {{
                    showAlert(result.message || '登录失败', 'error');
                    refreshCaptcha(); // 刷新验证码
                }}
            }} catch (error) {{
                showAlert('登录请求失败: ' + error.message, 'error');
                refreshCaptcha(); // 刷新验证码
            }} finally {{
                // 隐藏加载状态
                document.getElementById('loading').style.display = 'none';
                document.getElementById('loginButton').disabled = false;
            }}
        }});

        // 回车键提交表单
        document.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                document.getElementById('loginForm').dispatchEvent(new Event('submit'));
            }}
        }});
    </script>
</body>
</html>
    """


def get_main_template(app_version: str) -> str:
    """获取主界面HTML模板"""
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wake-on-LAN 管理界面</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header-left h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header-left p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .header-right {{
            text-align: right;
        }}

        .user-info {{
            margin-bottom: 15px;
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .logout-btn {{
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }}

        .logout-btn:hover {{
            background: rgba(255,255,255,0.3);
            border-color: rgba(255,255,255,0.5);
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }}

        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}

        .form-group {{
            margin-bottom: 20px;
        }}

        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }}

        input, select, button {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: all 0.3s ease;
        }}

        input:focus, select:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }}

        button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}

        .result {{
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            white-space: pre-wrap;
        }}

        .result.success {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}

        .result.error {{
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }}

        .interfaces-list {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 15px;
            background: white;
        }}

        .interface-item {{
            padding: 10px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
        }}

        .interface-item:hover {{
            background: #f8f9fa;
        }}

        .interface-item:last-child {{
            border-bottom: none;
        }}

        .interface-name {{
            font-weight: 600;
            color: #667eea;
        }}

        .interface-details {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}

        .loading {{
            display: none;
            text-align: center;
            padding: 20px;
        }}

        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .status-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }}

        .status-online {{
            background: #28a745;
        }}

        .status-offline {{
            background: #dc3545;
        }}

        /* 白名单管理样式 */
        .whitelist-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .whitelist-table th,
        .whitelist-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}

        .whitelist-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}

        .whitelist-table tr:hover {{
            background: #f8f9fa;
        }}

        .remove-btn {{
            background: #dc3545;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
        }}

        .remove-btn:hover {{
            background: #c82333;
            transform: translateY(-1px);
        }}

        .ip-status {{
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: 600;
            display: inline-block;
            margin-top: 10px;
        }}

        .ip-status.in-whitelist {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}

        .ip-status.not-in-whitelist {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}

        .empty-whitelist {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }}

        .auth-type-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 600;
            margin-left: 8px;
        }}

        .auth-type-token {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .auth-type-whitelist {{
            background: #d4edda;
            color: #155724;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>🌐 Wake-on-LAN 管理界面</h1>
                <p>内网设备远程唤醒服务 v{app_version}</p>
            </div>
            <div class="header-right">
                <div class="user-info" id="userInfo">
                    正在加载用户信息...
                </div>
                <button class="logout-btn" onclick="logout()">退出登录</button>
            </div>
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

            <!-- IP白名单管理 -->
            <div class="section" id="whitelistSection">
                <h2>🛡️ IP白名单管理</h2>
                <p style="margin-bottom: 20px; color: #666;">白名单中的IP地址可以无需登录直接调用API接口</p>

                <!-- 添加IP -->
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

                <!-- 白名单列表 -->
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
                    <!-- 简单唤醒 -->
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

                    <!-- 高级唤醒 -->
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
        </div>
    </div>

    <script>
        // API基础URL
        const API_BASE = '';

        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {{
            loadUserInfo();
            checkServiceStatus();
            loadInterfaces();
            loadWhitelist();
            checkCurrentIpStatus();
        }});

        // 获取认证头
        function getAuthHeaders() {{
            const token = getCookie('access_token');
            return token ? {{ 'Authorization': `Bearer ${{token}}` }} : {{}};
        }}

        // 获取Cookie
        function getCookie(name) {{
            const value = `; ${{document.cookie}}`;
            const parts = value.split(`; ${{name}}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
        }}

        // 加载用户信息
        async function loadUserInfo() {{
            try {{
                const response = await fetch(`${{API_BASE}}/api/user`, {{
                    headers: getAuthHeaders()
                }});

                if (response.ok) {{
                    const user = await response.json();
                    let authBadge = '';
                    if (user.auth_type === 'whitelist') {{
                        authBadge = '<span class="auth-type-badge auth-type-whitelist">白名单用户</span>';
                        // 隐藏白名单管理功能
                        const whitelistSection = document.getElementById('whitelistSection');
                        if (whitelistSection) {{
                            whitelistSection.style.display = 'none';
                        }}
                    }} else if (user.auth_type === 'token') {{
                        authBadge = '<span class="auth-type-badge auth-type-token">登录用户</span>';
                    }}

                    document.getElementById('userInfo').innerHTML = `
                        欢迎, ${{user.username}} ${{authBadge}}
                        ${{user.ip ? `<br><small>IP: ${{user.ip}}</small>` : ''}}
                    `;
                }} else {{
                    // 认证失败，跳转到登录页
                    logout();
                }}
            }} catch (error) {{
                console.error('获取用户信息失败:', error);
                logout();
            }}
        }}

        // 退出登录
        function logout() {{
            // 清除cookie
            document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
            // 跳转到登录页
            window.location.href = '/';
        }}

        // 检查服务状态
        async function checkServiceStatus() {{
            const statusDiv = document.getElementById('serviceStatus');
            statusDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在检查服务状态...</p></div>';

            try {{
                const response = await fetch(`${{API_BASE}}/health`, {{
                    headers: getAuthHeaders()
                }});
                const data = await response.json();

                statusDiv.innerHTML = `
                    <div class="result success">
                        <span class="status-indicator status-online"></span>
                        <strong>服务运行正常</strong><br>
                        版本: ${{data.version}}<br>
                        运行时间: ${{data.uptime}}<br>
                        状态: ${{data.status}}
                    </div>
                `;
            }} catch (error) {{
                statusDiv.innerHTML = `
                    <div class="result error">
                        <span class="status-indicator status-offline"></span>
                        <strong>服务连接失败</strong><br>
                        错误: ${{error.message}}
                    </div>
                `;
            }}
        }}

        // 加载网络接口
        async function loadInterfaces() {{
            const interfacesDiv = document.getElementById('interfacesList');
            const interfaceSelect = document.getElementById('interface');

            interfacesDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在加载网络接口...</p></div>';

            try {{
                const response = await fetch(`${{API_BASE}}/interfaces`, {{
                    headers: getAuthHeaders()
                }});
                const data = await response.json();

                // 更新接口列表显示
                let interfacesHtml = `<div class="interfaces-list">`;
                interfacesHtml += `<p><strong>找到 ${{data.count}} 个网络接口:</strong></p>`;

                data.interfaces.forEach(iface => {{
                    interfacesHtml += `
                        <div class="interface-item" onclick="selectInterface('${{iface.name}}', '${{iface.broadcast || ''}}')">
                            <div class="interface-name">${{iface.name}}</div>
                            <div class="interface-details">
                                IP: ${{iface.ip_address}} |
                                子网掩码: ${{iface.netmask}} |
                                广播: ${{iface.broadcast || 'N/A'}} |
                                MAC: ${{iface.mac_address || 'N/A'}}
                            </div>
                        </div>
                    `;
                }});
                interfacesHtml += `</div>`;
                interfacesDiv.innerHTML = interfacesHtml;

                // 更新接口选择下拉框
                interfaceSelect.innerHTML = '<option value="">自动选择</option>';
                data.interfaces.forEach(iface => {{
                    interfaceSelect.innerHTML += `<option value="${{iface.name}}">${{iface.name}} (${{iface.ip_address}})</option>`;
                }});

            }} catch (error) {{
                interfacesDiv.innerHTML = `
                    <div class="result error">
                        <strong>加载网络接口失败</strong><br>
                        错误: ${{error.message}}
                    </div>
                `;
            }}
        }}

        // 选择网络接口
        function selectInterface(name, broadcast) {{
            document.getElementById('interface').value = name;
            if (broadcast) {{
                document.getElementById('broadcast').value = broadcast;
            }}
        }}

        // 简单唤醒
        async function simpleWake() {{
            const macAddress = document.getElementById('simpleMac').value.trim();
            const resultDiv = document.getElementById('simpleResult');

            if (!macAddress) {{
                resultDiv.innerHTML = '<div class="result error">请输入MAC地址</div>';
                return;
            }}

            if (!isValidMac(macAddress)) {{
                resultDiv.innerHTML = '<div class="result error">MAC地址格式无效，请使用 AA:BB:CC:DD:EE:FF 格式</div>';
                return;
            }}

            resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在唤醒设备...</p></div>';

            try {{
                const response = await fetch(`${{API_BASE}}/wake`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        ...getAuthHeaders()
                    }},
                    body: JSON.stringify({{
                        mac_address: macAddress
                    }})
                }});

                const data = await response.json();

                if (response.ok) {{
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <strong>✅ 唤醒成功!</strong><br>
                            消息: ${{data.message}}<br>
                            使用接口: ${{data.interface_used}}<br>
                            广播地址: ${{data.broadcast_address}}<br>
                            目标MAC: ${{data.mac_address}}
                        </div>
                    `;
                }} else {{
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <strong>❌ 唤醒失败</strong><br>
                            错误: ${{data.detail}}
                        </div>
                    `;
                }}
            }} catch (error) {{
                resultDiv.innerHTML = `
                    <div class="result error">
                        <strong>❌ 请求失败</strong><br>
                        错误: ${{error.message}}
                    </div>
                `;
            }}
        }}

        // 高级唤醒
        async function advancedWake() {{
            const macAddress = document.getElementById('advancedMac').value.trim();
            const interface = document.getElementById('interface').value;
            const broadcast = document.getElementById('broadcast').value.trim();
            const port = parseInt(document.getElementById('port').value);
            const resultDiv = document.getElementById('advancedResult');

            if (!macAddress) {{
                resultDiv.innerHTML = '<div class="result error">请输入MAC地址</div>';
                return;
            }}

            if (!isValidMac(macAddress)) {{
                resultDiv.innerHTML = '<div class="result error">MAC地址格式无效，请使用 AA:BB:CC:DD:EE:FF 格式</div>';
                return;
            }}

            resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在执行高级唤醒...</p></div>';

            const requestBody = {{
                mac_address: macAddress,
                port: port
            }};

            if (interface) requestBody.interface = interface;
            if (broadcast) requestBody.broadcast_address = broadcast;

            try {{
                const response = await fetch(`${{API_BASE}}/wake/advanced`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        ...getAuthHeaders()
                    }},
                    body: JSON.stringify(requestBody)
                }});

                const data = await response.json();

                if (response.ok) {{
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <strong>✅ 高级唤醒成功!</strong><br>
                            消息: ${{data.message}}<br>
                            使用接口: ${{data.interface_used}}<br>
                            广播地址: ${{data.broadcast_address}}<br>
                            目标MAC: ${{data.mac_address}}
                        </div>
                    `;
                }} else {{
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <strong>❌ 高级唤醒失败</strong><br>
                            错误: ${{data.detail}}
                        </div>
                    `;
                }}
            }} catch (error) {{
                resultDiv.innerHTML = `
                    <div class="result error">
                        <strong>❌ 请求失败</strong><br>
                        错误: ${{error.message}}
                    </div>
                `;
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
                const response = await fetch(`${{API_BASE}}/api/whitelist`, {{
                    headers: getAuthHeaders()
                }});

                if (response.ok) {{
                    const data = await response.json();

                    if (data.count === 0) {{
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
                                        <th>描述</th>
                                        <th>添加时间</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;

                        data.whitelist.forEach(item => {{
                            tableHtml += `
                                <tr>
                                    <td><code>${{item.ip}}</code></td>
                                    <td>${{item.description || '无描述'}}</td>
                                    <td>${{new Date(item.added_at).toLocaleString()}}</td>
                                    <td>
                                        <button class="remove-btn" onclick="removeIpFromWhitelist('${{item.ip}}')">
                                            移除
                                        </button>
                                    </td>
                                </tr>
                            `;
                        }});

                        tableHtml += '</tbody></table>';
                        whitelistDiv.innerHTML = tableHtml;
                    }}
                }} else if (response.status === 403) {{
                    whitelistDiv.innerHTML = `
                        <div class="result error">
                            <strong>权限不足</strong><br>
                            白名单用户无法管理白名单，请使用管理员账号登录
                        </div>
                    `;
                }} else {{
                    whitelistDiv.innerHTML = `
                        <div class="result error">
                            <strong>加载白名单失败</strong><br>
                            HTTP ${{response.status}}
                        </div>
                    `;
                }}
            }} catch (error) {{
                whitelistDiv.innerHTML = `
                    <div class="result error">
                        <strong>加载白名单失败</strong><br>
                        错误: ${{error.message}}
                    </div>
                `;
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
                const response = await fetch(`${{API_BASE}}/api/whitelist/add`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        ...getAuthHeaders()
                    }},
                    body: JSON.stringify({{
                        ip: ip,
                        description: description
                    }})
                }});

                const data = await response.json();

                if (response.ok && data.success) {{
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <strong>✅ 添加成功!</strong><br>
                            ${{data.message}}
                        </div>
                    `;

                    // 清空输入框
                    document.getElementById('newIp').value = '';
                    document.getElementById('ipDescription').value = '';

                    // 刷新白名单
                    loadWhitelist();
                    checkCurrentIpStatus();
                }} else {{
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <strong>❌ 添加失败</strong><br>
                            ${{data.message || '未知错误'}}
                        </div>
                    `;
                }}
            }} catch (error) {{
                resultDiv.innerHTML = `
                    <div class="result error">
                        <strong>❌ 请求失败</strong><br>
                        错误: ${{error.message}}
                    </div>
                `;
            }}
        }}

        async function removeIpFromWhitelist(ip) {{
            if (!confirm(`确定要从白名单中移除 ${{ip}} 吗？`)) {{
                return;
            }}

            try {{
                const response = await fetch(`${{API_BASE}}/api/whitelist/remove`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        ...getAuthHeaders()
                    }},
                    body: JSON.stringify({{
                        ip: ip
                    }})
                }});

                const data = await response.json();

                if (response.ok && data.success) {{
                    // 刷新白名单
                    loadWhitelist();
                    checkCurrentIpStatus();

                    // 显示成功消息
                    const resultDiv = document.getElementById('addIpResult');
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <strong>✅ 移除成功!</strong><br>
                            已从白名单移除 ${{ip}}
                        </div>
                    `;

                    // 3秒后清除消息
                    setTimeout(() => {{
                        resultDiv.innerHTML = '';
                    }}, 3000);
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
                const response = await fetch(`${{API_BASE}}/api/whitelist/check`);
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
                statusDiv.innerHTML = `
                    <div class="result error">
                        <strong>检查失败</strong><br>
                        错误: ${{error.message}}
                    </div>
                `;
            }}
        }}
    </script>
</body>
</html>
    """
