# Wake-on-LAN Service 部署指南

## 🎯 项目概述

这是一个完整的内网设备唤醒服务，支持通过HTTP API远程唤醒网络设备。项目已成功构建并推送到Docker Hub，支持快速部署。

## 📦 Docker镜像信息

- **镜像名称**: `kkape/wake-on-lan-service`
- **可用标签**: `latest`, `1.0.0`
- **镜像大小**: ~170MB
- **支持架构**: linux/amd64 (当前版本)
- **Docker Hub地址**: https://hub.docker.com/r/kkape/wake-on-lan-service

## 🚀 快速部署

### 方式一：一键部署脚本

```bash
# Windows
deploy_and_test.bat

# Linux/Mac (需要先给脚本执行权限)
chmod +x deploy_and_test.sh
./deploy_and_test.sh
```

### 方式二：手动部署

```bash
# 1. 拉取镜像
docker pull kkape/wake-on-lan-service:latest

# 2. 运行容器
docker run -d \
  --name wake-on-lan-service \
  --network host \
  -p 8000:8000 \
  kkape/wake-on-lan-service:latest

# 3. 验证服务
curl http://localhost:8000/health
```

### 方式三：使用docker-compose

```bash
# 使用项目中的docker-compose.yml
docker-compose up -d

# 或者创建简单的compose文件
cat > docker-compose.yml << EOF
version: '3.8'
services:
  wake-on-lan:
    image: kkape/wake-on-lan-service:latest
    container_name: wake-on-lan-service
    network_mode: host
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF

docker-compose up -d
```

## 🔧 API 使用

### 基础接口

```bash
# 健康检查
curl http://localhost:8000/health

# 查询网络接口
curl http://localhost:8000/interfaces

# API文档
# 浏览器访问: http://localhost:8000/docs
```

### 设备唤醒

```bash
# 简单唤醒（推荐）
curl -X POST "http://localhost:8000/wake" \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "aa:bb:cc:dd:ee:ff"}'

# 高级唤醒（自定义参数）
curl -X POST "http://localhost:8000/wake/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "interface": "eth0",
    "broadcast_address": "192.168.1.255",
    "port": 9
  }'
```

## 🧪 测试验证

### 自动化测试

```bash
# 运行完整测试套件
python test_service.py

# 交互式使用示例
python example_usage.py
```

### 手动测试

```bash
# 1. 检查服务状态
docker ps | grep wake-on-lan

# 2. 查看服务日志
docker logs wake-on-lan-service

# 3. 测试API响应
curl -s http://localhost:8000/health | python -m json.tool

# 4. 查看网络接口
curl -s http://localhost:8000/interfaces | python -m json.tool
```

## 🔒 安全配置

### 网络要求

- 容器需要使用 `--network host` 模式以访问主机网络接口
- 确保防火墙允许UDP端口9（WOL默认端口）
- 目标设备需要启用Wake-on-LAN功能

### 生产环境建议

```bash
# 1. 使用特定版本标签
docker run -d \
  --name wake-on-lan-service \
  --network host \
  --restart unless-stopped \
  kkape/wake-on-lan-service:1.0.0

# 2. 限制资源使用
docker run -d \
  --name wake-on-lan-service \
  --network host \
  --memory 256m \
  --cpus 0.5 \
  kkape/wake-on-lan-service:latest

# 3. 添加健康检查监控
docker run -d \
  --name wake-on-lan-service \
  --network host \
  --health-cmd "python -c 'import requests; requests.get(\"http://localhost:8000/health\")'" \
  --health-interval 30s \
  --health-timeout 10s \
  --health-retries 3 \
  kkape/wake-on-lan-service:latest
```

## 📊 监控和维护

### 容器管理

```bash
# 查看容器状态
docker ps -a | grep wake-on-lan

# 查看资源使用
docker stats wake-on-lan-service

# 重启服务
docker restart wake-on-lan-service

# 更新镜像
docker pull kkape/wake-on-lan-service:latest
docker stop wake-on-lan-service
docker rm wake-on-lan-service
# 然后重新运行容器
```

### 日志管理

```bash
# 查看实时日志
docker logs -f wake-on-lan-service

# 查看最近日志
docker logs --tail 100 wake-on-lan-service

# 日志轮转配置
docker run -d \
  --name wake-on-lan-service \
  --network host \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  kkape/wake-on-lan-service:latest
```

## 🛠️ 故障排除

### 常见问题

1. **容器无法启动**
   ```bash
   docker logs wake-on-lan-service
   # 检查端口是否被占用
   netstat -tulpn | grep 8000
   ```

2. **无法唤醒设备**
   - 确认目标设备MAC地址正确
   - 检查目标设备是否启用WOL
   - 验证网络接口和广播地址
   - 确认防火墙设置

3. **API无法访问**
   ```bash
   # 检查容器网络模式
   docker inspect wake-on-lan-service | grep NetworkMode
   
   # 测试容器内部服务
   docker exec wake-on-lan-service curl localhost:8000/health
   ```

### 调试模式

```bash
# 以交互模式运行容器进行调试
docker run -it --rm \
  --network host \
  kkape/wake-on-lan-service:latest \
  /bin/bash

# 在容器内手动启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📈 性能优化

### 资源配置

```bash
# 生产环境推荐配置
docker run -d \
  --name wake-on-lan-service \
  --network host \
  --memory 128m \
  --memory-swap 256m \
  --cpus 0.25 \
  --restart unless-stopped \
  kkape/wake-on-lan-service:latest
```

### 扩展部署

```bash
# 使用nginx反向代理（可选）
# 创建nginx配置文件nginx.conf
upstream wake_on_lan {
    server localhost:8000;
}

server {
    listen 80;
    server_name wake-on-lan.local;
    
    location / {
        proxy_pass http://wake_on_lan;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔄 更新和维护

### 镜像更新

```bash
# 1. 拉取最新镜像
docker pull kkape/wake-on-lan-service:latest

# 2. 停止当前容器
docker stop wake-on-lan-service

# 3. 备份当前容器（可选）
docker commit wake-on-lan-service wake-on-lan-backup

# 4. 删除旧容器
docker rm wake-on-lan-service

# 5. 启动新容器
docker run -d --name wake-on-lan-service --network host kkape/wake-on-lan-service:latest
```

### 数据备份

由于这是无状态服务，无需特殊备份。如需保存配置，可以：

```bash
# 导出容器配置
docker inspect wake-on-lan-service > wake-on-lan-config.json

# 保存镜像
docker save kkape/wake-on-lan-service:latest > wake-on-lan-image.tar
```

---

## 📞 支持

如有问题，请：
1. 查看容器日志：`docker logs wake-on-lan-service`
2. 运行测试脚本：`python test_service.py`
3. 检查网络配置和防火墙设置
4. 确认目标设备WOL配置

**项目地址**: https://github.com/kkape/wake-on-lan-service  
**Docker Hub**: https://hub.docker.com/r/kkape/wake-on-lan-service
