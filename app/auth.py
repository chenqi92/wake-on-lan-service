"""
认证模块 - 处理用户登录、会话管理和验证码生成
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from io import BytesIO
import base64

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from PIL import Image, ImageDraw, ImageFont
import random
import string

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = os.getenv("WOL_SESSION_SECRET", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)

# 内存中的验证码存储（生产环境建议使用Redis）
captcha_store: Dict[str, Dict[str, Any]] = {}

# 会话存储（生产环境建议使用Redis）
session_store: Dict[str, Dict[str, Any]] = {}


class AuthConfig:
    """认证配置类"""
    
    def __init__(self):
        self.username = os.getenv("WOL_USERNAME", "admin")
        self.password = os.getenv("WOL_PASSWORD", "admin123")
        self.session_secret = os.getenv("WOL_SESSION_SECRET", "your-secret-key-change-this")
        
        # 验证配置
        if self.session_secret == "your-secret-key-change-this":
            print("警告: 使用默认的会话密钥，生产环境请修改 WOL_SESSION_SECRET 环境变量")
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """验证用户凭据"""
        return username == self.username and password == self.password


# 全局认证配置实例
auth_config = AuthConfig()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证访问令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return {"username": username}
    except JWTError:
        return None


def generate_captcha_text(length: int = 4) -> str:
    """生成验证码文本"""
    # 避免容易混淆的字符
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(random.choice(chars) for _ in range(length))


def create_captcha_image(text: str, width: int = 120, height: int = 40) -> str:
    """创建验证码图片并返回base64编码"""
    # 创建图片
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 尝试使用系统字体，如果失败则使用默认字体
    try:
        # 在不同系统上尝试不同的字体路径
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "C:/Windows/Fonts/arial.ttf",  # Windows
        ]
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 20)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # 添加背景噪点
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(200, 255), random.randint(200, 255), random.randint(200, 255)))
    
    # 绘制验证码文本
    text_width = draw.textlength(text, font=font) if hasattr(draw, 'textlength') else len(text) * 15
    text_height = 20
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 为每个字符添加随机颜色和位置偏移
    char_width = text_width // len(text)
    for i, char in enumerate(text):
        char_x = x + i * char_width + random.randint(-3, 3)
        char_y = y + random.randint(-3, 3)
        color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        draw.text((char_x, char_y), char, fill=color, font=font)
    
    # 添加干扰线
    for _ in range(3):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([start, end], fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)), width=1)
    
    # 转换为base64
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def generate_captcha() -> Dict[str, str]:
    """生成验证码"""
    captcha_id = secrets.token_urlsafe(16)
    captcha_text = generate_captcha_text()
    captcha_image = create_captcha_image(captcha_text)
    
    # 存储验证码（5分钟过期）
    captcha_store[captcha_id] = {
        "text": captcha_text.upper(),
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    }
    
    # 清理过期的验证码
    cleanup_expired_captchas()
    
    return {
        "captcha_id": captcha_id,
        "captcha_image": captcha_image
    }


def verify_captcha(captcha_id: str, captcha_text: str) -> bool:
    """验证验证码"""
    if captcha_id not in captcha_store:
        return False
    
    stored_captcha = captcha_store[captcha_id]
    
    # 检查是否过期
    if datetime.utcnow() > stored_captcha["expires_at"]:
        del captcha_store[captcha_id]
        return False
    
    # 验证文本（不区分大小写）
    is_valid = stored_captcha["text"].upper() == captcha_text.upper()
    
    # 验证后删除验证码（一次性使用）
    del captcha_store[captcha_id]
    
    return is_valid


def cleanup_expired_captchas():
    """清理过期的验证码"""
    current_time = datetime.utcnow()
    expired_ids = [
        captcha_id for captcha_id, captcha_data in captcha_store.items()
        if current_time > captcha_data["expires_at"]
    ]
    
    for captcha_id in expired_ids:
        del captcha_store[captcha_id]


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """获取当前用户（依赖注入）"""
    
    # 首先尝试从Authorization header获取token
    token = None
    if credentials:
        token = credentials.credentials
    
    # 如果没有Authorization header，尝试从cookie获取
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证token
    user_data = verify_token(token)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data


def create_session(username: str) -> str:
    """创建用户会话"""
    session_id = secrets.token_urlsafe(32)
    session_store[session_id] = {
        "username": username,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    return session_id


def verify_session(session_id: str) -> Optional[Dict[str, Any]]:
    """验证会话"""
    if session_id not in session_store:
        return None
    
    session_data = session_store[session_id]
    
    # 检查是否过期
    if datetime.utcnow() > session_data["expires_at"]:
        del session_store[session_id]
        return None
    
    return session_data


def cleanup_expired_sessions():
    """清理过期的会话"""
    current_time = datetime.utcnow()
    expired_ids = [
        session_id for session_id, session_data in session_store.items()
        if current_time > session_data["expires_at"]
    ]
    
    for session_id in expired_ids:
        del session_store[session_id]
