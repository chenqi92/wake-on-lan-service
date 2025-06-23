@echo off
REM Build Environment Check Script (Windows)
REM Author: kkape

setlocal enabledelayedexpansion

echo ==========================================
echo Docker Multi-Platform Build Environment Check
echo ==========================================

REM Check if Docker is running
echo Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or accessible
    echo Please start Docker Desktop or Docker service
    pause
    exit /b 1
)
echo OK: Docker is running

REM Check Docker version
docker --version

REM Check Docker Buildx
echo.
echo Checking Docker Buildx...
docker buildx version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Buildx is not available
    echo Please install Docker Buildx: https://docs.docker.com/buildx/working-with-buildx/
    pause
    exit /b 1
)
echo OK: Docker Buildx is available
docker buildx version

REM Check current builder
echo.
echo Checking builder...
docker buildx ls

REM Check builder supported platforms
echo.
echo Checking supported platforms...
docker buildx inspect --bootstrap
echo.
echo Checking if target platforms are supported...
docker buildx inspect | findstr "linux/amd64" >nul
if errorlevel 1 (
    echo WARNING: linux/amd64 platform not supported
) else (
    echo OK: linux/amd64 platform supported
)

docker buildx inspect | findstr "linux/arm64" >nul
if errorlevel 1 (
    echo WARNING: linux/arm64 platform not supported
) else (
    echo OK: linux/arm64 platform supported
)

REM Check Docker Hub login status
echo.
echo Checking Docker Hub login status...
docker info | findstr "Username:" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Not logged in to Docker Hub
    echo You need to login to push images
) else (
    echo OK: Logged in to Docker Hub
    docker info | findstr "Username:"
)

REM Check network connection
echo.
echo Checking network connection...
ping -n 1 registry-1.docker.io >nul 2>&1
if errorlevel 1 (
    echo WARNING: Cannot connect to Docker Hub
    echo Please check network connection
) else (
    echo OK: Docker Hub network connection is working
)

echo.
echo ==========================================
echo Environment check completed!
echo ==========================================
echo.
echo If all checks pass, you can run the build script:
echo   build_and_push.bat
echo.
echo If you need to setup multi-platform builder:
echo   docker buildx create --name multiarch-builder --use --bootstrap
echo.
echo If you need to login to Docker Hub:
echo   docker login

pause
