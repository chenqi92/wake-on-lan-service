#!/usr/bin/env python3
"""
Wake-on-LAN Service 使用示例
演示如何使用API接口唤醒设备
"""

import requests
import json
import sys


def main():
    # 服务地址
    base_url = "http://localhost:12345"
    
    print("🌟 Wake-on-LAN Service 使用示例")
    print("=" * 40)
    
    try:
        # 1. 检查服务状态
        print("1️⃣ 检查服务状态...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 服务运行正常 (版本: {health_data['version']})")
        else:
            print("❌ 服务不可用")
            return
        
        # 2. 查询网络接口
        print("\n2️⃣ 查询网络接口...")
        response = requests.get(f"{base_url}/interfaces")
        if response.status_code == 200:
            interfaces_data = response.json()
            print(f"找到 {interfaces_data['count']} 个网络接口:")
            for i, interface in enumerate(interfaces_data['interfaces'], 1):
                print(f"  {i}. {interface['name']} - {interface['ip_address']}")
                if interface['broadcast']:
                    print(f"     广播地址: {interface['broadcast']}")
        
        # 3. 获取用户输入
        print("\n3️⃣ 设备唤醒设置")
        mac_address = input("请输入要唤醒的设备MAC地址 (格式: aa:bb:cc:dd:ee:ff): ").strip()
        
        if not mac_address:
            print("❌ MAC地址不能为空")
            return
        
        # 4. 选择唤醒方式
        print("\n选择唤醒方式:")
        print("1. 简单唤醒 (使用默认设置)")
        print("2. 高级唤醒 (自定义参数)")
        
        choice = input("请选择 (1 或 2): ").strip()
        
        if choice == "1":
            # 简单唤醒
            print(f"\n4️⃣ 执行简单唤醒 (MAC: {mac_address})...")
            payload = {"mac_address": mac_address}
            response = requests.post(
                f"{base_url}/wake",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
        elif choice == "2":
            # 高级唤醒
            print(f"\n4️⃣ 执行高级唤醒 (MAC: {mac_address})...")
            
            # 可选参数
            interface = input("指定网络接口 (留空使用默认): ").strip() or None
            broadcast = input("指定广播地址 (留空使用默认): ").strip() or None
            port_input = input("指定端口 (留空使用9): ").strip()
            port = int(port_input) if port_input else 9
            
            payload = {
                "mac_address": mac_address,
                "port": port
            }
            if interface:
                payload["interface"] = interface
            if broadcast:
                payload["broadcast_address"] = broadcast
            
            response = requests.post(
                f"{base_url}/wake/advanced",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
        else:
            print("❌ 无效选择")
            return
        
        # 5. 处理响应
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 唤醒成功!")
            print(f"   消息: {result['message']}")
            print(f"   使用接口: {result['interface_used']}")
            print(f"   广播地址: {result['broadcast_address']}")
            print(f"   目标MAC: {result['mac_address']}")
        else:
            print(f"\n❌ 唤醒失败 (HTTP {response.status_code})")
            try:
                error_data = response.json()
                print(f"   错误: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   响应: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请确保服务正在运行")
        print("   启动命令: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except KeyboardInterrupt:
        print("\n\n⏹️ 操作被用户取消")
    except Exception as e:
        print(f"\n💥 发生错误: {e}")


if __name__ == "__main__":
    main()
