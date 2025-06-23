import psutil
import socket
import ipaddress
from typing import List, Optional, Dict, Any
from app.models import NetworkInterface


def get_network_interfaces() -> List[NetworkInterface]:
    """
    获取所有网络接口信息

    Returns:
        List[NetworkInterface]: 网络接口列表
    """
    interfaces = []

    try:
        # 使用psutil获取网络接口信息
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()

        for interface_name, addrs in net_if_addrs.items():
            # 跳过回环接口和非活动接口
            if interface_name.lower().startswith('lo') or interface_name.lower() == 'loopback':
                continue

            # 检查接口是否活动
            if interface_name in net_if_stats and not net_if_stats[interface_name].isup:
                continue

            # 查找IPv4地址
            ipv4_addr = None
            mac_address = None

            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    if addr.address != '127.0.0.1':
                        ipv4_addr = addr
                elif addr.family == psutil.AF_LINK:  # MAC地址
                    mac_address = addr.address

            if ipv4_addr:
                # 计算广播地址
                broadcast = None
                netmask = ipv4_addr.netmask
                if netmask:
                    try:
                        network = ipaddress.IPv4Network(f"{ipv4_addr.address}/{netmask}", strict=False)
                        broadcast = str(network.broadcast_address)
                    except:
                        broadcast = calculate_broadcast_address(ipv4_addr.address, netmask)

                interface = NetworkInterface(
                    name=interface_name,
                    ip_address=ipv4_addr.address,
                    netmask=netmask or '',
                    broadcast=broadcast,
                    mac_address=mac_address
                )
                interfaces.append(interface)

    except Exception as e:
        print(f"获取网络接口信息时出错: {e}")

    return interfaces


def get_interface_by_name(interface_name: str) -> Optional[NetworkInterface]:
    """
    根据接口名称获取网络接口信息
    
    Args:
        interface_name: 网络接口名称
        
    Returns:
        Optional[NetworkInterface]: 网络接口信息，如果不存在则返回None
    """
    interfaces = get_network_interfaces()
    for interface in interfaces:
        if interface.name == interface_name:
            return interface
    return None


def get_default_interface() -> Optional[NetworkInterface]:
    """
    获取默认网络接口

    Returns:
        Optional[NetworkInterface]: 默认网络接口信息
    """
    try:
        # 尝试通过连接到外部地址来确定默认接口
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 连接到Google DNS，不会实际发送数据
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]

        # 查找对应的接口
        interfaces = get_network_interfaces()
        for interface in interfaces:
            if interface.ip_address == local_ip:
                return interface

    except Exception as e:
        print(f"获取默认网络接口时出错: {e}")

    # 如果无法获取默认接口，返回第一个可用接口
    interfaces = get_network_interfaces()
    return interfaces[0] if interfaces else None


def calculate_broadcast_address(ip_address: str, netmask: str) -> str:
    """
    计算广播地址
    
    Args:
        ip_address: IP地址
        netmask: 子网掩码
        
    Returns:
        str: 广播地址
    """
    try:
        # 将IP地址和子网掩码转换为整数
        ip_int = int(socket.inet_aton(ip_address).hex(), 16)
        mask_int = int(socket.inet_aton(netmask).hex(), 16)
        
        # 计算网络地址
        network_int = ip_int & mask_int
        
        # 计算广播地址
        broadcast_int = network_int | (0xFFFFFFFF ^ mask_int)
        
        # 转换回IP地址格式
        broadcast_bytes = broadcast_int.to_bytes(4, byteorder='big')
        return socket.inet_ntoa(broadcast_bytes)
    except Exception as e:
        print(f"计算广播地址时出错: {e}")
        return "255.255.255.255"


def is_valid_ip(ip_address: str) -> bool:
    """
    验证IP地址格式是否正确
    
    Args:
        ip_address: IP地址字符串
        
    Returns:
        bool: 是否为有效的IP地址
    """
    try:
        socket.inet_aton(ip_address)
        return True
    except socket.error:
        return False
