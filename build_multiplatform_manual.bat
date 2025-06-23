@echo off
REM Manual Multi-Platform Docker Build Script (Windows)
REM This script builds images for different platforms and creates a manifest
REM Author: kkape

setlocal enabledelayedexpansion

REM Configuration
set DOCKER_USERNAME=kkape
set IMAGE_NAME=wake-on-lan-service
set VERSION=1.0.1
set LATEST_TAG=latest

REM Full image name
set FULL_IMAGE_NAME=%DOCKER_USERNAME%/%IMAGE_NAME%

echo ==========================================
echo Manual Multi-Platform Docker Build
echo ==========================================
echo Username: %DOCKER_USERNAME%
echo Image: %IMAGE_NAME%
echo Version: %VERSION%
echo Platforms: linux/amd64, linux/arm64
echo ==========================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running
    pause
    exit /b 1
)

REM Enable experimental features for manifest
set DOCKER_CLI_EXPERIMENTAL=enabled

REM Login to Docker Hub
echo.
echo Logging in to Docker Hub...
docker login
if errorlevel 1 (
    echo ERROR: Docker Hub login failed
    pause
    exit /b 1
)

REM Build AMD64 image
echo.
echo Building AMD64 image...
docker build --platform linux/amd64 -t "%FULL_IMAGE_NAME%:%VERSION%-amd64" .
if errorlevel 1 (
    echo ERROR: AMD64 build failed
    pause
    exit /b 1
)

docker build --platform linux/amd64 -t "%FULL_IMAGE_NAME%:%LATEST_TAG%-amd64" .
if errorlevel 1 (
    echo ERROR: AMD64 latest build failed
    pause
    exit /b 1
)

REM Try to build ARM64 image with emulation
echo.
echo Building ARM64 image (requires emulation)...
echo This may take longer due to emulation...

docker build --platform linux/arm64 -t "%FULL_IMAGE_NAME%:%VERSION%-arm64" .
if errorlevel 1 (
    echo ARM64 build failed - continuing with AMD64 only
    set ARM64_AVAILABLE=false
) else (
    echo ARM64 build successful
    docker build --platform linux/arm64 -t "%FULL_IMAGE_NAME%:%LATEST_TAG%-arm64" .
    if errorlevel 1 (
        echo ARM64 latest build failed
        set ARM64_AVAILABLE=false
    ) else (
        set ARM64_AVAILABLE=true
    )
)

REM Push individual platform images
echo.
echo Pushing platform-specific images...
docker push "%FULL_IMAGE_NAME%:%VERSION%-amd64"
if errorlevel 1 (
    echo ERROR: Failed to push AMD64 version image
    pause
    exit /b 1
)

docker push "%FULL_IMAGE_NAME%:%LATEST_TAG%-amd64"
if errorlevel 1 (
    echo ERROR: Failed to push AMD64 latest image
    pause
    exit /b 1
)

if "%ARM64_AVAILABLE%"=="true" (
    docker push "%FULL_IMAGE_NAME%:%VERSION%-arm64"
    if errorlevel 1 (
        echo ERROR: Failed to push ARM64 version image
        pause
        exit /b 1
    )
    
    docker push "%FULL_IMAGE_NAME%:%LATEST_TAG%-arm64"
    if errorlevel 1 (
        echo ERROR: Failed to push ARM64 latest image
        pause
        exit /b 1
    )
)

REM Create and push manifest for version tag
echo.
echo Creating manifest for version %VERSION%...
if "%ARM64_AVAILABLE%"=="true" (
    docker manifest create "%FULL_IMAGE_NAME%:%VERSION%" ^
        "%FULL_IMAGE_NAME%:%VERSION%-amd64" ^
        "%FULL_IMAGE_NAME%:%VERSION%-arm64"
    
    docker manifest annotate "%FULL_IMAGE_NAME%:%VERSION%" ^
        "%FULL_IMAGE_NAME%:%VERSION%-amd64" --arch amd64
    
    docker manifest annotate "%FULL_IMAGE_NAME%:%VERSION%" ^
        "%FULL_IMAGE_NAME%:%VERSION%-arm64" --arch arm64
) else (
    docker manifest create "%FULL_IMAGE_NAME%:%VERSION%" ^
        "%FULL_IMAGE_NAME%:%VERSION%-amd64"
    
    docker manifest annotate "%FULL_IMAGE_NAME%:%VERSION%" ^
        "%FULL_IMAGE_NAME%:%VERSION%-amd64" --arch amd64
)

docker manifest push "%FULL_IMAGE_NAME%:%VERSION%"
if errorlevel 1 (
    echo ERROR: Failed to push version manifest
    pause
    exit /b 1
)

REM Create and push manifest for latest tag
echo.
echo Creating manifest for latest tag...
if "%ARM64_AVAILABLE%"=="true" (
    docker manifest create "%FULL_IMAGE_NAME%:%LATEST_TAG%" ^
        "%FULL_IMAGE_NAME%:%LATEST_TAG%-amd64" ^
        "%FULL_IMAGE_NAME%:%LATEST_TAG%-arm64"
    
    docker manifest annotate "%FULL_IMAGE_NAME%:%LATEST_TAG%" ^
        "%FULL_IMAGE_NAME%:%LATEST_TAG%-amd64" --arch amd64
    
    docker manifest annotate "%FULL_IMAGE_NAME%:%LATEST_TAG%" ^
        "%FULL_IMAGE_NAME%:%LATEST_TAG%-arm64" --arch arm64
) else (
    docker manifest create "%FULL_IMAGE_NAME%:%LATEST_TAG%" ^
        "%FULL_IMAGE_NAME%:%LATEST_TAG%-amd64"
    
    docker manifest annotate "%FULL_IMAGE_NAME%:%LATEST_TAG%" ^
        "%FULL_IMAGE_NAME%:%LATEST_TAG%-amd64" --arch amd64
)

docker manifest push "%FULL_IMAGE_NAME%:%LATEST_TAG%"
if errorlevel 1 (
    echo ERROR: Failed to push latest manifest
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Multi-platform build completed!
echo ==========================================
echo.
echo Verify multi-platform support:
echo   docker manifest inspect %FULL_IMAGE_NAME%:%VERSION%
echo   docker manifest inspect %FULL_IMAGE_NAME%:%LATEST_TAG%
echo.
echo Test on different platforms:
echo   # On AMD64:
echo   docker run --rm %FULL_IMAGE_NAME%:%VERSION% python -c "import platform; print(f'Architecture: {platform.machine()}')"
echo   # On ARM64:
echo   docker run --rm %FULL_IMAGE_NAME%:%VERSION% python -c "import platform; print(f'Architecture: {platform.machine()}')"
echo.
if "%ARM64_AVAILABLE%"=="true" (
    echo ✅ Multi-platform images (AMD64 + ARM64) created successfully!
) else (
    echo ⚠️  Only AMD64 image created (ARM64 build failed)
    echo    For full multi-platform support, use GitHub Actions or an ARM64 machine
)
echo ==========================================

pause
