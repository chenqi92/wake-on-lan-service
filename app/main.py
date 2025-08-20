from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from app.models import (
    WakeRequest, AdvancedWakeRequest, WakeResponse,
    InterfacesResponse, HealthResponse,
    LoginRequest, LoginResponse, CaptchaResponse, UserInfo,
    IPWhitelistResponse, IPWhitelistItem, AddIPRequest,
    RemoveIPRequest, IPWhitelistOperationResponse
)
from app.network_utils import get_network_interfaces
from app.wake_on_lan import wake_device_simple, wake_device_advanced
from app.auth import (
    auth_config, create_access_token, get_current_user, get_current_user_optional,
    generate_captcha, verify_captcha, cleanup_expired_captchas,
    cleanup_expired_sessions, get_client_ip, is_ip_in_whitelist,
    add_ip_to_whitelist, remove_ip_from_whitelist, get_ip_whitelist,
    validate_ip_format
)

# 应用启动时间
start_time = time.time()

# 暂时移除lifespan功能以避免启动问题
# 定期清理任务
# import asyncio
# from contextlib import asynccontextmanager

# @asynccontextmanager
# async def lifespan(app):
#     # 启动时的清理任务
#     cleanup_task = asyncio.create_task(periodic_cleanup())
#     yield
#     # 关闭时取消任务
#     cleanup_task.cancel()
#     try:
#         await cleanup_task
#     except asyncio.CancelledError:
#         pass

# async def periodic_cleanup():
#     """定期清理过期的验证码和会话"""
#     while True:
#         try:
#             cleanup_expired_captchas()
#             cleanup_expired_sessions()
#             await asyncio.sleep(300)  # 每5分钟清理一次
#         except asyncio.CancelledError:
#             break
#         except Exception as e:
#             print(f"清理任务出错: {e}")
#             await asyncio.sleep(60)  # 出错后等待1分钟再试

# 读取版本号
def get_version():
    try:
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "1.0.1"  # 默认版本
    except:
        return "1.0.1"  # 默认版本

APP_VERSION = get_version()

# 创建FastAPI应用
app = FastAPI(
    title="Wake-on-LAN Service",
    description="内网设备唤醒服务 - 支持通过MAC地址唤醒网络设备",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    # 暂时禁用lifespan以便调试
    # lifespan=lifespan
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
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception as e:
    print(f"警告: 静态文件目录挂载失败: {e}")
    # 创建静态文件目录
    import os
    os.makedirs("app/static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse, summary="Web界面", description="Wake-on-LAN Web管理界面")
async def web_interface(request: Request):
    """Web管理界面 - 检查认证状态"""
    try:
        # 检查是否已登录
        token = request.cookies.get("access_token")
        if token:
            try:
                from app.auth import verify_token
                user_data = verify_token(token)
                if user_data:
                    # 已登录，显示主界面
                    return await main_interface()
            except Exception as e:
                print(f"Token验证失败: {e}")

        # 未登录，显示登录界面
        return await login_interface()
    except Exception as e:
        # 如果出现任何错误，返回简单的错误页面
        return f"""
        <html>
        <head><title>Wake-on-LAN Service</title></head>
        <body>
            <h1>Wake-on-LAN Service</h1>
            <p>服务正在运行，但遇到了一些问题。</p>
            <p>错误: {str(e)}</p>
            <p><a href="/health">健康检查</a> | <a href="/docs">API文档</a></p>
        </body>
        </html>
        """


async def login_interface():
    """登录界面"""
    try:
        from app.templates import get_login_template
        return get_login_template(APP_VERSION)
    except Exception as e:
        # 简单的登录页面
        return f"""
        <html>
        <head><title>Wake-on-LAN 登录</title></head>
        <body>
            <h1>Wake-on-LAN 登录</h1>
            <p>模板加载失败: {str(e)}</p>
            <form method="post" action="/api/login">
                <p>用户名: <input type="text" name="username" value="admin"></p>
                <p>密码: <input type="password" name="password"></p>
                <p><button type="submit">登录</button></p>
            </form>
        </body>
        </html>
        """


async def main_interface():
    """主界面"""
    try:
        from app.templates import get_main_template
        return get_main_template(APP_VERSION)
    except Exception as e:
        # 简单的主界面
        return f"""
        <html>
        <head><title>Wake-on-LAN 管理</title></head>
        <body>
            <h1>Wake-on-LAN 管理界面</h1>
            <p>模板加载失败: {str(e)}</p>
            <p>服务正在运行中...</p>
            <p><a href="/health">健康检查</a> | <a href="/docs">API文档</a> | <a href="/interfaces">网络接口</a></p>
        </body>
        </html>
        """


# 认证相关API端点
@app.get("/api/captcha", response_model=CaptchaResponse, summary="获取验证码", description="生成新的验证码")
async def get_captcha():
    """获取验证码"""
    try:
        captcha_data = generate_captcha()
        return CaptchaResponse(**captcha_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成验证码失败: {str(e)}")


@app.post("/api/login", response_model=LoginResponse, summary="用户登录", description="使用账号密码和验证码登录")
async def login(request: LoginRequest):
    """用户登录"""
    try:
        # 验证验证码
        if not verify_captcha(request.captcha_id, request.captcha_text):
            return LoginResponse(
                success=False,
                message="验证码错误或已过期"
            )

        # 验证用户凭据
        if not auth_config.verify_credentials(request.username, request.password):
            return LoginResponse(
                success=False,
                message="用户名或密码错误"
            )

        # 创建访问令牌
        access_token = create_access_token(data={"sub": request.username})

        return LoginResponse(
            success=True,
            message="登录成功",
            access_token=access_token,
            token_type="bearer"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@app.get("/api/user", response_model=UserInfo, summary="获取用户信息", description="获取当前登录用户信息")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """获取用户信息"""
    return UserInfo(
        username=current_user["username"],
        is_authenticated=True,
        auth_type=current_user.get("auth_type"),
        ip=current_user.get("ip")
    )


@app.post("/api/logout", summary="用户登出", description="退出登录")
async def logout():
    """用户登出"""
    # 清理过期的会话和验证码
    cleanup_expired_sessions()
    cleanup_expired_captchas()

    return {"success": True, "message": "已退出登录"}


# IP白名单管理API
@app.get("/api/whitelist", response_model=IPWhitelistResponse, summary="获取IP白名单", description="获取当前IP白名单列表")
async def get_whitelist(current_user: dict = Depends(get_current_user)):
    """获取IP白名单列表"""
    # 只有通过token认证的用户才能管理白名单
    if current_user.get("auth_type") == "whitelist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="白名单用户无法管理白名单"
        )

    try:
        whitelist = get_ip_whitelist()
        items = []
        for ip in whitelist:
            items.append(IPWhitelistItem(
                ip=ip,
                description=f"IP地址: {ip}",
                added_at=datetime.utcnow().isoformat()
            ))

        return IPWhitelistResponse(
            whitelist=items,
            count=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取白名单失败: {str(e)}")


@app.post("/api/whitelist/add", response_model=IPWhitelistOperationResponse, summary="添加IP到白名单", description="添加IP地址或CIDR网段到白名单")
async def add_ip_whitelist(request: AddIPRequest, current_user: dict = Depends(get_current_user)):
    """添加IP到白名单"""
    # 只有通过token认证的用户才能管理白名单
    if current_user.get("auth_type") == "whitelist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="白名单用户无法管理白名单"
        )

    try:
        if add_ip_to_whitelist(request.ip):
            return IPWhitelistOperationResponse(
                success=True,
                message=f"成功添加IP {request.ip} 到白名单",
                ip=request.ip,
                whitelist=get_ip_whitelist()
            )
        else:
            return IPWhitelistOperationResponse(
                success=False,
                message=f"添加IP {request.ip} 失败，可能是无效的IP格式",
                ip=request.ip
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加IP到白名单失败: {str(e)}")


@app.post("/api/whitelist/remove", response_model=IPWhitelistOperationResponse, summary="从白名单移除IP", description="从白名单中移除指定的IP地址或CIDR网段")
async def remove_ip_whitelist(request: RemoveIPRequest, current_user: dict = Depends(get_current_user)):
    """从白名单移除IP"""
    # 只有通过token认证的用户才能管理白名单
    if current_user.get("auth_type") == "whitelist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="白名单用户无法管理白名单"
        )

    try:
        if remove_ip_from_whitelist(request.ip):
            return IPWhitelistOperationResponse(
                success=True,
                message=f"成功从白名单移除IP {request.ip}",
                ip=request.ip,
                whitelist=get_ip_whitelist()
            )
        else:
            return IPWhitelistOperationResponse(
                success=False,
                message=f"移除IP {request.ip} 失败，IP不在白名单中",
                ip=request.ip
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"从白名单移除IP失败: {str(e)}")


@app.get("/api/whitelist/check", summary="检查IP白名单状态", description="检查当前客户端IP是否在白名单中")
async def check_ip_whitelist(request: Request):
    """检查IP白名单状态"""
    client_ip = get_client_ip(request)
    in_whitelist = is_ip_in_whitelist(client_ip)

    return {
        "client_ip": client_ip,
        "in_whitelist": in_whitelist,
        "message": "IP在白名单中，可免认证访问" if in_whitelist else "IP不在白名单中，需要登录认证"
    }




@app.get("/api", summary="API信息", description="服务API信息，返回基本信息")
async def api_info():
    """根路径接口"""
    return {
        "service": "Wake-on-LAN Service",
        "version": APP_VERSION,
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
        version=APP_VERSION,
        uptime=uptime_str
    )


@app.get("/interfaces", response_model=InterfacesResponse, summary="查询网络接口", description="获取所有可用的网络接口信息")
async def get_interfaces(current_user: dict = Depends(get_current_user)):
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
async def wake_device(request: WakeRequest, current_user: dict = Depends(get_current_user)):
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
async def wake_device_advanced_endpoint(request: AdvancedWakeRequest, current_user: dict = Depends(get_current_user)):
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
