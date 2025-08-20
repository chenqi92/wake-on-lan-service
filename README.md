# Wake-on-LAN Service

一个基于 FastAPI 的内网设备唤醒服务，支持通过 HTTP API 远程唤醒网络设备。

## 🚀 功能特性

- **简单唤醒**: 仅需提供 MAC 地址即可唤醒设备
- **高级唤醒**: 支持指定网络接口、广播地址、端口等参数
- **网络接口查询**: 查看所有可用的网络接口信息
- **RESTful API**: 完整的 HTTP API 接口
- **Docker 支持**: 提供完整的 Docker 镜像和编排文件
- **健康检查**: 内置服务健康检查接口
- **API 文档**: 自动生成的 Swagger/OpenAPI 文档
- **🔐 登录认证**: 账号密码 + 验证码登录保护
- **🛡️ 安全防护**: JWT令牌认证，会话管理
- **🔧 容器稳定性**: 优化的Docker配置，自动重启和健康检查

## 📋 API 接口

### 基础接口

- `GET /` - 服务基本信息
- `GET /health` - 健康检查
- `GET /docs` - API 文档 (Swagger UI)
- `GET /redoc` - API 文档 (ReDoc)

### 功能接口

- `GET /interfaces` - 查询所有网络接口
- `POST /wake` - 简单设备唤醒
- `POST /wake/advanced` - 高级设备唤醒

## 🛠️ 安装和使用

### 方式一: Docker 运行 (推荐)

#### 从 Docker Hub 拉取镜像

```bash
# 拉取最新镜像
docker pull kkape/wake-on-lan-service:latest

# 运行容器
docker run -d \
  --name wake-on-lan \
  --network host \
  -p 12345:12345 \
  kkape/wake-on-lan-service:latest
```

#### 使用 docker-compose

```bash
# 下载 docker-compose.yml 文件
curl -O https://raw.githubusercontent.com/chenqi92/wake-on-lan-service/master/docker-compose.yml

# 启动服务
docker-compose up -d
```

### 方式二: 本地构建

```bash
# 克隆仓库
git clone https://github.com/chenqi92/wake-on-lan-service.git
cd wake-up

# 构建并运行
docker build -t wake-on-lan-service .
docker run -d --name wake-on-lan --network host wake-on-lan-service
```

### 方式三: Python 直接运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 12345
```

## 📖 使用示例

### 查询网络接口

```bash
curl -X GET "http://localhost:12345/interfaces"
```

响应示例:
```json
{
  "interfaces": [
    {
      "name": "eth0",
      "ip_address": "192.168.1.100",
      "netmask": "255.255.255.0",
      "broadcast": "192.168.1.255",
      "mac_address": "aa:bb:cc:dd:ee:ff"
    }
  ],
  "count": 1
}
```

### 简单设备唤醒

```bash
curl -X POST "http://localhost:12345/wake" \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "aa:bb:cc:dd:ee:ff"}'
```

### 高级设备唤醒

```bash
curl -X POST "http://localhost:12345/wake/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "interface": "eth0",
    "broadcast_address": "192.168.1.255",
    "port": 9
  }'
```

## 🔧 配置说明

### 环境变量

#### 基础配置
- `HOST`: 服务监听地址 (默认: 0.0.0.0)
- `PORT`: 服务监听端口 (默认: 12345)

#### 🔐 认证配置
- `WOL_USERNAME`: 登录用户名 (默认: admin)
- `WOL_PASSWORD`: 登录密码 (默认: admin123)
- `WOL_SESSION_SECRET`: 会话密钥 (默认: your-secret-key-change-this)

⚠️ **安全提醒**: 生产环境请务必修改默认的用户名、密码和会话密钥！

### Docker 网络模式

为了访问主机的网络接口，容器需要使用 `--network host` 模式运行。这样容器可以直接访问主机的网络接口来发送 WOL 包。

## 📝 API 文档

启动服务后，可以通过以下地址访问 API 文档:

- Swagger UI: http://localhost:12345/docs
- ReDoc: http://localhost:12345/redoc

## 🐳 Docker 镜像信息

### 镜像标签

- `kkape/wake-on-lan-service:latest` - 最新版本
- `kkape/wake-on-lan-service:1.0.1` - 当前版本（从VERSION文件读取）

### 多平台支持

本镜像支持以下平台架构：
- **linux/amd64** - Intel/AMD 64位处理器
- **linux/arm64** - ARM 64位处理器 (Apple M1/M2, Raspberry Pi 4等)

Docker 会自动根据运行环境选择合适的镜像版本。

#### 构建状态
- ✅ **AMD64**: 已构建并推送
- 🔄 **ARM64**: 通过GitHub Actions自动构建
- 📦 **多平台manifest**: 自动创建统一镜像标签

#### 验证多平台支持
```bash
# 检查镜像支持的平台
docker manifest inspect kkape/wake-on-lan-service:latest

# 测试不同架构
docker run --rm kkape/wake-on-lan-service:latest python -c "import platform; print(f'架构: {platform.machine()}')"
```

### 镜像特性

- 基于 Python 3.11 slim 镜像
- 多平台架构支持 (AMD64/ARM64)
- 非 root 用户运行
- 内置健康检查
- 优化的镜像大小

## 🔐 登录认证

### 认证功能
- **登录界面**: 访问根路径 `/` 时，未认证用户将看到登录界面
- **验证码保护**: 每次登录都需要输入图形验证码，防止暴力破解
- **JWT令牌**: 登录成功后使用JWT令牌进行身份验证
- **会话管理**: 自动清理过期的会话和验证码
- **Cookie认证**: 支持Cookie和Authorization头两种认证方式

### 使用方法
1. 浏览器访问 `http://localhost:12345`
2. 输入配置的用户名和密码
3. 输入验证码（点击图片可刷新）
4. 登录成功后即可使用所有功能

### API认证
所有功能性API端点都需要认证：
- `GET /interfaces` - 需要认证
- `POST /wake` - 需要认证
- `POST /wake/advanced` - 需要认证

公开端点（无需认证）：
- `GET /health` - 健康检查
- `GET /docs` - API文档
- `POST /api/login` - 登录接口
- `GET /api/captcha` - 获取验证码

## 🔒 安全注意事项

### 网络安全
1. **网络访问**: 服务需要访问主机网络接口，请确保在受信任的网络环境中运行
2. **防火墙**: 确保目标设备的防火墙允许 WOL 包 (通常是 UDP 端口 9)
3. **访问控制**: 建议通过防火墙限制服务访问来源

### 设备要求
1. **BIOS 设置**: 目标设备需要在 BIOS/UEFI 中启用 Wake-on-LAN 功能
2. **网卡支持**: 目标设备的网卡需要支持 Wake-on-LAN 功能
3. **电源管理**: 确保设备在关机状态下网卡仍有供电

### 认证安全
1. **强密码**: 使用复杂的用户名和密码
2. **会话密钥**: 生产环境必须修改 `WOL_SESSION_SECRET`
3. **HTTPS**: 生产环境建议使用HTTPS（可通过反向代理实现）
4. **访问日志**: 定期检查访问日志，监控异常登录

## 🧪 测试

### 自动化测试

项目提供了两个测试脚本来验证功能：

#### Docker容器稳定性测试
```bash
python test_docker.py
```
测试内容：
- Docker环境检查
- 镜像构建和容器启动
- 服务健康检查
- 容器重启测试
- 压力测试

#### 认证功能测试
```bash
python test_auth.py
```
测试内容：
- 验证码生成和验证
- 登录认证流程
- 受保护端点访问控制
- Web界面重定向

### 手动测试

#### 基础功能测试
```bash
# 健康检查
curl http://localhost:12345/health

# 获取验证码
curl http://localhost:12345/api/captcha

# 登录（需要先获取验证码）
curl -X POST http://localhost:12345/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","captcha_id":"xxx","captcha_text":"1234"}'
```

#### Web界面测试
1. 浏览器访问 `http://localhost:12345`
2. 验证登录界面显示
3. 测试登录功能
4. 验证主界面功能

## 🔧 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 检查容器日志
docker logs wake-on-lan-service

# 检查端口占用
netstat -tuln | grep 12345

# 检查Docker权限
docker info
```

#### 2. 登录失败
- 检查环境变量配置
- 验证用户名密码是否正确
- 确认验证码输入正确
- 检查浏览器Cookie设置

#### 3. 网络接口访问失败
```bash
# 检查容器权限
docker inspect wake-on-lan-service | grep -A 10 "CapAdd"

# 检查网络模式
docker inspect wake-on-lan-service | grep -A 5 "NetworkMode"
```

#### 4. Wake-on-LAN功能失败
- 确认目标设备支持WOL
- 检查网络接口和广播地址
- 验证MAC地址格式
- 确认目标设备网络配置

### 日志分析

#### 应用日志
```bash
# 查看实时日志
docker logs -f wake-on-lan-service

# 查看最近日志
docker logs --tail 50 wake-on-lan-service
```

#### 健康检查日志
```bash
# 检查健康状态
docker inspect wake-on-lan-service | grep -A 10 "Health"
```

## 🛠️ 开发

### 项目结构

```
wake-up/
├── app/                          # 主应用代码
│   ├── __init__.py              # 包初始化
│   ├── main.py                  # FastAPI应用主文件（含Web界面）
│   ├── models.py                # 数据模型定义
│   ├── network_utils.py         # 网络工具函数
│   ├── wake_on_lan.py           # WOL核心功能
│   └── static/                  # 静态文件目录
├── .github/workflows/           # GitHub Actions工作流
│   └── docker-build.yml        # 多平台Docker构建
├── VERSION                      # 版本号文件
├── Dockerfile                   # Docker镜像构建文件
├── docker-compose.yml          # Docker编排文件
├── requirements.txt             # Python依赖
├── build_and_push.sh           # 构建脚本 (Linux/Mac)
├── build_and_push.bat          # 构建脚本 (Windows)
├── build_and_push_legacy.bat   # 传统构建脚本 (Windows)
├── test_service.py             # 功能测试套件
├── example_usage.py            # 使用示例脚本
└── README.md                   # 项目文档
```

### 本地开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 12345
```

### 多平台Docker构建

#### 版本管理

项目使用 `VERSION` 文件管理版本号：
```bash
# 查看当前版本
cat VERSION

# 更新版本（更新后重新构建镜像）
echo "1.0.2" > VERSION
```

#### 构建和推送

1. **GitHub Actions自动构建（推荐）**：
```bash
# 推送到master分支自动触发多平台构建
git push origin master

# 或创建标签触发版本构建
git tag v1.0.1
git push origin v1.0.1
```

2. **本地构建脚本**：
```bash
# Linux/Mac
./build_and_push.sh

# Windows
build_and_push.bat
```

#### 验证多平台镜像

```bash
# 手动验证
docker manifest inspect kkape/wake-on-lan-service:latest

# 测试不同平台
docker run --rm kkape/wake-on-lan-service:latest python -c "import platform; print(f'架构: {platform.machine()}')"
```

> **注意**: 完整的多平台支持通过GitHub Actions实现。本地环境可能无法构建ARM64镜像。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📞 支持

如有问题，请通过以下方式联系:

- 提交 [GitHub Issue](https://github.com/chenqi92/wake-on-lan-service/issues)
- 邮箱: contact@kkape.com

---

**作者**: kkape  
**版本**: 从VERSION文件读取
**更新时间**: 2025-06-23
