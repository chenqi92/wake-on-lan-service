import socket
import struct
from typing import Optional, Tuple
from app.network_utils import get_default_interface, get_interface_by_name, calculate_broadcast_address


def create_magic_packet(mac_address: str) -> bytes:
    """
    创建WOL魔术包
    
    Args:
        mac_address: MAC地址，格式为 XX:XX:XX:XX:XX:XX
        
    Returns:
        bytes: 魔术包数据
    """
    # 移除MAC地址中的分隔符
    mac_address = mac_address.replace(':', '').replace('-', '')
    
    # 验证MAC地址长度
    if len(mac_address) != 12:
        raise ValueError("MAC地址长度无效")
    
    # 将MAC地址转换为字节
    mac_bytes = bytes.fromhex(mac_address)
    
    # 创建魔术包：6个0xFF字节 + 16次重复的MAC地址
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    
    return magic_packet


def send_wake_on_lan(mac_address: str, 
                    interface_name: Optional[str] = None,
                    broadcast_address: Optional[str] = None,
                    port: int = 9) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    发送Wake-on-LAN魔术包
    
    Args:
        mac_address: 目标设备MAC地址
        interface_name: 指定的网络接口名称（可选）
        broadcast_address: 指定的广播地址（可选）
        port: WOL端口号，默认为9
        
    Returns:
        Tuple[bool, str, Optional[str], Optional[str]]: 
        (是否成功, 消息, 使用的接口, 使用的广播地址)
    """
    try:
        # 创建魔术包
        magic_packet = create_magic_packet(mac_address)
        
        # 确定使用的网络接口
        if interface_name:
            interface = get_interface_by_name(interface_name)
            if not interface:
                return False, f"网络接口 '{interface_name}' 不存在", None, None
        else:
            interface = get_default_interface()
            if not interface:
                return False, "无法获取默认网络接口", None, None
        
        # 确定广播地址
        if broadcast_address:
            target_broadcast = broadcast_address
        else:
            if interface.broadcast:
                target_broadcast = interface.broadcast
            else:
                # 如果接口没有广播地址，计算一个
                target_broadcast = calculate_broadcast_address(
                    interface.ip_address, 
                    interface.netmask
                )
        
        # 创建UDP套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            # 绑定到指定的网络接口
            sock.bind((interface.ip_address, 0))
            
            # 发送魔术包
            sock.sendto(magic_packet, (target_broadcast, port))
            
            message = f"成功发送WOL包到 {mac_address}"
            return True, message, interface.name, target_broadcast
            
        finally:
            sock.close()
            
    except ValueError as e:
        return False, f"参数错误: {str(e)}", None, None
    except socket.error as e:
        return False, f"网络错误: {str(e)}", None, None
    except Exception as e:
        return False, f"未知错误: {str(e)}", None, None


def wake_device_simple(mac_address: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    简单的设备唤醒功能，使用默认设置
    
    Args:
        mac_address: 目标设备MAC地址
        
    Returns:
        Tuple[bool, str, Optional[str], Optional[str]]: 
        (是否成功, 消息, 使用的接口, 使用的广播地址)
    """
    return send_wake_on_lan(mac_address)


def wake_device_advanced(mac_address: str,
                        interface_name: Optional[str] = None,
                        broadcast_address: Optional[str] = None,
                        port: int = 9) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    高级设备唤醒功能，支持自定义参数
    
    Args:
        mac_address: 目标设备MAC地址
        interface_name: 指定的网络接口名称
        broadcast_address: 指定的广播地址
        port: WOL端口号
        
    Returns:
        Tuple[bool, str, Optional[str], Optional[str]]: 
        (是否成功, 消息, 使用的接口, 使用的广播地址)
    """
    return send_wake_on_lan(mac_address, interface_name, broadcast_address, port)
