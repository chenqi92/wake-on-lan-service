# Wake-on-LAN 服务部署指南

## 🚀 快速部署

### 1. 环境准备

确保系统已安装：
- Docker
- Docker Compose

### 2. 配置环境变量

创建 `.env` 文件：
```bash
# 基础配置
HOST=0.0.0.0
PORT=12345

# 认证配置（请修改为安全的值）
WOL_USERNAME=your_username
WOL_PASSWORD=your_secure_password
WOL_SESSION_SECRET=your-very-long-and-random-secret-key-here
```

### 3. 启动服务

```bash
# 使用 docker-compose
docker-compose up -d

# 或者直接使用 Docker
docker run -d \
  --name wake-on-lan \
  --network host \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  -e WOL_USERNAME=your_username \
  -e WOL_PASSWORD=your_secure_password \
  -e WOL_SESSION_SECRET=your-secret-key \
  kkape/wake-on-lan-service:latest
```

### 4. 验证部署

```bash
# 运行测试脚本
python test_docker.py
python test_auth.py

# 或手动检查
curl http://localhost:12345/health
```

## 🔧 生产环境部署

### 1. 安全配置

#### 强化认证
```bash
# 生成安全的会话密钥
openssl rand -hex 32

# 设置复杂密码
WOL_USERNAME=admin_$(date +%s)
WOL_PASSWORD=$(openssl rand -base64 16)
```

#### 网络安全
```bash
# 使用防火墙限制访问
sudo ufw allow from 192.168.1.0/24 to any port 12345
sudo ufw deny 12345
```

### 2. 反向代理配置

#### Nginx 配置示例
```nginx
server {
    listen 443 ssl;
    server_name wol.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:12345;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Traefik 配置示例
```yaml
version: '3.8'
services:
  wake-on-lan:
    image: kkape/wake-on-lan-service:latest
    networks:
      - traefik
    environment:
      - WOL_USERNAME=${WOL_USERNAME}
      - WOL_PASSWORD=${WOL_PASSWORD}
      - WOL_SESSION_SECRET=${WOL_SESSION_SECRET}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.wol.rule=Host(`wol.yourdomain.com`)"
      - "traefik.http.routers.wol.tls=true"
      - "traefik.http.routers.wol.tls.certresolver=letsencrypt"
```

### 3. 监控和日志

#### 日志配置
```yaml
version: '3.8'
services:
  wake-on-lan:
    image: kkape/wake-on-lan-service:latest
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### 健康检查监控
```bash
# 创建监控脚本
cat > /usr/local/bin/wol-health-check.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:12345/health > /dev/null 2>&1; then
    echo "$(date): Wake-on-LAN service health check failed" >> /var/log/wol-monitor.log
    # 可以添加重启逻辑或告警
fi
EOF

chmod +x /usr/local/bin/wol-health-check.sh

# 添加到 crontab
echo "*/5 * * * * /usr/local/bin/wol-health-check.sh" | crontab -
```

## 🔄 升级和维护

### 1. 服务升级

```bash
# 拉取最新镜像
docker pull kkape/wake-on-lan-service:latest

# 停止现有服务
docker-compose down

# 启动新版本
docker-compose up -d

# 验证升级
python test_auth.py
```

### 2. 数据备份

```bash
# 备份配置文件
cp docker-compose.yml docker-compose.yml.backup
cp .env .env.backup

# 导出容器配置
docker inspect wake-on-lan-service > container-config.json
```

### 3. 故障恢复

```bash
# 快速重启
docker-compose restart

# 完全重建
docker-compose down
docker-compose up -d --force-recreate

# 查看日志
docker-compose logs -f
```

## 📊 性能优化

### 1. 资源限制

```yaml
version: '3.8'
services:
  wake-on-lan:
    image: kkape/wake-on-lan-service:latest
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
```

### 2. 缓存优化

```bash
# 设置更长的会话过期时间（减少登录频率）
WOL_SESSION_EXPIRE_HOURS=24
```

## 🛡️ 安全最佳实践

### 1. 定期安全检查

```bash
# 检查容器安全
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image kkape/wake-on-lan-service:latest

# 检查网络端口
nmap -sT -O localhost -p 12345
```

### 2. 访问日志分析

```bash
# 分析访问模式
docker logs wake-on-lan-service 2>&1 | grep "POST /api/login" | tail -20

# 检查异常访问
docker logs wake-on-lan-service 2>&1 | grep "401\|403\|429"
```

### 3. 定期密码更新

```bash
# 生成新密码
NEW_PASSWORD=$(openssl rand -base64 16)
echo "新密码: $NEW_PASSWORD"

# 更新环境变量并重启服务
sed -i "s/WOL_PASSWORD=.*/WOL_PASSWORD=$NEW_PASSWORD/" .env
docker-compose restart
```

## 📞 技术支持

### 问题报告
- GitHub Issues: https://github.com/chenqi92/wake-on-lan-service/issues
- 邮箱: contact@kkape.com

### 社区支持
- 文档: README.md
- 示例: example_usage.py
- 测试: test_*.py

---

**部署完成后，请务必：**
1. 修改默认密码
2. 配置防火墙
3. 启用HTTPS（生产环境）
4. 设置监控和备份
5. 定期更新镜像
