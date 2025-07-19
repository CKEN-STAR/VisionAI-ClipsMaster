#!/bin/bash
# VisionAI-ClipsMaster Docker容器入口脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 初始化函数
initialize() {
    log_info "初始化VisionAI-ClipsMaster容器..."
    
    # 检查环境变量
    if [ -n "$VISIONAI_MODE" ]; then
        log_info "运行模式: $VISIONAI_MODE"
    fi
    
    if [ -n "$VISIONAI_MAX_MEMORY" ]; then
        log_info "内存限制: ${VISIONAI_MAX_MEMORY}MB"
    fi
    
    # 创建必要目录
    mkdir -p data/input data/output logs models
    
    # 设置权限
    chmod 755 data/input data/output logs models
    
    log_success "容器初始化完成"
}

# 检查模型文件
check_models() {
    log_info "检查模型文件..."
    
    if [ ! -d "models" ] || [ -z "$(ls -A models)" ]; then
        log_warning "未找到模型文件"
        log_info "首次运行需要下载模型文件"
        log_info "请运行: docker exec -it <container_name> python scripts/setup_models.py --setup"
        return 1
    fi
    
    log_success "模型文件检查完成"
    return 0
}

# 运行环境检查
run_health_check() {
    log_info "运行环境检查..."
    
    if python scripts/check_environment.py; then
        log_success "环境检查通过"
        return 0
    else
        log_error "环境检查失败"
        return 1
    fi
}

# 启动GUI模式
start_gui() {
    log_info "启动GUI模式..."
    
    # 检查X11转发
    if [ -z "$DISPLAY" ]; then
        log_error "未检测到DISPLAY环境变量"
        log_info "GUI模式需要X11转发，请使用以下命令启动容器:"
        log_info "docker run -e DISPLAY=\$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix visionai-clipsmaster"
        exit 1
    fi
    
    # 启动GUI应用
    python src/visionai_clipsmaster/ui/main_window.py
}

# 启动CLI模式
start_cli() {
    log_info "启动CLI模式..."
    
    if [ $# -eq 0 ]; then
        # 显示帮助信息
        python src/cli.py --help
    else
        # 执行CLI命令
        python src/cli.py "$@"
    fi
}

# 启动Web模式
start_web() {
    log_info "启动Web模式..."
    
    # 设置默认端口
    PORT=${VISIONAI_PORT:-8080}
    HOST=${VISIONAI_HOST:-0.0.0.0}
    
    log_info "Web服务将在 http://${HOST}:${PORT} 启动"
    
    # 启动Web服务
    python src/visionai_clipsmaster/web/app.py --host "$HOST" --port "$PORT"
}

# 启动开发模式
start_dev() {
    log_info "启动开发模式..."
    
    # 安装开发依赖
    if [ -f "requirements/requirements-dev.txt" ]; then
        log_info "安装开发依赖..."
        pip install --user -r requirements/requirements-dev.txt
    fi
    
    # 运行测试
    log_info "运行测试套件..."
    python scripts/run_tests.py
    
    # 启动开发服务器
    start_web
}

# 下载模型
download_models() {
    log_info "下载模型文件..."
    
    # 检查网络连接
    if ! curl -s --head https://huggingface.co > /dev/null; then
        log_error "无法连接到HuggingFace，请检查网络连接"
        exit 1
    fi
    
    # 运行模型下载脚本
    python scripts/setup_models.py --setup
}

# 运行基准测试
run_benchmark() {
    log_info "运行性能基准测试..."
    
    if [ -f "scripts/benchmark.py" ]; then
        python scripts/benchmark.py
    else
        log_error "基准测试脚本不存在"
        exit 1
    fi
}

# 清理缓存
cleanup() {
    log_info "清理缓存和临时文件..."
    
    # 清理Python缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # 清理日志文件
    find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # 清理临时文件
    rm -rf /tmp/visionai_* 2>/dev/null || true
    
    log_success "清理完成"
}

# 显示帮助信息
show_help() {
    cat << EOF
VisionAI-ClipsMaster Docker容器

用法: docker run [OPTIONS] visionai-clipsmaster [COMMAND] [ARGS...]

命令:
  gui                启动图形界面模式 (需要X11转发)
  cli [args...]      启动命令行模式
  web               启动Web服务模式
  dev               启动开发模式
  download-models   下载AI模型文件
  benchmark         运行性能基准测试
  cleanup           清理缓存和临时文件
  health-check      运行环境检查
  help              显示此帮助信息

环境变量:
  VISIONAI_MODE         运行模式 (lite/full)
  VISIONAI_MAX_MEMORY   最大内存使用 (MB)
  VISIONAI_PORT         Web服务端口 (默认: 8080)
  VISIONAI_HOST         Web服务主机 (默认: 0.0.0.0)

示例:
  # 启动GUI模式
  docker run -e DISPLAY=\$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix visionai-clipsmaster gui
  
  # 启动Web模式
  docker run -p 8080:8080 visionai-clipsmaster web
  
  # 运行CLI命令
  docker run -v \$(pwd)/data:/home/visionai/data visionai-clipsmaster cli --help
  
  # 下载模型
  docker run -v \$(pwd)/models:/home/visionai/models visionai-clipsmaster download-models

EOF
}

# 主函数
main() {
    # 初始化容器
    initialize
    
    # 解析命令
    case "${1:-gui}" in
        "gui")
            run_health_check
            start_gui
            ;;
        "cli")
            shift
            start_cli "$@"
            ;;
        "web")
            run_health_check
            start_web
            ;;
        "dev")
            start_dev
            ;;
        "download-models")
            download_models
            ;;
        "benchmark")
            run_benchmark
            ;;
        "cleanup")
            cleanup
            ;;
        "health-check")
            run_health_check
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 信号处理
trap 'log_info "收到停止信号，正在清理..."; cleanup; exit 0' SIGTERM SIGINT

# 运行主函数
main "$@"
