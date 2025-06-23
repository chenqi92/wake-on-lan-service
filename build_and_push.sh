#!/bin/bash

# Wake-on-LAN Service Docker 多平台构建和推送脚本
# 支持 AMD64 和 ARM64 平台
# 作者: kkape

set -e

# 配置变量
DOCKER_USERNAME="kkape"
IMAGE_NAME="wake-on-lan-service"
VERSION="1.0.1"
LATEST_TAG="latest"
PLATFORMS="linux/amd64,linux/arm64"

# 完整镜像名称
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}"

echo "=========================================="
echo "Wake-on-LAN Service Docker 多平台构建和推送"
echo "=========================================="
echo "用户名: ${DOCKER_USERNAME}"
echo "镜像名: ${IMAGE_NAME}"
echo "版本: ${VERSION}"
echo "支持平台: ${PLATFORMS}"
echo "=========================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行或无法访问"
    exit 1
fi

# 检查Docker Buildx是否可用
echo "检查Docker Buildx..."
if ! docker buildx version > /dev/null 2>&1; then
    echo "错误: Docker Buildx 不可用，请安装或启用 Docker Buildx"
    echo "安装指南: https://docs.docker.com/buildx/working-with-buildx/"
    exit 1
fi

# 创建并使用多平台构建器
echo "设置多平台构建器..."
if ! docker buildx create --name multiarch-builder --use --bootstrap > /dev/null 2>&1; then
    echo "使用现有构建器..."
    if ! docker buildx use multiarch-builder > /dev/null 2>&1; then
        echo "警告: 无法设置专用构建器，使用默认构建器"
        docker buildx use default > /dev/null 2>&1 || true
    fi
fi

# 检查构建器支持的平台
echo "检查构建器支持的平台..."
docker buildx inspect --bootstrap > /dev/null 2>&1

# 询问是否推送到Docker Hub
read -p "是否要构建并推送多平台镜像到Docker Hub? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在登录Docker Hub..."
    if ! docker login; then
        echo "错误: Docker Hub 登录失败"
        exit 1
    fi

    echo ""
    echo "正在构建并推送多平台镜像..."
    echo "这可能需要几分钟时间，请耐心等待..."
    echo ""

    # 构建并推送多平台镜像
    if ! docker buildx build --platform "${PLATFORMS}" \
        -t "${FULL_IMAGE_NAME}:${VERSION}" \
        -t "${FULL_IMAGE_NAME}:${LATEST_TAG}" \
        --push .; then
        echo "错误: 多平台镜像构建或推送失败"
        exit 1
    fi

    echo ""
    echo "🎉 多平台镜像推送完成!"
    echo ""
    echo "镜像地址:"
    echo "  - ${FULL_IMAGE_NAME}:${VERSION}"
    echo "  - ${FULL_IMAGE_NAME}:${LATEST_TAG}"
    echo ""
    echo "支持的平台:"
    echo "  - linux/amd64 (Intel/AMD 64位)"
    echo "  - linux/arm64 (ARM 64位, 如 Apple M1/M2, Raspberry Pi 4)"
    echo ""
    echo "验证多平台镜像:"
    echo "  docker buildx imagetools inspect ${FULL_IMAGE_NAME}:${LATEST_TAG}"

else
    echo "跳过推送步骤"
    echo ""
    echo "如需本地构建测试镜像，请运行:"
    echo "  docker buildx build --platform linux/amd64 -t ${FULL_IMAGE_NAME}:local-test --load ."
fi

echo "=========================================="
echo "构建脚本执行完成!"
echo "=========================================="
echo ""
echo "本地运行命令:"
echo "  docker run -d --name wake-on-lan --network host ${FULL_IMAGE_NAME}:${LATEST_TAG}"
echo ""
echo "使用docker-compose运行:"
echo "  docker-compose up -d"
echo ""
echo "访问服务:"
echo "  http://localhost:8000"
echo "  http://localhost:8000/docs (API文档)"
echo ""
echo "清理构建器 (可选):"
echo "  docker buildx rm multiarch-builder"
echo "=========================================="
