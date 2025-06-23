# GitHub Actions 多平台构建设置指南

## 🎯 概述

本项目包含GitHub Actions工作流，可以自动构建支持AMD64和ARM64架构的Docker镜像。当代码推送到master/main分支时，会自动触发构建和推送到Docker Hub。

## 🔧 设置步骤

### 1. 配置GitHub Secrets

在GitHub仓库中设置以下secrets：

1. 进入GitHub仓库页面
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret` 添加以下secrets：

#### 必需的Secrets

| Secret名称 | 描述 | 示例值 |
|-----------|------|--------|
| `DOCKER_USERNAME` | Docker Hub用户名 | `kkape` |
| `DOCKER_PASSWORD` | Docker Hub访问令牌 | `dckr_pat_xxxxx` |

#### 获取Docker Hub访问令牌

1. 登录 [Docker Hub](https://hub.docker.com/)
2. 点击右上角头像 → `Account Settings`
3. 选择 `Security` → `New Access Token`
4. 输入令牌名称（如：`github-actions`）
5. 选择权限：`Read, Write, Delete`
6. 点击 `Generate` 并复制生成的令牌
7. 将令牌作为 `DOCKER_PASSWORD` 添加到GitHub Secrets

### 2. 工作流触发条件

工作流会在以下情况自动触发：

- **推送到master/main分支**：自动构建并推送镜像
- **创建标签**：构建带版本号的镜像
- **Pull Request**：仅构建，不推送
- **手动触发**：在Actions页面手动运行

### 3. 构建的镜像标签

工作流会创建以下镜像标签：

- `kkape/wake-on-lan-service:latest` - 最新版本
- `kkape/wake-on-lan-service:1.0.1` - 当前版本
- `kkape/wake-on-lan-service:master` - master分支版本

## 🚀 手动触发构建

### 方法一：通过GitHub界面

1. 进入GitHub仓库
2. 点击 `Actions` 标签
3. 选择 `Build and Push Multi-Platform Docker Images` 工作流
4. 点击 `Run workflow`
5. 选择分支并可选择指定版本标签
6. 点击 `Run workflow` 开始构建

### 方法二：通过Git标签

```bash
# 创建并推送标签
git tag v1.0.1
git push origin v1.0.1

# 这会触发构建并创建版本化的镜像
```

## 📊 构建状态

### 查看构建进度

1. 进入GitHub仓库的 `Actions` 页面
2. 查看最新的工作流运行状态
3. 点击具体的运行查看详细日志

### 构建时间

- **AMD64架构**：约5-8分钟
- **ARM64架构**：约8-12分钟（需要模拟）
- **总构建时间**：约10-15分钟

## 🔍 验证多平台镜像

构建完成后，可以验证镜像是否支持多平台：

```bash
# 检查镜像支持的平台
docker manifest inspect kkape/wake-on-lan-service:latest

# 在不同平台测试
# AMD64系统
docker run --rm kkape/wake-on-lan-service:latest python -c "import platform; print(f'Architecture: {platform.machine()}')"

# ARM64系统（如Apple M1/M2）
docker run --rm kkape/wake-on-lan-service:latest python -c "import platform; print(f'Architecture: {platform.machine()}')"
```

## 🛠️ 故障排除

### 常见问题

1. **构建失败：认证错误**
   - 检查 `DOCKER_USERNAME` 和 `DOCKER_PASSWORD` secrets是否正确设置
   - 确认Docker Hub访问令牌有效且权限足够

2. **ARM64构建超时**
   - ARM64构建需要模拟，时间较长是正常的
   - 如果超时，可以在工作流中增加timeout设置

3. **推送失败**
   - 检查Docker Hub仓库是否存在
   - 确认用户有推送权限

### 调试步骤

1. **查看构建日志**
   ```
   GitHub → Actions → 选择失败的运行 → 查看详细日志
   ```

2. **本地测试**
   ```bash
   # 使用本地多平台构建脚本测试
   ./build_multiplatform_manual.sh  # Linux/Mac
   build_multiplatform_manual.bat   # Windows
   ```

3. **验证Dockerfile**
   ```bash
   # 本地构建测试
   docker build --platform linux/amd64 -t test-amd64 .
   docker build --platform linux/arm64 -t test-arm64 .
   ```

## 📈 优化建议

### 加速构建

1. **使用构建缓存**
   - 工作流已配置GitHub Actions缓存
   - 后续构建会复用缓存层

2. **并行构建**
   - 工作流使用Docker Buildx并行构建多平台

3. **优化Dockerfile**
   - 将不常变化的层放在前面
   - 使用多阶段构建减少镜像大小

### 安全最佳实践

1. **定期更新访问令牌**
   - 建议每6个月更新一次Docker Hub令牌

2. **最小权限原则**
   - 只给予必要的Docker Hub权限

3. **监控构建**
   - 设置GitHub通知监控构建状态

## 🔄 更新工作流

如需修改构建配置，编辑 `.github/workflows/docker-build.yml` 文件：

```yaml
# 修改支持的平台
platforms: linux/amd64,linux/arm64,linux/arm/v7

# 修改镜像标签策略
tags: |
  type=ref,event=branch
  type=ref,event=pr
  type=semver,pattern={{version}}
  type=raw,value=latest,enable={{is_default_branch}}

# 修改构建超时
timeout-minutes: 60
```

---

## 📞 支持

如有问题：

1. 查看GitHub Actions运行日志
2. 检查Docker Hub仓库状态
3. 验证secrets配置
4. 参考本文档的故障排除部分

**GitHub仓库**: https://github.com/chenqi92/wake-on-lan-service  
**Docker Hub**: https://hub.docker.com/r/kkape/wake-on-lan-service
