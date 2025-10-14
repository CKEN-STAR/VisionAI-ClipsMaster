#!/bin/bash
# VisionAI-ClipsMaster Docker Management Script
# Provides easy commands for Docker operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="visionai-clipsmaster"
COMPOSE_FILE="docker/docker-compose.root.yml"
COMPOSE_DEV_FILE="docker/docker-compose.dev.root.yml"

# Helper functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  VisionAI-ClipsMaster Docker Manager${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    mkdir -p models data output logs cache static
    mkdir -p docker/nginx/ssl
    print_success "Directories created"
}

# Copy environment file
setup_env() {
    if [ ! -f .env ]; then
        print_info "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please edit .env file with your configuration"
    else
        print_info ".env file already exists"
    fi
}

# Build images
build() {
    print_info "Building Docker images..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    print_success "Images built successfully"
}

# Build development images
build_dev() {
    print_info "Building development Docker images..."
    docker-compose -f $COMPOSE_DEV_FILE build --no-cache
    print_success "Development images built successfully"
}

# Start production services
start() {
    print_info "Starting VisionAI-ClipsMaster services..."
    docker-compose -f $COMPOSE_FILE up -d
    print_success "Services started successfully"
    
    print_info "Waiting for services to be ready..."
    sleep 10
    
    print_info "Service URLs:"
    echo "  - Main Application: http://localhost:8000"
    echo "  - Web Interface: http://localhost:8080"
    echo "  - API: http://localhost:5000"
    echo "  - Nginx Proxy: http://localhost:80"
}

# Start development services
start_dev() {
    print_info "Starting VisionAI-ClipsMaster development services..."
    docker-compose -f $COMPOSE_DEV_FILE up -d
    print_success "Development services started successfully"
    
    print_info "Development URLs:"
    echo "  - Main Application: http://localhost:8000"
    echo "  - Jupyter Lab: http://localhost:8888"
    echo "  - Jupyter Notebook: http://localhost:8889"
}

# Stop services
stop() {
    print_info "Stopping VisionAI-ClipsMaster services..."
    docker-compose -f $COMPOSE_FILE down
    print_success "Services stopped successfully"
}

# Stop development services
stop_dev() {
    print_info "Stopping development services..."
    docker-compose -f $COMPOSE_DEV_FILE down
    print_success "Development services stopped successfully"
}

# Restart services
restart() {
    print_info "Restarting VisionAI-ClipsMaster services..."
    docker-compose -f $COMPOSE_FILE restart
    print_success "Services restarted successfully"
}

# Show logs
logs() {
    docker-compose -f $COMPOSE_FILE logs -f "${2:-}"
}

# Show development logs
logs_dev() {
    docker-compose -f $COMPOSE_DEV_FILE logs -f "${2:-}"
}

# Show status
status() {
    print_info "Service Status:"
    docker-compose -f $COMPOSE_FILE ps
}

# Clean up
clean() {
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker-compose -f $COMPOSE_FILE down -v --remove-orphans
        docker-compose -f $COMPOSE_DEV_FILE down -v --remove-orphans
        docker system prune -f
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Update images
update() {
    print_info "Updating VisionAI-ClipsMaster..."
    docker-compose -f $COMPOSE_FILE pull
    docker-compose -f $COMPOSE_FILE up -d
    print_success "Update completed"
}

# Backup data
backup() {
    print_info "Creating backup..."
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # Backup database
    docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U visionai visionai > $BACKUP_DIR/database.sql
    
    # Backup volumes
    docker run --rm -v visionai-clipsmaster_postgres-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/postgres-data.tar.gz -C /data .
    docker run --rm -v visionai-clipsmaster_redis-data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/redis-data.tar.gz -C /data .
    
    print_success "Backup created in $BACKUP_DIR"
}

# Show help
show_help() {
    print_header
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup       - Initial setup (create directories, copy env file)"
    echo "  build       - Build production Docker images"
    echo "  build-dev   - Build development Docker images"
    echo "  start       - Start production services"
    echo "  start-dev   - Start development services"
    echo "  stop        - Stop production services"
    echo "  stop-dev    - Stop development services"
    echo "  restart     - Restart production services"
    echo "  logs        - Show production logs"
    echo "  logs-dev    - Show development logs"
    echo "  status      - Show service status"
    echo "  clean       - Clean up all containers and volumes"
    echo "  update      - Update and restart services"
    echo "  backup      - Create backup of data"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup && $0 build && $0 start"
    echo "  $0 logs visionai-app"
    echo "  $0 start-dev"
}

# Main script logic
main() {
    check_docker
    check_docker_compose
    
    case "${1:-help}" in
        setup)
            create_directories
            setup_env
            ;;
        build)
            build
            ;;
        build-dev)
            build_dev
            ;;
        start)
            start
            ;;
        start-dev)
            start_dev
            ;;
        stop)
            stop
            ;;
        stop-dev)
            stop_dev
            ;;
        restart)
            restart
            ;;
        logs)
            logs "$@"
            ;;
        logs-dev)
            logs_dev "$@"
            ;;
        status)
            status
            ;;
        clean)
            clean
            ;;
        update)
            update
            ;;
        backup)
            backup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
