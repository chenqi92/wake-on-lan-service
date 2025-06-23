from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re


class NetworkInterface(BaseModel):
    """网络接口信息模型"""
    name: str = Field(..., description="网络接口名称")
    ip_address: str = Field(..., description="IP地址")
    netmask: str = Field(..., description="子网掩码")
    broadcast: Optional[str] = Field(None, description="广播地址")
    mac_address: Optional[str] = Field(None, description="MAC地址")


class WakeRequest(BaseModel):
    """基础唤醒请求模型"""
    mac_address: str = Field(..., description="目标设备MAC地址")
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        # 移除常见的分隔符并转换为标准格式
        mac = re.sub(r'[:-]', '', v.upper())
        if not re.match(r'^[0-9A-F]{12}$', mac):
            raise ValueError('MAC地址格式无效，应为 XX:XX:XX:XX:XX:XX 或 XX-XX-XX-XX-XX-XX 格式')
        return ':'.join([mac[i:i+2] for i in range(0, 12, 2)])


class AdvancedWakeRequest(WakeRequest):
    """高级唤醒请求模型"""
    interface: Optional[str] = Field(None, description="指定网络接口名称")
    broadcast_address: Optional[str] = Field(None, description="指定广播地址")
    port: int = Field(9, description="WOL端口号，默认为9")
    
    @validator('broadcast_address')
    def validate_broadcast_address(cls, v):
        if v is not None:
            # 简单的IP地址格式验证
            if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', v):
                raise ValueError('广播地址格式无效')
        return v


class WakeResponse(BaseModel):
    """唤醒响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    mac_address: str = Field(..., description="目标MAC地址")
    interface_used: Optional[str] = Field(None, description="使用的网络接口")
    broadcast_address: Optional[str] = Field(None, description="使用的广播地址")


class InterfacesResponse(BaseModel):
    """网络接口查询响应模型"""
    interfaces: List[NetworkInterface] = Field(..., description="网络接口列表")
    count: int = Field(..., description="接口数量")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="服务版本")
    uptime: str = Field(..., description="运行时间")
