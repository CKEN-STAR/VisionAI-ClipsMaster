#!/bin/bash
# 测试环境创建与验证脚本
# 支持Windows(PowerShell)和Linux/macOS

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 确定操作系统
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    IS_WINDOWS=true
    echo -e "${BLUE}检测到Windows系统${NC}"
else
    IS_WINDOWS=false
    echo -e "${BLUE}检测到UNIX系统${NC}"
fi

# 创建测试环境
create_test_environment() {
    echo -e "${YELLOW}正在创建测试虚拟环境...${NC}"
    
    # 创建测试环境
    if [ "$IS_WINDOWS" = true ]; then
        python -m venv test_venv
    else
        python3 -m venv test_venv
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}虚拟环境创建失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
}

# 激活环境
activate_environment() {
    echo -e "${YELLOW}正在激活虚拟环境...${NC}"
    
    if [ "$IS_WINDOWS" = true ]; then
        source test_venv/Scripts/activate
    else
        source test_venv/bin/activate
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}虚拟环境激活失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 虚拟环境激活成功${NC}"
}

# 安装测试依赖
install_dependencies() {
    echo -e "${YELLOW}正在安装测试依赖...${NC}"
    
    # 确保目录存在
    mkdir -p tests
    
    # 运行Python安装脚本
    python scripts/setup_test_env.py
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}依赖安装失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 依赖安装成功${NC}"
}

# 创建测试数据
create_test_data() {
    echo -e "${YELLOW}正在创建测试数据...${NC}"
    
    # 创建测试目录
    mkdir -p data/input/subtitles
    mkdir -p data/input/videos
    mkdir -p data/output/generated_srt
    mkdir -p data/output/final_videos
    
    # 创建测试字幕
    if [ ! -f "data/input/subtitles/test_zh.srt" ]; then
        cat > data/input/subtitles/test_zh.srt << EOF
1
00:00:01,000 --> 00:00:05,000
大家好，这是一个测试字幕

2
00:00:06,000 --> 00:00:10,000
我们正在测试VisionAI-ClipsMaster
EOF
    fi
    
    if [ ! -f "data/input/subtitles/test_en.srt" ]; then
        cat > data/input/subtitles/test_en.srt << EOF
1
00:00:01,000 --> 00:00:05,000
Hello, this is a test subtitle

2
00:00:06,000 --> 00:00:10,000
We are testing VisionAI-ClipsMaster
EOF
    fi
    
    echo -e "${GREEN}✓ 测试数据创建成功${NC}"
}

# 运行语言检测测试
run_language_test() {
    echo -e "${YELLOW}正在运行语言检测测试...${NC}"
    
    # 运行语言检测测试
    python -m pytest tests/test_language_detector.py -v
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}语言检测测试失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 语言检测测试通过${NC}"
}

# 运行内存测试
run_memory_test() {
    echo -e "${YELLOW}正在运行内存监控测试...${NC}"
    
    # 运行内存监控测试
    python tests/memory_test.py
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}内存监控测试失败${NC}"
    else
        echo -e "${GREEN}✓ 内存监控测试通过${NC}"
    fi
}

# 验证模型配置
verify_model_configs() {
    echo -e "${YELLOW}正在验证模型配置...${NC}"
    
    # 检查模型配置文件是否存在
    if [ -f "configs/models/active_model.yaml" ] && 
       [ -f "configs/models/available_models/qwen2.5-7b-zh.yaml" ] && 
       [ -f "configs/models/available_models/mistral-7b-en.yaml" ]; then
        echo -e "${GREEN}✓ 模型配置文件验证通过${NC}"
    else
        echo -e "${RED}模型配置文件验证失败${NC}"
        exit 1
    fi
    
    # 验证语言检测和模型选择
    python src/core/language_detector.py data/input/subtitles/test_zh.srt
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}语言检测器验证失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 模型配置验证通过${NC}"
}

# 主函数
main() {
    echo -e "${BLUE}===== VisionAI-ClipsMaster 测试环境设置 =====${NC}"
    
    # 执行设置步骤
    create_test_environment
    activate_environment
    install_dependencies
    create_test_data
    run_language_test
    run_memory_test
    verify_model_configs
    
    echo -e "${BLUE}===== 测试环境设置完成 =====${NC}"
    echo -e "${GREEN}可通过以下命令激活测试环境:${NC}"
    
    if [ "$IS_WINDOWS" = true ]; then
        echo -e "   ${YELLOW}source test_venv/Scripts/activate${NC}"
    else
        echo -e "   ${YELLOW}source test_venv/bin/activate${NC}"
    fi
}

# 执行主函数
main 