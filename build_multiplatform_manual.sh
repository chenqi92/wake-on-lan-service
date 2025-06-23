#!/bin/bash

# Manual Multi-Platform Docker Build Script
# This script builds images for different platforms and creates a manifest
# Author: kkape

set -e

# Configuration
DOCKER_USERNAME="kkape"
IMAGE_NAME="wake-on-lan-service"
VERSION="1.0.1"
LATEST_TAG="latest"

# Full image name
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}"

echo "=========================================="
echo "Manual Multi-Platform Docker Build"
echo "=========================================="
echo "Username: ${DOCKER_USERNAME}"
echo "Image: ${IMAGE_NAME}"
echo "Version: ${VERSION}"
echo "Platforms: linux/amd64, linux/arm64"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running"
    exit 1
fi

# Enable experimental features for manifest
export DOCKER_CLI_EXPERIMENTAL=enabled

# Login to Docker Hub
echo "Logging in to Docker Hub..."
docker login

# Build AMD64 image
echo ""
echo "Building AMD64 image..."
docker build --platform linux/amd64 -t "${FULL_IMAGE_NAME}:${VERSION}-amd64" .
docker build --platform linux/amd64 -t "${FULL_IMAGE_NAME}:${LATEST_TAG}-amd64" .

# Note: ARM64 build requires emulation or ARM64 machine
echo ""
echo "Building ARM64 image (requires emulation)..."
echo "This may take longer due to emulation..."

# Try to build ARM64 image with emulation
if docker build --platform linux/arm64 -t "${FULL_IMAGE_NAME}:${VERSION}-arm64" .; then
    echo "ARM64 build successful"
    docker build --platform linux/arm64 -t "${FULL_IMAGE_NAME}:${LATEST_TAG}-arm64" .
    ARM64_AVAILABLE=true
else
    echo "ARM64 build failed - continuing with AMD64 only"
    ARM64_AVAILABLE=false
fi

# Push individual platform images
echo ""
echo "Pushing platform-specific images..."
docker push "${FULL_IMAGE_NAME}:${VERSION}-amd64"
docker push "${FULL_IMAGE_NAME}:${LATEST_TAG}-amd64"

if [ "$ARM64_AVAILABLE" = true ]; then
    docker push "${FULL_IMAGE_NAME}:${VERSION}-arm64"
    docker push "${FULL_IMAGE_NAME}:${LATEST_TAG}-arm64"
fi

# Create and push manifest for version tag
echo ""
echo "Creating manifest for version ${VERSION}..."
if [ "$ARM64_AVAILABLE" = true ]; then
    docker manifest create "${FULL_IMAGE_NAME}:${VERSION}" \
        "${FULL_IMAGE_NAME}:${VERSION}-amd64" \
        "${FULL_IMAGE_NAME}:${VERSION}-arm64"
    
    docker manifest annotate "${FULL_IMAGE_NAME}:${VERSION}" \
        "${FULL_IMAGE_NAME}:${VERSION}-amd64" --arch amd64
    
    docker manifest annotate "${FULL_IMAGE_NAME}:${VERSION}" \
        "${FULL_IMAGE_NAME}:${VERSION}-arm64" --arch arm64
else
    docker manifest create "${FULL_IMAGE_NAME}:${VERSION}" \
        "${FULL_IMAGE_NAME}:${VERSION}-amd64"
    
    docker manifest annotate "${FULL_IMAGE_NAME}:${VERSION}" \
        "${FULL_IMAGE_NAME}:${VERSION}-amd64" --arch amd64
fi

docker manifest push "${FULL_IMAGE_NAME}:${VERSION}"

# Create and push manifest for latest tag
echo ""
echo "Creating manifest for latest tag..."
if [ "$ARM64_AVAILABLE" = true ]; then
    docker manifest create "${FULL_IMAGE_NAME}:${LATEST_TAG}" \
        "${FULL_IMAGE_NAME}:${LATEST_TAG}-amd64" \
        "${FULL_IMAGE_NAME}:${LATEST_TAG}-arm64"
    
    docker manifest annotate "${FULL_IMAGE_NAME}:${LATEST_TAG}" \
        "${FULL_IMAGE_NAME}:${LATEST_TAG}-amd64" --arch amd64
    
    docker manifest annotate "${FULL_IMAGE_NAME}:${LATEST_TAG}" \
        "${FULL_IMAGE_NAME}:${LATEST_TAG}-arm64" --arch arm64
else
    docker manifest create "${FULL_IMAGE_NAME}:${LATEST_TAG}" \
        "${FULL_IMAGE_NAME}:${LATEST_TAG}-amd64"
    
    docker manifest annotate "${FULL_IMAGE_NAME}:${LATEST_TAG}" \
        "${FULL_IMAGE_NAME}:${LATEST_TAG}-amd64" --arch amd64
fi

docker manifest push "${FULL_IMAGE_NAME}:${LATEST_TAG}"

echo ""
echo "=========================================="
echo "Multi-platform build completed!"
echo "=========================================="
echo ""
echo "Verify multi-platform support:"
echo "  docker manifest inspect ${FULL_IMAGE_NAME}:${VERSION}"
echo "  docker manifest inspect ${FULL_IMAGE_NAME}:${LATEST_TAG}"
echo ""
echo "Test on different platforms:"
echo "  # On AMD64:"
echo "  docker run --rm ${FULL_IMAGE_NAME}:${VERSION} python -c \"import platform; print(f'Architecture: {platform.machine()}')\""
echo "  # On ARM64:"
echo "  docker run --rm ${FULL_IMAGE_NAME}:${VERSION} python -c \"import platform; print(f'Architecture: {platform.machine()}')\""
echo ""
if [ "$ARM64_AVAILABLE" = true ]; then
    echo "✅ Multi-platform images (AMD64 + ARM64) created successfully!"
else
    echo "⚠️  Only AMD64 image created (ARM64 build failed)"
    echo "   For full multi-platform support, use GitHub Actions or an ARM64 machine"
fi
echo "=========================================="
