#!/bin/bash
# VisionAI-ClipsMaster 框架验证脚本
# 验证项目环境、结构和依赖，确保测试和开发环境正确配置

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 错误计数器
ERROR_COUNT=0

# 记录成功消息
log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 记录警告消息
log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 记录错误消息
log_error() {
    echo -e "${RED}✗ $1${NC}"
    ERROR_COUNT=$((ERROR_COUNT + 1))
}

# 记录信息消息
log_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# 检查目录存在性
check_dir_exists() {
    local dir="$1"
    if [ -d "$dir" ]; then
        log_success "目录存在: $dir"
        return 0
    else
        log_error "目录不存在: $dir"
        return 1
    fi
}

# 检查文件存在性
check_file_exists() {
    local file="$1"
    if [ -f "$file" ]; then
        log_success "文件存在: $file"
        return 0
    else
        log_error "文件不存在: $file"
        return 1
    fi
}

# 检查命令是否存在
check_command() {
    local cmd="$1"
    if command -v "$cmd" >/dev/null 2>&1; then
        log_success "命令可用: $cmd"
        return 0
    else
        log_error "命令不可用: $cmd"
        return 1
    fi
}

# 检查Python模块是否已安装
check_python_module() {
    local module="$1"
    if python -c "import $module" >/dev/null 2>&1; then
        log_success "Python模块已安装: $module"
        return 0
    else
        log_error "Python模块未安装: $module"
        return 1
    fi
}

# 检查目录结构
check_dir_structure() {
    echo -e "\n${BLUE}=== 检查目录结构 ===${NC}"
    
    # 检查核心目录
    check_dir_exists "$PROJECT_ROOT/src"
    check_dir_exists "$PROJECT_ROOT/tests"
    check_dir_exists "$PROJECT_ROOT/docs"
    check_dir_exists "$PROJECT_ROOT/scripts"
    
    # 检查测试相关目录
    check_dir_exists "$PROJECT_ROOT/tests/unit"
    check_dir_exists "$PROJECT_ROOT/tests/functional"
    check_dir_exists "$PROJECT_ROOT/tests/integration"
    check_dir_exists "$PROJECT_ROOT/tests/golden_samples"
    check_dir_exists "$PROJECT_ROOT/tests/data"
    check_dir_exists "$PROJECT_ROOT/tests/tmp_output"
    check_dir_exists "$PROJECT_ROOT/tests/configs"
    
    # 检查模型目录
    check_dir_exists "$PROJECT_ROOT/models"
    check_dir_exists "$PROJECT_ROOT/models/chinese"
    check_dir_exists "$PROJECT_ROOT/models/english"
}

# 检查pytest安装和版本
check_pytest() {
    echo -e "\n${BLUE}=== 检查Pytest安装 ===${NC}"
    
    if check_command "pytest"; then
        # 检查版本
        PYTEST_VERSION=$(pytest --version | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        if [ -n "$PYTEST_VERSION" ]; then
            MAJOR_VERSION=$(echo $PYTEST_VERSION | cut -d. -f1)
            MINOR_VERSION=$(echo $PYTEST_VERSION | cut -d. -f2)
            
            if [ "$MAJOR_VERSION" -ge 7 ]; then
                log_success "Pytest版本 $PYTEST_VERSION 满足要求"
            else
                log_warning "Pytest版本 $PYTEST_VERSION 可能过低，推荐 7.0.0 或更高版本"
            fi
        else
            log_warning "无法确定Pytest版本"
        fi
        
        # 测试pytest是否可以正常运行
        if pytest --version > /dev/null 2>&1; then
            log_success "Pytest可以正常运行"
        else
            log_error "Pytest无法正常运行"
        fi
    fi
}

# 检查配置文件
check_config() {
    echo -e "\n${BLUE}=== 检查配置文件 ===${NC}"
    
    # 检查测试配置文件
    check_file_exists "$PROJECT_ROOT/tests/configs/test_config.yaml"
    
    # 检查配置文件格式是否正确
    if [ -f "$PROJECT_ROOT/tests/configs/test_config.yaml" ]; then
        if command -v python >/dev/null 2>&1; then
            if python -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/tests/configs/test_config.yaml'))" >/dev/null 2>&1; then
                log_success "测试配置文件格式正确"
            else
                log_error "测试配置文件格式不正确"
            fi
        else
            log_warning "Python不可用，无法验证YAML格式"
        fi
    fi
    
    # 检查模型配置文件
    check_file_exists "$PROJECT_ROOT/models/chinese/config.json"
    check_file_exists "$PROJECT_ROOT/models/english/config.json"
}

# 检查Python环境
check_python_env() {
    echo -e "\n${BLUE}=== 检查Python环境 ===${NC}"
    
    # 检查Python版本
    if command -v python >/dev/null 2>&1; then
        PYTHON_VERSION=$(python --version 2>&1 | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+')
        log_success "Python版本: $PYTHON_VERSION"
        
        # 检查核心依赖
        check_python_module "numpy"
        check_python_module "torch"
        check_python_module "transformers"
        check_python_module "yaml"
        check_python_module "pytest"
        check_python_module "cv2"  # OpenCV
    else
        log_error "Python未安装或不在PATH中"
    fi
}

# 检查系统依赖
check_system_deps() {
    echo -e "\n${BLUE}=== 检查系统依赖 ===${NC}"
    
    # 检查FFmpeg（视频处理必需）
    if command -v ffmpeg >/dev/null 2>&1; then
        FFMPEG_VERSION=$(ffmpeg -version | grep -Eo 'version [0-9]+\.[0-9]+' | head -1)
        log_success "FFmpeg已安装: $FFMPEG_VERSION"
    else
        log_warning "FFmpeg未安装，视频处理功能可能受限"
    fi
    
    # 检查Git
    if command -v git >/dev/null 2>&1; then
        GIT_VERSION=$(git --version | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+')
        log_success "Git已安装: $GIT_VERSION"
    else
        log_warning "Git未安装，版本控制功能可能受限"
    fi
}

# 检查测试数据
check_test_data() {
    echo -e "\n${BLUE}=== 检查测试数据 ===${NC}"
    
    if [ -d "$PROJECT_ROOT/tests/data" ] && [ "$(ls -A "$PROJECT_ROOT/tests/data" 2>/dev/null)" ]; then
        log_success "测试数据目录非空"
    else
        log_warning "测试数据目录为空，运行部分测试可能会失败"
        log_info "可以运行 python scripts/init_test_data.py 初始化测试数据"
    fi
    
    # 检查黄金样本
    if [ -d "$PROJECT_ROOT/tests/golden_samples" ] && [ "$(ls -A "$PROJECT_ROOT/tests/golden_samples" 2>/dev/null)" ]; then
        log_success "黄金样本目录非空"
    else
        log_warning "黄金样本目录为空，对比测试可能会失败"
    fi
}

# 主函数
main() {
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${BLUE}   VisionAI-ClipsMaster 框架验证            ${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    # 检查当前工作目录
    log_info "当前目录: $(pwd)"
    log_info "项目根目录: $PROJECT_ROOT"
    
    # 检查环境
    check_dir_structure
    check_pytest
    check_config
    check_python_env
    check_system_deps
    check_test_data
    
    # 总结
    echo -e "\n${BLUE}=== 验证结果 ===${NC}"
    if [ $ERROR_COUNT -eq 0 ]; then
        echo -e "${GREEN}✓ 框架验证通过，没有发现错误${NC}"
        exit 0
    else
        echo -e "${RED}✗ 框架验证失败，发现 $ERROR_COUNT 个错误${NC}"
        exit 1
    fi
}

# 执行主函数
main 