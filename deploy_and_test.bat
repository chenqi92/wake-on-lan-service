@echo off
REM Wake-on-LAN Service Deployment and Test Script
REM Author: kkape

setlocal enabledelayedexpansion

set IMAGE_NAME=kkape/wake-on-lan-service:latest
set CONTAINER_NAME=wake-on-lan-service
set SERVICE_PORT=12345

echo ==========================================
echo Wake-on-LAN Service Deployment and Test
echo ==========================================
echo Image: %IMAGE_NAME%
echo Container: %CONTAINER_NAME%
echo Port: %SERVICE_PORT%
echo ==========================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running
    pause
    exit /b 1
)

REM Stop and remove existing container if it exists
echo Cleaning up existing container...
docker stop %CONTAINER_NAME% >nul 2>&1
docker rm %CONTAINER_NAME% >nul 2>&1

REM Pull latest image
echo Pulling latest image from Docker Hub...
docker pull %IMAGE_NAME%
if errorlevel 1 (
    echo ERROR: Failed to pull image
    pause
    exit /b 1
)

REM Run the container
echo Starting container...
docker run -d --name %CONTAINER_NAME% --network host %IMAGE_NAME%
if errorlevel 1 (
    echo ERROR: Failed to start container
    pause
    exit /b 1
)

REM Wait for service to start
echo Waiting for service to start...
timeout /t 10 /nobreak >nul

REM Check container status
echo Checking container status...
docker ps | findstr %CONTAINER_NAME%
if errorlevel 1 (
    echo ERROR: Container is not running
    echo Container logs:
    docker logs %CONTAINER_NAME%
    pause
    exit /b 1
)

REM Test health endpoint
echo Testing health endpoint...
powershell -Command "try { $response = Invoke-RestMethod http://localhost:%SERVICE_PORT%/health; Write-Host 'Health check passed:'; Write-Host ($response | ConvertTo-Json) } catch { Write-Host 'Health check failed:' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo ERROR: Health check failed
    echo Container logs:
    docker logs %CONTAINER_NAME%
    pause
    exit /b 1
)

REM Test interfaces endpoint
echo Testing interfaces endpoint...
powershell -Command "try { $response = Invoke-RestMethod http://localhost:%SERVICE_PORT%/interfaces; Write-Host 'Interfaces check passed:'; Write-Host 'Found' $response.count 'network interfaces' } catch { Write-Host 'Interfaces check failed:' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo ERROR: Interfaces check failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Deployment and Test Successful!
echo ==========================================
echo.
echo Service is running at:
echo   http://localhost:%SERVICE_PORT%
echo   http://localhost:%SERVICE_PORT%/docs (API Documentation)
echo.
echo Container management:
echo   Stop:    docker stop %CONTAINER_NAME%
echo   Start:   docker start %CONTAINER_NAME%
echo   Logs:    docker logs %CONTAINER_NAME%
echo   Remove:  docker rm %CONTAINER_NAME%
echo.
echo Test the service:
echo   python test_service.py
echo   python example_usage.py
echo ==========================================

pause
