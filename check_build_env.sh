#!/bin/bash

# 构建环境检查脚本
# 作者: kkape

set -e

echo "=========================================="
echo "Docker 多平台构建环境检查"
echo "=========================================="

# 检查Docker是否运行
echo "🔍 检查Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行或无法访问"
    echo "请启动Docker Desktop或Docker服务"
    exit 1
fi
echo "✅ Docker 运行正常"

# 检查Docker版本
DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
echo "   版本: ${DOCKER_VERSION}"

# 检查Docker Buildx
echo ""
echo "🔍 检查Docker Buildx..."
if ! docker buildx version > /dev/null 2>&1; then
    echo "❌ Docker Buildx 不可用"
    echo "请安装Docker Buildx: https://docs.docker.com/buildx/working-with-buildx/"
    exit 1
fi
BUILDX_VERSION=$(docker buildx version | head -n1 | cut -d' ' -f2)
echo "✅ Docker Buildx 可用"
echo "   版本: ${BUILDX_VERSION}"

# 检查当前构建器
echo ""
echo "🔍 检查构建器..."
CURRENT_BUILDER=$(docker buildx ls | grep '*' | awk '{print $1}' | sed 's/\*//')
echo "   当前构建器: ${CURRENT_BUILDER}"

# 检查构建器支持的平台
echo ""
echo "🔍 检查支持的平台..."
PLATFORMS=$(docker buildx inspect --bootstrap 2>/dev/null | grep "Platforms:" | cut -d':' -f2 | tr -d ' ')
echo "   支持的平台: ${PLATFORMS}"

# 检查是否支持目标平台
if [[ $PLATFORMS == *"linux/amd64"* ]] && [[ $PLATFORMS == *"linux/arm64"* ]]; then
    echo "✅ 支持目标平台 (linux/amd64, linux/arm64)"
else
    echo "⚠️  当前构建器可能不支持所有目标平台"
    echo "   建议创建新的多平台构建器"
fi

# 检查Docker Hub登录状态
echo ""
echo "🔍 检查Docker Hub登录状态..."
if docker info 2>/dev/null | grep -q "Username:"; then
    USERNAME=$(docker info 2>/dev/null | grep "Username:" | awk '{print $2}')
    echo "✅ 已登录Docker Hub"
    echo "   用户名: ${USERNAME}"
else
    echo "⚠️  未登录Docker Hub"
    echo "   构建时需要登录才能推送镜像"
fi

# 检查网络连接
echo ""
echo "🔍 检查网络连接..."
if ping -c 1 registry-1.docker.io > /dev/null 2>&1; then
    echo "✅ Docker Hub 网络连接正常"
else
    echo "⚠️  无法连接到Docker Hub"
    echo "   请检查网络连接"
fi

echo ""
echo "=========================================="
echo "环境检查完成!"
echo "=========================================="
echo ""
echo "如果所有检查都通过，可以运行构建脚本:"
echo "  ./build_and_push.sh"
echo ""
echo "如果需要设置多平台构建器:"
echo "  docker buildx create --name multiarch-builder --use --bootstrap"
echo ""
echo "如果需要登录Docker Hub:"
echo "  docker login"
