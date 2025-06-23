@echo off
REM Wake-on-LAN Service Docker Build and Push Script (Legacy - Windows)
REM For systems without Docker Buildx
REM Author: kkape

setlocal enabledelayedexpansion

REM Configuration variables
set DOCKER_USERNAME=kkape
set IMAGE_NAME=wake-on-lan-service
set VERSION=1.0.1
set LATEST_TAG=latest

REM Full image name
set FULL_IMAGE_NAME=%DOCKER_USERNAME%/%IMAGE_NAME%

echo ==========================================
echo Wake-on-LAN Service Docker Build and Push (Legacy)
echo ==========================================
echo Username: %DOCKER_USERNAME%
echo Image: %IMAGE_NAME%
echo Version: %VERSION%
echo Note: This script builds for current platform only
echo ==========================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or accessible
    echo Please start Docker Desktop or Docker service
    pause
    exit /b 1
)

echo OK: Docker is running
docker --version

REM Build images
echo.
echo Building Docker images...
docker build -t "%FULL_IMAGE_NAME%:%VERSION%" .
if errorlevel 1 (
    echo ERROR: Failed to build image with version tag
    pause
    exit /b 1
)

docker build -t "%FULL_IMAGE_NAME%:%LATEST_TAG%" .
if errorlevel 1 (
    echo ERROR: Failed to build image with latest tag
    pause
    exit /b 1
)

echo Images built successfully!

REM Show image information
echo.
echo Image information:
docker images | findstr "%FULL_IMAGE_NAME%"

REM Ask if user wants to push to Docker Hub
echo.
set /p PUSH_CHOICE="Do you want to push images to Docker Hub? (y/N): "
if /i "%PUSH_CHOICE%"=="y" (
    echo.
    echo Logging in to Docker Hub...
    docker login
    if errorlevel 1 (
        echo ERROR: Docker Hub login failed
        pause
        exit /b 1
    )
    
    echo.
    echo Pushing images...
    docker push "%FULL_IMAGE_NAME%:%VERSION%"
    if errorlevel 1 (
        echo ERROR: Failed to push version tag
        pause
        exit /b 1
    )
    
    docker push "%FULL_IMAGE_NAME%:%LATEST_TAG%"
    if errorlevel 1 (
        echo ERROR: Failed to push latest tag
        pause
        exit /b 1
    )
    
    echo.
    echo Images pushed successfully!
    echo.
    echo Image addresses:
    echo   - %FULL_IMAGE_NAME%:%VERSION%
    echo   - %FULL_IMAGE_NAME%:%LATEST_TAG%
    echo.
    echo Note: These images are built for the current platform only.
    echo For multi-platform support, please install Docker Buildx.
    
) else (
    echo Skipping push step
    echo.
    echo To push later, run:
    echo   docker push %FULL_IMAGE_NAME%:%VERSION%
    echo   docker push %FULL_IMAGE_NAME%:%LATEST_TAG%
)

echo.
echo ==========================================
echo Build script completed!
echo ==========================================
echo.
echo Local run commands:
echo   docker run -d --name wake-on-lan --network host %FULL_IMAGE_NAME%:%LATEST_TAG%
echo.
echo Using docker-compose:
echo   docker-compose up -d
echo.
echo Access service:
echo   http://localhost:8000
echo   http://localhost:8000/docs (API documentation)
echo.
echo To install Docker Buildx for multi-platform builds:
echo   https://docs.docker.com/buildx/working-with-buildx/
echo ==========================================

pause
