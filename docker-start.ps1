# VisionAI-ClipsMaster Docker Management Script for PowerShell
# Provides easy commands for Docker operations with enhanced Windows support

param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "build", "build-dev", "start", "start-dev", "stop", "stop-dev", 
                 "restart", "logs", "logs-dev", "status", "clean", "update", "backup", "help")]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Service = ""
)

# Configuration
$ComposeFile = "docker-compose.yml"
$ComposeDevFile = "docker-compose.dev.yml"

# Helper functions
function Write-Header {
    Write-Host "=============================================" -ForegroundColor Blue
    Write-Host "  VisionAI-ClipsMaster Docker Manager" -ForegroundColor Blue
    Write-Host "=============================================" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Test-Docker {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        Write-Error "Docker is not running. Please start Docker first."
        return $false
    }
}

function Test-DockerCompose {
    try {
        docker-compose --version | Out-Null
        return $true
    }
    catch {
        Write-Error "Docker Compose is not installed. Please install Docker Compose first."
        return $false
    }
}

function New-Directories {
    Write-Info "Creating necessary directories..."
    $directories = @("models", "data", "output", "logs", "cache", "static", "docker`nginx\ssl")
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    Write-Success "Directories created"
}

function Initialize-Environment {
    if (!(Test-Path ".env")) {
        Write-Info "Creating .env file from template..."
        Copy-Item ".env.example" ".env"
        Write-Warning "Please edit .env file with your configuration"
    } else {
        Write-Info ".env file already exists"
    }
}

function Invoke-Setup {
    Write-Header
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    New-Directories
    Initialize-Environment
    Write-Success "Setup completed"
}

function Invoke-Build {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Building Docker images..."
    docker-compose -f $ComposeFile build --no-cache
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Images built successfully"
    } else {
        Write-Error "Failed to build images"
    }
}

function Invoke-BuildDev {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Building development Docker images..."
    docker-compose -f $ComposeDevFile build --no-cache
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Development images built successfully"
    } else {
        Write-Error "Failed to build development images"
    }
}

function Invoke-Start {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Starting VisionAI-ClipsMaster services..."
    docker-compose -f $ComposeFile up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services started successfully"
        
        Write-Info "Waiting for services to be ready..."
        Start-Sleep -Seconds 10
        
        Write-Info "Service URLs:"
        Write-Host "  - Main Application: http://localhost:8000" -ForegroundColor White
        Write-Host "  - Web Interface: http://localhost:8080" -ForegroundColor White
        Write-Host "  - API: http://localhost:5000" -ForegroundColor White
        Write-Host "  - Nginx Proxy: http://localhost:80" -ForegroundColor White
    } else {
        Write-Error "Failed to start services"
    }
}

function Invoke-StartDev {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Starting VisionAI-ClipsMaster development services..."
    docker-compose -f $ComposeDevFile up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Development services started successfully"
        
        Write-Info "Development URLs:"
        Write-Host "  - Main Application: http://localhost:8000" -ForegroundColor White
        Write-Host "  - Jupyter Lab: http://localhost:8888" -ForegroundColor White
        Write-Host "  - Jupyter Notebook: http://localhost:8889" -ForegroundColor White
    } else {
        Write-Error "Failed to start development services"
    }
}

function Invoke-Stop {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Stopping VisionAI-ClipsMaster services..."
    docker-compose -f $ComposeFile down
    Write-Success "Services stopped successfully"
}

function Invoke-StopDev {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Stopping development services..."
    docker-compose -f $ComposeDevFile down
    Write-Success "Development services stopped successfully"
}

function Invoke-Restart {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Restarting VisionAI-ClipsMaster services..."
    docker-compose -f $ComposeFile restart
    Write-Success "Services restarted successfully"
}

function Show-Logs {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    if ($Service) {
        docker-compose -f $ComposeFile logs -f $Service
    } else {
        docker-compose -f $ComposeFile logs -f
    }
}

function Show-LogsDev {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    if ($Service) {
        docker-compose -f $ComposeDevFile logs -f $Service
    } else {
        docker-compose -f $ComposeDevFile logs -f
    }
}

function Show-Status {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Service Status:"
    docker-compose -f $ComposeFile ps
}

function Invoke-Clean {
    Write-Warning "This will remove all containers, networks, and volumes!"
    $confirm = Read-Host "Are you sure? (y/N)"
    
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Write-Info "Cleaning up..."
        docker-compose -f $ComposeFile down -v --remove-orphans
        docker-compose -f $ComposeDevFile down -v --remove-orphans
        docker system prune -f
        Write-Success "Cleanup completed"
    } else {
        Write-Info "Cleanup cancelled"
    }
}

function Invoke-Update {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Updating VisionAI-ClipsMaster..."
    docker-compose -f $ComposeFile pull
    docker-compose -f $ComposeFile up -d
    Write-Success "Update completed"
}

function Invoke-Backup {
    if (!(Test-Docker) -or !(Test-DockerCompose)) { return }
    
    Write-Info "Creating backup..."
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = "backups\$timestamp"
    
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # Backup database
    docker-compose -f $ComposeFile exec -T postgres pg_dump -U visionai visionai | Out-File -FilePath "$backupDir\database.sql" -Encoding UTF8
    
    Write-Success "Backup created in $backupDir"
}

function Show-Help {
    Write-Header
    Write-Host "Usage: .\docker-start.ps1 [COMMAND] [SERVICE]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  setup       - Initial setup (create directories, copy env file)" -ForegroundColor White
    Write-Host "  build       - Build production Docker images" -ForegroundColor White
    Write-Host "  build-dev   - Build development Docker images" -ForegroundColor White
    Write-Host "  start       - Start production services" -ForegroundColor White
    Write-Host "  start-dev   - Start development services" -ForegroundColor White
    Write-Host "  stop        - Stop production services" -ForegroundColor White
    Write-Host "  stop-dev    - Stop development services" -ForegroundColor White
    Write-Host "  restart     - Restart production services" -ForegroundColor White
    Write-Host "  logs        - Show production logs" -ForegroundColor White
    Write-Host "  logs-dev    - Show development logs" -ForegroundColor White
    Write-Host "  status      - Show service status" -ForegroundColor White
    Write-Host "  clean       - Clean up all containers and volumes" -ForegroundColor White
    Write-Host "  update      - Update and restart services" -ForegroundColor White
    Write-Host "  backup      - Create backup of data" -ForegroundColor White
    Write-Host "  help        - Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\docker-start.ps1 setup" -ForegroundColor Gray
    Write-Host "  .\docker-start.ps1 build" -ForegroundColor Gray
    Write-Host "  .\docker-start.ps1 start" -ForegroundColor Gray
    Write-Host "  .\docker-start.ps1 logs visionai-app" -ForegroundColor Gray
    Write-Host "  .\docker-start.ps1 start-dev" -ForegroundColor Gray
}

# Main execution
switch ($Command) {
    "setup" { Invoke-Setup }
    "build" { Invoke-Build }
    "build-dev" { Invoke-BuildDev }
    "start" { Invoke-Start }
    "start-dev" { Invoke-StartDev }
    "stop" { Invoke-Stop }
    "stop-dev" { Invoke-StopDev }
    "restart" { Invoke-Restart }
    "logs" { Show-Logs }
    "logs-dev" { Show-LogsDev }
    "status" { Show-Status }
    "clean" { Invoke-Clean }
    "update" { Invoke-Update }
    "backup" { Invoke-Backup }
    "help" { Show-Help }
    default { Show-Help }
}
