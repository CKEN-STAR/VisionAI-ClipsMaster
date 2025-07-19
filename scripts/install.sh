#!/bin/bash
# VisionAI-ClipsMaster Linux/macOS 自动安装脚本

set -e  # 遇到错误立即退出

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

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# 检测系统内存
get_memory_gb() {
    if [[ "$(detect_os)" == "linux" ]]; then
        # Linux
        memory_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        echo $((memory_kb / 1024 / 1024))
    elif [[ "$(detect_os)" == "macos" ]]; then
        # macOS
        memory_bytes=$(sysctl -n hw.memsize)
        echo $((memory_bytes / 1024 / 1024 / 1024))
    else
        echo "8"  # 默认假设8GB
    fi
}

# 主安装函数
main() {
    echo "========================================"
    echo "VisionAI-ClipsMaster 自动安装程序"
    echo "========================================"
    echo

    # 1. 检查Python
    log_info "检查Python环境..."
    if ! command_exists python3; then
        log_error "未检测到Python3，请先安装Python 3.8+"
        if [[ "$(detect_os)" == "linux" ]]; then
            log_info "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
            log_info "CentOS/RHEL: sudo yum install python3 python3-pip"
        elif [[ "$(detect_os)" == "macos" ]]; then
            log_info "macOS: brew install python3"
            log_info "或从官网下载: https://www.python.org/downloads/"
        fi
        exit 1
    fi

    # 检查Python版本
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Python版本: $python_version"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_error "Python版本过低，需要3.8+，当前版本: $python_version"
        exit 1
    fi

    # 2. 检查系统配置
    log_info "检查系统配置..."
    memory_gb=$(get_memory_gb)
    log_info "系统内存: ${memory_gb}GB"
    
    # 确定安装模式
    if [ "$memory_gb" -le 4 ]; then
        install_mode="lite"
        log_info "使用轻量化模式（4GB内存优化）"
    else
        install_mode="full"
        log_info "使用完整模式"
    fi

    # 3. 检查必要工具
    log_info "检查必要工具..."
    
    # 检查pip
    if ! command_exists pip3; then
        log_warning "pip3未安装，正在尝试安装..."
        if [[ "$(detect_os)" == "linux" ]]; then
            if command_exists apt; then
                sudo apt update && sudo apt install python3-pip
            elif command_exists yum; then
                sudo yum install python3-pip
            fi
        elif [[ "$(detect_os)" == "macos" ]]; then
            python3 -m ensurepip --upgrade
        fi
    fi

    # 升级pip
    log_info "升级pip..."
    python3 -m pip install --upgrade pip

    # 4. 创建虚拟环境
    log_info "创建虚拟环境..."
    if [ -d "venv" ]; then
        log_warning "虚拟环境已存在，将重新创建"
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate

    # 5. 安装依赖
    log_info "安装Python依赖..."
    if [ "$install_mode" = "lite" ]; then
        pip install -r requirements/requirements-lite.txt
    else
        pip install -r requirements/requirements.txt
    fi

    # 6. 环境验证
    log_info "验证安装..."
    if python scripts/check_environment.py; then
        log_success "环境验证通过"
    else
        log_warning "环境验证发现问题，但安装已完成"
    fi

    # 7. 创建启动脚本
    log_info "创建启动脚本..."
    cat > start_visionai.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python src/visionai_clipsmaster/ui/main_window.py
EOF
    chmod +x start_visionai.sh

    # 8. 创建命令行启动脚本
    cat > visionai_cli.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python src/cli.py "$@"
EOF
    chmod +x visionai_cli.sh

    # 完成安装
    echo
    echo "========================================"
    log_success "安装完成！"
    echo "========================================"
    echo
    log_info "安装位置: $(pwd)"
    log_info "启动方式:"
    echo "  1. 图形界面: ./start_visionai.sh"
    echo "  2. 命令行: ./visionai_cli.sh --help"
    echo "  3. 手动启动: source venv/bin/activate && python src/visionai_clipsmaster/ui/main_window.py"
    echo
    log_info "下一步：下载AI模型"
    echo "  source venv/bin/activate"
    echo "  python scripts/setup_models.py --setup"
    echo
    log_info "首次使用建议："
    echo "  1. 运行环境检查: python scripts/check_environment.py"
    echo "  2. 下载推荐模型: python scripts/setup_models.py --setup"
    echo "  3. 运行测试: python scripts/run_tests.py"
    echo

    # 询问是否立即下载模型
    read -p "是否现在下载AI模型? (y/N): " download_models
    if [[ "$download_models" =~ ^[Yy]$ ]]; then
        log_info "开始下载模型..."
        python scripts/setup_models.py --setup
    fi

    log_success "安装完成！"
}

# 错误处理
trap 'log_error "安装过程中发生错误，请检查上述输出信息"' ERR

# 运行主函数
main "$@"
