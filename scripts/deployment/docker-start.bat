@echo off
REM VisionAI-ClipsMaster Docker Management Script for Windows
REM Provides easy commands for Docker operations

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_NAME=visionai-clipsmaster
set COMPOSE_FILE=docker\docker-compose.root.yml
set COMPOSE_DEV_FILE=docker\docker-compose.dev.root.yml

REM Colors (Windows doesn't support colors in batch, but we'll use echo)
set "HEADER============================================="

:main
if "%1"=="" goto show_help
if "%1"=="setup" goto setup
if "%1"=="build" goto build
if "%1"=="build-dev" goto build_dev
if "%1"=="start" goto start
if "%1"=="start-dev" goto start_dev
if "%1"=="stop" goto stop
if "%1"=="stop-dev" goto stop_dev
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="logs-dev" goto logs_dev
if "%1"=="status" goto status
if "%1"=="clean" goto clean
if "%1"=="update" goto update
if "%1"=="backup" goto backup
if "%1"=="help" goto show_help
if "%1"=="-h" goto show_help
if "%1"=="--help" goto show_help

echo [ERROR] Unknown command: %1
goto show_help

:print_header
echo %HEADER%
echo   VisionAI-ClipsMaster Docker Manager
echo %HEADER%
goto :eof

:check_docker
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker first.
    exit /b 1
)
goto :eof

:check_docker_compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)
goto :eof

:create_directories
echo [INFO] Creating necessary directories...
if not exist "models" mkdir models
if not exist "data" mkdir data
if not exist "output" mkdir output
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache
if not exist "static" mkdir static
if not exist "docker\nginx\ssl" mkdir docker\nginx\ssl
echo [SUCCESS] Directories created
goto :eof

:setup_env
if not exist ".env" (
    echo [INFO] Creating .env file from template...
    copy .env.example .env >nul
    echo [WARNING] Please edit .env file with your configuration
) else (
    echo [INFO] .env file already exists
)
goto :eof

:setup
call :print_header
call :check_docker
call :check_docker_compose
call :create_directories
call :setup_env
echo [SUCCESS] Setup completed
goto :eof

:build
call :check_docker
call :check_docker_compose
echo [INFO] Building Docker images...
docker-compose -f %COMPOSE_FILE% build --no-cache
if errorlevel 1 (
    echo [ERROR] Failed to build images
    exit /b 1
)
echo [SUCCESS] Images built successfully
goto :eof

:build_dev
call :check_docker
call :check_docker_compose
echo [INFO] Building development Docker images...
docker-compose -f %COMPOSE_DEV_FILE% build --no-cache
if errorlevel 1 (
    echo [ERROR] Failed to build development images
    exit /b 1
)
echo [SUCCESS] Development images built successfully
goto :eof

:start
call :check_docker
call :check_docker_compose
echo [INFO] Starting VisionAI-ClipsMaster services...
docker-compose -f %COMPOSE_FILE% up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    exit /b 1
)
echo [SUCCESS] Services started successfully

echo [INFO] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo [INFO] Service URLs:
echo   - Main Application: http://localhost:8000
echo   - Web Interface: http://localhost:8080
echo   - API: http://localhost:5000
echo   - Nginx Proxy: http://localhost:80
goto :eof

:start_dev
call :check_docker
call :check_docker_compose
echo [INFO] Starting VisionAI-ClipsMaster development services...
docker-compose -f %COMPOSE_DEV_FILE% up -d
if errorlevel 1 (
    echo [ERROR] Failed to start development services
    exit /b 1
)
echo [SUCCESS] Development services started successfully

echo [INFO] Development URLs:
echo   - Main Application: http://localhost:8000
echo   - Jupyter Lab: http://localhost:8888
echo   - Jupyter Notebook: http://localhost:8889
goto :eof

:stop
call :check_docker
call :check_docker_compose
echo [INFO] Stopping VisionAI-ClipsMaster services...
docker-compose -f %COMPOSE_FILE% down
echo [SUCCESS] Services stopped successfully
goto :eof

:stop_dev
call :check_docker
call :check_docker_compose
echo [INFO] Stopping development services...
docker-compose -f %COMPOSE_DEV_FILE% down
echo [SUCCESS] Development services stopped successfully
goto :eof

:restart
call :check_docker
call :check_docker_compose
echo [INFO] Restarting VisionAI-ClipsMaster services...
docker-compose -f %COMPOSE_FILE% restart
echo [SUCCESS] Services restarted successfully
goto :eof

:logs
call :check_docker
call :check_docker_compose
docker-compose -f %COMPOSE_FILE% logs -f %2
goto :eof

:logs_dev
call :check_docker
call :check_docker_compose
docker-compose -f %COMPOSE_DEV_FILE% logs -f %2
goto :eof

:status
call :check_docker
call :check_docker_compose
echo [INFO] Service Status:
docker-compose -f %COMPOSE_FILE% ps
goto :eof

:clean
echo [WARNING] This will remove all containers, networks, and volumes!
set /p "confirm=Are you sure? (y/N): "
if /i "!confirm!"=="y" (
    echo [INFO] Cleaning up...
    docker-compose -f %COMPOSE_FILE% down -v --remove-orphans
    docker-compose -f %COMPOSE_DEV_FILE% down -v --remove-orphans
    docker system prune -f
    echo [SUCCESS] Cleanup completed
) else (
    echo [INFO] Cleanup cancelled
)
goto :eof

:update
call :check_docker
call :check_docker_compose
echo [INFO] Updating VisionAI-ClipsMaster...
docker-compose -f %COMPOSE_FILE% pull
docker-compose -f %COMPOSE_FILE% up -d
echo [SUCCESS] Update completed
goto :eof

:backup
call :check_docker
call :check_docker_compose
echo [INFO] Creating backup...
set BACKUP_DIR=backups\%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=!BACKUP_DIR: =0!
mkdir !BACKUP_DIR! 2>nul

REM Backup database
docker-compose -f %COMPOSE_FILE% exec -T postgres pg_dump -U visionai visionai > !BACKUP_DIR!\database.sql

echo [SUCCESS] Backup created in !BACKUP_DIR!
goto :eof

:show_help
call :print_header
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   setup       - Initial setup (create directories, copy env file)
echo   build       - Build production Docker images
echo   build-dev   - Build development Docker images
echo   start       - Start production services
echo   start-dev   - Start development services
echo   stop        - Stop production services
echo   stop-dev    - Stop development services
echo   restart     - Restart production services
echo   logs        - Show production logs
echo   logs-dev    - Show development logs
echo   status      - Show service status
echo   clean       - Clean up all containers and volumes
echo   update      - Update and restart services
echo   backup      - Create backup of data
echo   help        - Show this help message
echo.
echo Examples:
echo   %0 setup
echo   %0 build
echo   %0 start
echo   %0 logs visionai-app
echo   %0 start-dev
goto :eof
