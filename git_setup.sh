#!/bin/bash
# VisionAI-ClipsMaster Git初始化和配置脚本

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

# 检查Git是否安装
check_git() {
    if ! command -v git &> /dev/null; then
        log_error "Git未安装，请先安装Git"
        exit 1
    fi
    log_success "Git已安装: $(git --version)"
}

# 检查Git LFS是否安装
check_git_lfs() {
    if ! command -v git-lfs &> /dev/null; then
        log_warning "Git LFS未安装，正在尝试安装..."
        
        # 尝试安装Git LFS
        if command -v brew &> /dev/null; then
            brew install git-lfs
        elif command -v apt &> /dev/null; then
            sudo apt update && sudo apt install git-lfs
        elif command -v yum &> /dev/null; then
            sudo yum install git-lfs
        else
            log_error "无法自动安装Git LFS，请手动安装: https://git-lfs.github.io/"
            exit 1
        fi
    fi
    
    log_success "Git LFS已安装: $(git lfs version)"
}

# 初始化Git仓库
init_git_repo() {
    log_info "初始化Git仓库..."
    
    if [ -d ".git" ]; then
        log_warning "Git仓库已存在，跳过初始化"
    else
        git init
        log_success "Git仓库初始化完成"
    fi
}

# 配置Git LFS
setup_git_lfs() {
    log_info "配置Git LFS..."
    
    # 安装Git LFS钩子
    git lfs install
    
    # 验证.gitattributes文件存在
    if [ ! -f ".gitattributes" ]; then
        log_error ".gitattributes文件不存在，请先运行项目组织脚本"
        exit 1
    fi
    
    log_success "Git LFS配置完成"
}

# 配置Git用户信息
configure_git_user() {
    log_info "配置Git用户信息..."
    
    # 检查是否已配置用户信息
    if ! git config user.name &> /dev/null; then
        read -p "请输入Git用户名: " git_username
        git config user.name "$git_username"
    fi
    
    if ! git config user.email &> /dev/null; then
        read -p "请输入Git邮箱: " git_email
        git config user.email "$git_email"
    fi
    
    log_success "Git用户信息配置完成"
    log_info "用户名: $(git config user.name)"
    log_info "邮箱: $(git config user.email)"
}

# 添加远程仓库
add_remote_origin() {
    log_info "配置远程仓库..."
    
    # 检查是否已配置远程仓库
    if git remote get-url origin &> /dev/null; then
        log_warning "远程仓库已配置: $(git remote get-url origin)"
        read -p "是否要更新远程仓库地址? (y/N): " update_remote
        if [[ "$update_remote" =~ ^[Yy]$ ]]; then
            git remote remove origin
        else
            return
        fi
    fi
    
    # 获取GitHub仓库地址
    echo "请选择远程仓库地址格式:"
    echo "1. HTTPS (推荐): https://github.com/CKEN/VisionAI-ClipsMaster.git"
    echo "2. SSH: git@github.com:CKEN/VisionAI-ClipsMaster.git"
    read -p "请选择 (1/2): " repo_format
    
    case $repo_format in
        1)
            remote_url="https://github.com/CKEN/VisionAI-ClipsMaster.git"
            ;;
        2)
            remote_url="git@github.com:CKEN/VisionAI-ClipsMaster.git"
            ;;
        *)
            log_error "无效选择"
            exit 1
            ;;
    esac
    
    git remote add origin "$remote_url"
    log_success "远程仓库配置完成: $remote_url"
}

# 创建初始提交
create_initial_commit() {
    log_info "创建初始提交..."
    
    # 检查是否有未提交的更改
    if git diff --cached --quiet && git diff --quiet; then
        log_info "添加所有文件到暂存区..."
        git add .
    fi
    
    # 检查是否有文件在暂存区
    if git diff --cached --quiet; then
        log_warning "没有文件需要提交"
        return
    fi
    
    # 创建符合conventional commits规范的提交信息
    commit_message="feat: initial release of VisionAI-ClipsMaster v1.0.0

🎬 AI-powered short drama intelligent remixing tool

Features:
- 🤖 Dual-model architecture (Mistral-7B + Qwen2.5-7B)
- 🎯 Intelligent screenplay reconstruction with AI analysis
- ⚡ Precise video splicing based on new subtitle timecodes
- 💾 4GB memory optimization with quantization support
- 🚀 Pure CPU inference, no GPU required
- 📤 JianYing project file export
- 🌍 Cross-platform support (Windows/Linux/macOS)
- 🐳 Docker containerization with lite and full versions

Technical Highlights:
- Threading-based concurrency for Python 3.8+ compatibility
- Automatic language detection and model switching
- Memory usage monitoring and optimization
- Comprehensive installation automation
- 30-minute setup from clone to first run

Documentation:
- Complete user guide and API documentation
- Developer contribution guidelines
- Docker deployment instructions
- Troubleshooting and FAQ
- Project roadmap and future plans

Breaking Changes: N/A (initial release)

BREAKING CHANGE: This is the initial release"
    
    git commit -m "$commit_message"
    log_success "初始提交创建完成"
}

# 推送到远程仓库
push_to_remote() {
    log_info "推送代码到远程仓库..."
    
    # 设置默认分支为main
    git branch -M main
    
    # 推送代码
    if git push -u origin main; then
        log_success "代码推送成功"
    else
        log_error "代码推送失败，请检查网络连接和仓库权限"
        exit 1
    fi
}

# 创建并推送标签
create_and_push_tag() {
    log_info "创建版本标签..."
    
    tag_name="v1.0.0"
    tag_message="Release v1.0.0: Initial stable release

🎉 VisionAI-ClipsMaster首个稳定版本发布

## ✨ 核心特性
- 🤖 双模型架构: Mistral-7B(英文) + Qwen2.5-7B(中文)
- 🎯 智能剧本重构: AI分析剧情并重新编排
- ⚡ 精准视频拼接: 零损失视频切割拼接
- 💾 4GB内存兼容: 专为低配设备优化
- 🚀 纯CPU推理: 无需GPU，普通电脑即可运行
- 📤 剪映工程导出: 生成可二次编辑的工程文件

## 🚀 快速开始
- 一键安装脚本支持Windows/Linux/macOS
- Docker部署支持轻量版和完整版
- 30分钟内完成从安装到首次使用

## 📊 性能指标
- 4GB设备: 8-12分钟处理30分钟视频
- 8GB设备: 5-8分钟处理30分钟视频
- 内存峰值: 3.2GB-5.1GB (根据量化级别)

## 🌍 兼容性
- Python 3.8+
- Windows 10+, Ubuntu 18.04+, macOS 10.15+
- 支持Q2_K, Q4_K_M, Q5_K量化级别

## 📚 文档
- 完整的用户指南和API文档
- 开发者贡献指南
- Docker部署说明
- 故障排除和FAQ

This release marks the first stable version of VisionAI-ClipsMaster,
providing a complete AI-powered video remixing solution for content creators."
    
    git tag -a "$tag_name" -m "$tag_message"
    git push origin "$tag_name"
    
    log_success "版本标签 $tag_name 创建并推送完成"
}

# 验证仓库状态
verify_repository() {
    log_info "验证仓库状态..."
    
    # 检查远程仓库连接
    if git ls-remote origin &> /dev/null; then
        log_success "远程仓库连接正常"
    else
        log_error "无法连接到远程仓库"
        exit 1
    fi
    
    # 显示仓库信息
    echo
    echo "📊 仓库信息:"
    echo "  远程地址: $(git remote get-url origin)"
    echo "  当前分支: $(git branch --show-current)"
    echo "  最新提交: $(git log --oneline -1)"
    echo "  标签列表: $(git tag -l)"
    echo
}

# 主函数
main() {
    echo "🚀 VisionAI-ClipsMaster Git初始化和配置"
    echo "=" * 60
    
    # 检查前置条件
    check_git
    check_git_lfs
    
    # Git仓库初始化
    init_git_repo
    setup_git_lfs
    configure_git_user
    add_remote_origin
    
    # 代码提交和推送
    create_initial_commit
    push_to_remote
    create_and_push_tag
    
    # 验证结果
    verify_repository
    
    echo "=" * 60
    log_success "Git配置完成！"
    echo
    echo "🎯 下一步操作:"
    echo "1. 访问GitHub仓库查看代码"
    echo "2. 配置GitHub仓库设置"
    echo "3. 启用GitHub Actions"
    echo "4. 创建GitHub Release"
    echo "5. 设置社区功能"
    echo
    echo "🔗 GitHub仓库地址:"
    echo "   $(git remote get-url origin | sed 's/\.git$//')"
}

# 错误处理
trap 'log_error "脚本执行失败，请检查错误信息"' ERR

# 运行主函数
main "$@"
