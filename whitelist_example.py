#!/usr/bin/env python3
"""
IP白名单功能使用示例
"""

import requests
import json

# 服务配置
BASE_URL = "http://localhost:12345"

def example_admin_login():
    """示例：管理员登录"""
    print("=== 管理员登录示例 ===")
    
    # 1. 获取验证码
    captcha_response = requests.get(f"{BASE_URL}/api/captcha")
    captcha_data = captcha_response.json()
    print(f"获取验证码: {captcha_data['captcha_id'][:8]}...")
    
    # 2. 登录（实际使用时需要输入正确的验证码）
    login_data = {
        "username": "admin",
        "password": "admin123",
        "captcha_id": captcha_data["captcha_id"],
        "captcha_text": "1234"  # 实际需要从图片中识别
    }
    
    login_response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    if login_response.status_code == 200:
        result = login_response.json()
        if result.get("success"):
            print("✅ 登录成功")
            return result["access_token"]
        else:
            print(f"❌ 登录失败: {result['message']}")
    else:
        print(f"❌ 登录请求失败: {login_response.status_code}")
    
    return None

def example_manage_whitelist(token):
    """示例：管理IP白名单"""
    print("\n=== IP白名单管理示例 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 查看当前白名单
    print("1. 查看当前白名单:")
    response = requests.get(f"{BASE_URL}/api/whitelist", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   当前白名单数量: {data['count']}")
        for item in data['whitelist']:
            print(f"   - {item['ip']}")
    
    # 2. 添加IP到白名单
    print("\n2. 添加IP到白名单:")
    add_data = {
        "ip": "192.168.1.100",
        "description": "办公室电脑"
    }
    response = requests.post(f"{BASE_URL}/api/whitelist/add", json=add_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   {result['message']}")
    
    # 3. 添加网段到白名单
    print("\n3. 添加网段到白名单:")
    add_data = {
        "ip": "10.0.0.0/24",
        "description": "内网网段"
    }
    response = requests.post(f"{BASE_URL}/api/whitelist/add", json=add_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   {result['message']}")
    
    # 4. 再次查看白名单
    print("\n4. 更新后的白名单:")
    response = requests.get(f"{BASE_URL}/api/whitelist", headers=headers)
    if response.status_code == 200:
        data = response.json()
        for item in data['whitelist']:
            print(f"   - {item['ip']}: {item.get('description', '无描述')}")

def example_whitelist_api_access():
    """示例：白名单IP免认证访问API"""
    print("\n=== 白名单IP免认证访问示例 ===")
    
    # 1. 检查当前IP状态
    print("1. 检查当前IP状态:")
    response = requests.get(f"{BASE_URL}/api/whitelist/check")
    if response.status_code == 200:
        data = response.json()
        print(f"   当前IP: {data['client_ip']}")
        print(f"   白名单状态: {'✅ 在白名单中' if data['in_whitelist'] else '❌ 不在白名单中'}")
        print(f"   消息: {data['message']}")
    
    # 2. 尝试无认证访问受保护的API
    print("\n2. 尝试无认证访问API:")
    
    # 测试网络接口API
    response = requests.get(f"{BASE_URL}/interfaces")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 网络接口API访问成功，发现 {data['count']} 个接口")
    elif response.status_code == 401:
        print("   ❌ 需要认证，当前IP不在白名单中")
    else:
        print(f"   ❌ API访问失败: {response.status_code}")
    
    # 测试Wake-on-LAN API
    wol_data = {"mac_address": "AA:BB:CC:DD:EE:FF"}
    response = requests.post(f"{BASE_URL}/wake", json=wol_data)
    if response.status_code == 200:
        print("   ✅ Wake-on-LAN API访问成功")
    elif response.status_code == 401:
        print("   ❌ Wake-on-LAN API需要认证")
    else:
        print(f"   ❌ Wake-on-LAN API访问失败: {response.status_code}")

def example_web_interface_usage():
    """示例：Web界面使用说明"""
    print("\n=== Web界面使用示例 ===")
    
    print("1. 访问Web界面:")
    print(f"   浏览器打开: {BASE_URL}")
    print("   - 未登录用户会看到登录界面")
    print("   - 白名单用户会直接看到主界面（但无法管理白名单）")
    print("   - 管理员登录后可以管理白名单")
    
    print("\n2. 白名单管理操作:")
    print("   - 查看当前白名单列表")
    print("   - 添加新的IP地址或CIDR网段")
    print("   - 移除不需要的白名单项")
    print("   - 检查当前访问IP的白名单状态")
    
    print("\n3. 支持的IP格式:")
    print("   - 单个IPv4地址: 192.168.1.100")
    print("   - 单个IPv6地址: 2001:db8::1")
    print("   - IPv4网段: 192.168.1.0/24")
    print("   - IPv6网段: 2001:db8::/32")

def example_api_integration():
    """示例：API集成"""
    print("\n=== API集成示例 ===")
    
    print("Python代码示例:")
    print("""
# 1. 检查IP白名单状态
import requests

def check_whitelist_status():
    response = requests.get('http://localhost:12345/api/whitelist/check')
    data = response.json()
    return data['in_whitelist']

# 2. 白名单IP直接调用API
def wake_device_if_whitelisted(mac_address):
    if check_whitelist_status():
        # 白名单IP，直接调用
        response = requests.post('http://localhost:12345/wake', 
                               json={'mac_address': mac_address})
        return response.json()
    else:
        # 非白名单IP，需要先登录获取token
        token = login_and_get_token()
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post('http://localhost:12345/wake',
                               json={'mac_address': mac_address},
                               headers=headers)
        return response.json()

# 3. 管理员添加IP到白名单
def add_ip_to_whitelist(token, ip, description=None):
    headers = {'Authorization': f'Bearer {token}'}
    data = {'ip': ip}
    if description:
        data['description'] = description
    
    response = requests.post('http://localhost:12345/api/whitelist/add',
                           json=data, headers=headers)
    return response.json()
    """)

def main():
    """主函数"""
    print("Wake-on-LAN IP白名单功能使用示例")
    print("=" * 50)
    
    # 示例1：管理员登录
    token = example_admin_login()
    
    if token:
        # 示例2：管理白名单
        example_manage_whitelist(token)
    
    # 示例3：白名单IP访问
    example_whitelist_api_access()
    
    # 示例4：Web界面使用
    example_web_interface_usage()
    
    # 示例5：API集成
    example_api_integration()
    
    print("\n" + "=" * 50)
    print("💡 重要提示:")
    print("1. 白名单功能提供便利性，但请注意安全性")
    print("2. 建议只将可信的内网IP添加到白名单")
    print("3. 定期审查和清理白名单")
    print("4. 生产环境建议使用HTTPS")
    print("5. 白名单用户无法管理白名单，防止权限滥用")

if __name__ == "__main__":
    main()
