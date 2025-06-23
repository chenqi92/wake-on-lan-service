@echo off
REM 多平台镜像验证脚本 (Windows)
REM 作者: kkape

setlocal enabledelayedexpansion

set DOCKER_USERNAME=kkape
set IMAGE_NAME=wake-on-lan-service
set LATEST_TAG=latest
set FULL_IMAGE_NAME=%DOCKER_USERNAME%/%IMAGE_NAME%

echo ==========================================
echo 多平台镜像验证
echo ==========================================

REM 检查Docker Buildx是否可用
docker buildx version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker Buildx 不可用
    pause
    exit /b 1
)

echo 正在验证多平台镜像: %FULL_IMAGE_NAME%:%LATEST_TAG%
echo.

REM 检查镜像的多平台支持
echo 📋 镜像平台信息:
docker buildx imagetools inspect "%FULL_IMAGE_NAME%:%LATEST_TAG%"

echo.
echo ✅ 验证完成!
echo.
echo 使用方法:
echo   # 在 AMD64 系统上:
echo   docker run --rm %FULL_IMAGE_NAME%:%LATEST_TAG% python -c "import platform; print(f'架构: {platform.machine()}')"
echo.
echo   # 在 ARM64 系统上:
echo   docker run --rm %FULL_IMAGE_NAME%:%LATEST_TAG% python -c "import platform; print(f'架构: {platform.machine()}')"
echo.
echo Docker 会自动选择适合当前平台的镜像版本。

pause
