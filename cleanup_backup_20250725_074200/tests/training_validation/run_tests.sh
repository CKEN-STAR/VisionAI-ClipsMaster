#!/bin/bash

# VisionAI-ClipsMaster 训练验证系统运行脚本

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        if ! command -v python &> /dev/null; then
            print_error "未找到Python环境"
            echo "请确保Python 3.7+已安装"
            exit 1
        else
            PYTHON_CMD="python"
        fi
    else
        PYTHON_CMD="python3"
    fi
    
    print_info "使用Python命令: $PYTHON_CMD"
    $PYTHON_CMD --version
}

# 显示菜单
show_menu() {
    echo "========================================"
    echo "VisionAI-ClipsMaster 训练验证系统"
    echo "========================================"
    echo ""
    echo "请选择要执行的测试:"
    echo ""
    echo "1. 快速测试 (推荐新用户)"
    echo "2. 训练效果验证"
    echo "3. GPU加速测试"
    echo "4. 质量指标测试"
    echo "5. 内存性能测试"
    echo "6. 完整验证套件"
    echo "7. 查看测试报告"
    echo "8. 清理测试输出"
    echo "0. 退出"
    echo ""
}

# 快速测试
run_quick_test() {
    print_info "执行快速测试..."
    echo "========================================"
    
    if $PYTHON_CMD quick_test.py; then
        print_success "快速测试完成"
    else
        print_error "快速测试失败"
    fi
}

# 训练效果验证测试
run_effectiveness_test() {
    print_info "执行训练效果验证测试..."
    echo "========================================"
    
    if $PYTHON_CMD test_training_effectiveness.py; then
        print_success "训练效果验证测试完成"
    else
        print_error "训练效果验证测试失败"
    fi
}

# GPU加速测试
run_gpu_test() {
    print_info "执行GPU加速测试..."
    echo "========================================"
    
    if $PYTHON_CMD test_gpu_acceleration.py; then
        print_success "GPU加速测试完成"
    else
        print_error "GPU加速测试失败"
    fi
}

# 质量指标测试
run_quality_test() {
    print_info "执行质量指标测试..."
    echo "========================================"
    
    if $PYTHON_CMD test_quality_metrics.py; then
        print_success "质量指标测试完成"
    else
        print_error "质量指标测试失败"
    fi
}

# 内存性能测试
run_memory_test() {
    print_info "执行内存性能测试..."
    echo "========================================"
    
    if $PYTHON_CMD test_memory_performance.py; then
        print_success "内存性能测试完成"
    else
        print_error "内存性能测试失败"
    fi
}

# 完整验证套件
run_full_suite() {
    print_info "执行完整验证套件..."
    echo "========================================"
    print_warning "完整测试可能需要较长时间 (5-15分钟)"
    
    read -p "确认执行? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        if $PYTHON_CMD run_training_validation_suite.py; then
            print_success "完整验证套件执行完成"
        else
            print_error "完整验证套件执行失败"
        fi
    else
        print_info "已取消执行"
    fi
}

# 查看测试报告
view_reports() {
    print_info "查看测试报告..."
    echo "========================================"
    
    TEST_OUTPUT_DIR="../../test_output"
    
    if [ ! -d "$TEST_OUTPUT_DIR" ]; then
        print_warning "未找到测试输出目录"
        echo "请先运行测试生成报告"
        return
    fi
    
    echo "最近的测试报告:"
    echo ""
    
    # 查找HTML报告
    if ls "$TEST_OUTPUT_DIR"/*.html 1> /dev/null 2>&1; then
        echo "HTML报告:"
        ls -lt "$TEST_OUTPUT_DIR"/*.html | head -5 | awk '{print "  " $9}'
        latest_html=$(ls -t "$TEST_OUTPUT_DIR"/*.html | head -1)
    fi
    
    # 查找JSON报告
    if ls "$TEST_OUTPUT_DIR"/*.json 1> /dev/null 2>&1; then
        echo "JSON报告:"
        ls -lt "$TEST_OUTPUT_DIR"/*.json | head -5 | awk '{print "  " $9}'
        latest_json=$(ls -t "$TEST_OUTPUT_DIR"/*.json | head -1)
    fi
    
    echo ""
    
    # 询问是否打开最新报告
    if [ -n "$latest_html" ]; then
        read -p "打开最新的HTML报告? (y/N): " open_html
        if [[ $open_html =~ ^[Yy]$ ]]; then
            if command -v xdg-open &> /dev/null; then
                xdg-open "$latest_html"
            elif command -v open &> /dev/null; then
                open "$latest_html"
            else
                print_info "请手动打开: $latest_html"
            fi
        fi
    fi
}

# 清理测试输出
cleanup_output() {
    print_info "清理测试输出..."
    echo "========================================"
    
    read -p "确认删除所有测试输出文件? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        if [ -d "../../test_output" ]; then
            rm -rf "../../test_output"
            print_success "测试输出已清理"
        else
            print_info "测试输出目录不存在"
        fi
        
        if [ -d "../../logs" ]; then
            rm -f "../../logs"/training_validation_*.log
            print_success "训练验证日志已清理"
        fi
    else
        print_info "已取消清理操作"
    fi
}

# 主函数
main() {
    # 检查Python环境
    check_python
    
    while true; do
        echo ""
        show_menu
        read -p "请输入选项 (0-8): " choice
        
        case $choice in
            1)
                run_quick_test
                ;;
            2)
                run_effectiveness_test
                ;;
            3)
                run_gpu_test
                ;;
            4)
                run_quality_test
                ;;
            5)
                run_memory_test
                ;;
            6)
                run_full_suite
                ;;
            7)
                view_reports
                ;;
            8)
                cleanup_output
                ;;
            0)
                echo ""
                print_info "感谢使用VisionAI-ClipsMaster训练验证系统"
                echo ""
                exit 0
                ;;
            *)
                print_error "无效选项，请重新选择"
                ;;
        esac
        
        echo ""
        read -p "按Enter键继续..."
    done
}

# 脚本入口点
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
