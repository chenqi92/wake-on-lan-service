#!/usr/bin/env python3
"""
调试应用启动问题
"""

import sys
import traceback
import os

def test_basic_imports():
    """测试基础导入"""
    print("🔍 测试基础导入...")
    
    try:
        import fastapi
        print(f"  ✅ FastAPI: {fastapi.__version__}")
    except Exception as e:
        print(f"  ❌ FastAPI导入失败: {e}")
        return False
    
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import HTMLResponse
        print("  ✅ FastAPI组件导入成功")
    except Exception as e:
        print(f"  ❌ FastAPI组件导入失败: {e}")
        return False
    
    return True

def test_app_modules():
    """测试应用模块"""
    print("\n🔍 测试应用模块...")
    
    modules = [
        ("app.models", "LoginRequest, CaptchaResponse"),
        ("app.auth", "generate_captcha, auth_config"),
        ("app.templates", "get_login_template, get_main_template"),
        ("app.network_utils", "get_network_interfaces"),
        ("app.wake_on_lan", "wake_device_simple"),
    ]
    
    for module_name, items in modules:
        try:
            exec(f"from {module_name} import {items}")
            print(f"  ✅ {module_name}")
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            traceback.print_exc()
            return False
    
    return True

def test_template_generation():
    """测试模板生成"""
    print("\n🔍 测试模板生成...")
    
    try:
        from app.templates import get_login_template
        
        print("  - 生成登录模板...")
        html = get_login_template("1.0.1")
        
        if not html:
            print("  ❌ 模板为空")
            return False
        
        if len(html) < 1000:
            print(f"  ❌ 模板太短: {len(html)} 字符")
            return False
        
        if "登录" not in html:
            print("  ❌ 模板缺少登录关键字")
            return False
        
        print(f"  ✅ 登录模板生成成功 ({len(html)} 字符)")
        return True
        
    except Exception as e:
        print(f"  ❌ 模板生成失败: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """测试应用创建"""
    print("\n🔍 测试应用创建...")
    
    try:
        # 设置环境变量
        os.environ.update({
            'WOL_USERNAME': 'testuser',
            'WOL_PASSWORD': 'testpass123',
            'WOL_SESSION_SECRET': 'test-secret-key'
        })
        
        print("  - 导入主应用...")
        from app.main import app
        
        print("  - 检查应用实例...")
        if not app:
            print("  ❌ 应用实例为空")
            return False
        
        print("  - 检查路由...")
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"  ✅ 发现 {len(routes)} 个路由")
        
        expected_routes = ["/", "/health", "/api/captcha", "/api/login"]
        missing_routes = []
        
        for expected in expected_routes:
            if expected not in routes:
                missing_routes.append(expected)
        
        if missing_routes:
            print(f"  ❌ 缺少路由: {missing_routes}")
            print(f"  📋 现有路由: {routes}")
            return False
        
        print("  ✅ 关键路由都存在")
        return True
        
    except Exception as e:
        print(f"  ❌ 应用创建失败: {e}")
        traceback.print_exc()
        return False

def test_route_handler():
    """测试路由处理器"""
    print("\n🔍 测试路由处理器...")
    
    try:
        from app.main import web_interface, login_interface
        from fastapi import Request
        
        print("  - 测试登录界面函数...")
        html = None
        
        # 创建一个模拟的异步上下文
        import asyncio
        
        async def test_login():
            return await login_interface()
        
        # 运行异步函数
        html = asyncio.run(test_login())
        
        if not html:
            print("  ❌ 登录界面返回空")
            return False
        
        if "登录" not in html:
            print("  ❌ 登录界面缺少关键内容")
            return False
        
        print(f"  ✅ 登录界面生成成功 ({len(html)} 字符)")
        return True
        
    except Exception as e:
        print(f"  ❌ 路由处理器测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🐛 Wake-on-LAN 应用调试")
    print("=" * 60)
    
    tests = [
        ("基础导入", test_basic_imports),
        ("应用模块", test_app_modules),
        ("模板生成", test_template_generation),
        ("应用创建", test_app_creation),
        ("路由处理器", test_route_handler),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
                break  # 如果某个测试失败，停止后续测试
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
            traceback.print_exc()
            break
    
    print("\n" + "=" * 60)
    print(f"📊 调试结果: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("🎉 所有测试通过！应用应该能正常启动。")
        print("\n🚀 启动命令:")
        print("uvicorn app.main:app --host 0.0.0.0 --port 12345 --reload")
        return True
    else:
        print("⚠️  发现问题，请根据错误信息修复。")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
