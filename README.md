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
curl -O https://raw.githubusercontent.com/kkape/wake-on-lan-service/main/docker-compose.yml

# 启动服务
docker-compose up -d
```

### 方式二: 本地构建

```bash
# 克隆仓库
git clone <repository-url>
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

- `HOST`: 服务监听地址 (默认: 0.0.0.0)
- `PORT`: 服务监听端口 (默认: 12345)

### Docker 网络模式

为了访问主机的网络接口，容器需要使用 `--network host` 模式运行。这样容器可以直接访问主机的网络接口来发送 WOL 包。

## 📝 API 文档

启动服务后，可以通过以下地址访问 API 文档:

- Swagger UI: http://localhost:12345/docs
- ReDoc: http://localhost:12345/redoc

## 🐳 Docker 镜像信息

### 镜像标签

- `kkape/wake-on-lan-service:latest` - 最新版本
- `kkape/wake-on-lan-service:1.0.1` - 指定版本

### 多平台支持

本镜像支持以下平台架构：
- **linux/amd64** - Intel/AMD 64位处理器
- **linux/arm64** - ARM 64位处理器 (Apple M1/M2, Raspberry Pi 4等)

Docker 会自动根据运行环境选择合适的镜像版本。

### 镜像特性

- 基于 Python 3.11 slim 镜像
- 多平台架构支持 (AMD64/ARM64)
- 非 root 用户运行
- 内置健康检查
- 优化的镜像大小

## 🔒 安全注意事项

1. **网络访问**: 服务需要访问主机网络接口，请确保在受信任的网络环境中运行
2. **防火墙**: 确保目标设备的防火墙允许 WOL 包 (通常是 UDP 端口 9)
3. **BIOS 设置**: 目标设备需要在 BIOS/UEFI 中启用 Wake-on-LAN 功能
4. **网卡支持**: 目标设备的网卡需要支持 Wake-on-LAN 功能

## 🛠️ 开发

### 项目结构

```
wake-up/
├── app/
│   ├── __init__.py              # 包初始化
│   ├── main.py                  # FastAPI 应用主文件
│   ├── models.py                # 数据模型定义
│   ├── network_utils.py         # 网络工具函数
│   └── wake_on_lan.py           # WOL 核心功能
├── requirements.txt             # Python 依赖
├── Dockerfile                   # Docker 镜像构建文件
├── docker-compose.yml          # Docker 编排文件
├── build_and_push.sh           # 多平台构建脚本 (Linux/Mac)
├── build_and_push.bat          # 多平台构建脚本 (Windows)
├── check_build_env.sh          # 构建环境检查 (Linux/Mac)
├── check_build_env.bat         # 构建环境检查 (Windows)
├── verify_multiplatform.sh     # 多平台镜像验证 (Linux/Mac)
├── verify_multiplatform.bat    # 多平台镜像验证 (Windows)
├── start_service.sh            # 快速启动脚本 (Linux/Mac)
├── start_service.bat           # 快速启动脚本 (Windows)
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

#### 环境准备

1. **检查构建环境**：
```bash
# Linux/Mac
./check_build_env.sh

# Windows
check_build_env.bat
```

2. **确保Docker Buildx可用**：
```bash
# 检查Buildx版本
docker buildx version

# 创建多平台构建器
docker buildx create --name multiarch-builder --use --bootstrap
```

#### 构建和推送

1. **自动构建推送**：
```bash
# Linux/Mac
./build_and_push.sh

# Windows
build_and_push.bat
```

2. **手动构建推送**：
```bash
# 登录Docker Hub
docker login

# 构建并推送多平台镜像
docker buildx build --platform linux/amd64,linux/arm64 \
  -t kkape/wake-on-lan-service:1.0.1 \
  -t kkape/wake-on-lan-service:latest \
  --push .
```

#### 验证多平台镜像

```bash
# 使用验证脚本
./verify_multiplatform.sh  # Linux/Mac
verify_multiplatform.bat   # Windows

# 手动验证
docker buildx imagetools inspect kkape/wake-on-lan-service:latest

# 测试不同平台
docker run --rm kkape/wake-on-lan-service:latest python -c "import platform; print(f'架构: {platform.machine()}')"
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📞 支持

如有问题，请通过以下方式联系:

- 提交 GitHub Issue
- 邮箱: [your-email@example.com]

---

**作者**: kkape  
**版本**: 1.0.1
**更新时间**: 2025-06-23
