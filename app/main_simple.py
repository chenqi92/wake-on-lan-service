#!/usr/bin/env python3
"""
Wake-on-LAN Service - 简化版本
避免复杂的模块导入问题，直接使用现代化的standalone应用
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    """主函数 - 使用现代化的standalone应用"""
    print("🔄 启动Wake-on-LAN服务...")
    
    # 检查standalone_app_v2.py是否存在
    standalone_path = Path(__file__).parent.parent / "standalone_app_v2.py"
    
    if standalone_path.exists():
        print("✅ 发现现代化应用，使用standalone_app_v2")
        
        # 设置环境变量
        os.environ.setdefault('WOL_USERNAME', os.getenv('WOL_USERNAME', 'admin'))
        os.environ.setdefault('WOL_PASSWORD', os.getenv('WOL_PASSWORD', 'admin123'))
        os.environ.setdefault('WOL_SESSION_SECRET', os.getenv('WOL_SESSION_SECRET', 'wake-on-lan-secret'))
        
        # 导入并运行standalone应用
        sys.path.insert(0, str(standalone_path.parent))
        
        try:
            from standalone_app_v2 import app
            print("✅ 现代化应用加载成功")
            return app
        except Exception as e:
            print(f"❌ 现代化应用加载失败: {e}")
            print("🔄 尝试使用基础版本...")
    
    # 如果现代化版本不可用，尝试使用基础版本
    try:
        from .wake_on_lan import send_magic_packet
        from .network_utils import get_network_interfaces
        from .auth import get_current_user, create_access_token
        
        # 创建基础FastAPI应用
        from fastapi import FastAPI, HTTPException, Depends, Request
        from fastapi.responses import HTMLResponse
        
        app = FastAPI(
            title="Wake-on-LAN Service",
            description="内网设备远程唤醒服务",
            version="1.0.0"
        )
        
        @app.get("/")
        async def root():
            return {"message": "Wake-on-LAN Service is running"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "version": "1.0.0"}
        
        @app.post("/wake")
        async def wake_device(wake_data: dict):
            mac_address = wake_data.get("mac_address")
            if not mac_address:
                raise HTTPException(status_code=400, detail="缺少MAC地址")
            
            try:
                send_magic_packet(mac_address)
                return {"success": True, "message": f"成功向 {mac_address} 发送唤醒包"}
            except Exception as e:
                return {"success": False, "message": str(e)}
        
        @app.get("/interfaces")
        async def get_interfaces():
            try:
                interfaces = get_network_interfaces()
                return {"interfaces": interfaces, "count": len(interfaces)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        print("✅ 基础应用创建成功")
        return app
        
    except Exception as e:
        print(f"❌ 基础应用创建失败: {e}")
        
        # 最后的备用方案：创建最简单的应用
        from fastapi import FastAPI
        
        app = FastAPI(title="Wake-on-LAN Service", version="1.0.0-minimal")
        
        @app.get("/")
        async def root():
            return {
                "message": "Wake-on-LAN Service is running (minimal mode)",
                "status": "healthy",
                "note": "Some features may be limited due to import issues"
            }
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "version": "1.0.0-minimal"}
        
        print("⚠️  使用最小化应用模式")
        return app

# 创建应用实例
app = main()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12345)
