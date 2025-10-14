# 🤝 贡献指南 | Contributing Guide

> **欢迎参与 VisionAI-ClipsMaster 项目！** 我们非常感谢您的贡献，无论是代码、文档、测试还是建议。

## 📋 目录

- [🚀 快速开始](#-快速开始)
- [🔧 开发环境设置](#-开发环境设置)
- [📝 提交规范](#-提交规范)
- [🎯 贡献方向](#-贡献方向)
- [🧪 测试指南](#-测试指南)
- [📚 文档贡献](#-文档贡献)
- [🐛 Bug报告](#-bug报告)
- [💡 功能建议](#-功能建议)
- [📞 获取帮助](#-获取帮助)

## 🚀 快速开始

### 1. Fork 仓库
```bash
# 1. 在GitHub上Fork仓库
# 2. 克隆您的Fork
git clone https://github.com/YOUR_USERNAME/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 3. 添加上游仓库
git remote add upstream https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
```

### 2. 创建功能分支
```bash
# 从main分支创建新分支
git checkout -b feature/your-feature-name

# 或者修复bug
git checkout -b fix/bug-description
```

### 3. 提交更改
```bash
# 添加更改
git add .

# 提交（遵循提交规范）
git commit -m "feat: 添加新的AI模型支持"

# 推送到您的Fork
git push origin feature/your-feature-name
```

### 4. 创建Pull Request
在GitHub上创建Pull Request，详细描述您的更改。

## 🔧 开发环境设置

### 系统要求
- **Python**: 3.11+ (推荐 3.13)
- **操作系统**: Windows 10/11, Linux, macOS
- **内存**: 4GB+ RAM (推荐 8GB+)
- **存储**: 2GB+ 可用空间

### 安装依赖
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements/requirements-dev.txt

# 安装测试依赖
pip install pytest pytest-cov black flake8 mypy
```

### 验证环境
```bash
# 运行基础测试
python -m pytest test/ -v

# 运行代码质量检查
black --check src/
flake8 src/
mypy src/
```

## 📝 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交类型

| 🏷️ 类型 | 📝 描述 | 🌰 示例 |
|---------|---------|---------|
| `feat` | 新功能 | `feat: 添加批量处理功能` |
| `fix` | Bug修复 | `fix: 修复内存泄漏问题` |
| `docs` | 文档更新 | `docs: 更新API文档` |
| `style` | 代码格式 | `style: 修复代码格式` |
| `refactor` | 重构 | `refactor: 优化模型加载逻辑` |
| `test` | 测试相关 | `test: 添加单元测试` |
| `chore` | 构建/工具 | `chore: 更新依赖版本` |

### 提交消息格式
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### 示例
```bash
feat(ai): 添加Qwen2.5-7B模型支持

- 实现中文剧本重构功能
- 添加模型量化支持
- 优化内存使用

Closes #123
```

## 🎯 贡献方向

### 🤖 AI模型优化
- **模型量化**: 减少内存占用
- **推理优化**: 提升处理速度
- **多语言支持**: 扩展语言覆盖
- **质量提升**: 改进生成效果

### 🎨 用户界面
- **响应式设计**: 适配不同屏幕
- **主题系统**: 深色/浅色主题
- **国际化**: 多语言界面
- **可访问性**: 无障碍支持

### ⚡ 性能优化
- **内存管理**: 减少内存使用
- **并发处理**: 提升处理效率
- **缓存策略**: 优化数据访问
- **硬件加速**: GPU/CPU优化

### 📚 文档完善
- **用户指南**: 使用教程
- **开发文档**: API参考
- **示例代码**: 实用示例
- **故障排除**: 问题解决

### 🧪 测试覆盖
- **单元测试**: 函数级测试
- **集成测试**: 模块协作测试
- **端到端测试**: 完整流程测试
- **性能测试**: 压力和稳定性测试

## 🧪 测试指南

### 运行测试
```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest test/test_core.py

# 运行带覆盖率的测试
python -m pytest --cov=src --cov-report=html

# 运行性能测试
python comprehensive_production_verification_test.py
```

### 编写测试
```python
import pytest
from src.core.model_switcher import ModelSwitcher

def test_model_switcher_initialization():
    """测试模型切换器初始化"""
    switcher = ModelSwitcher()
    assert switcher is not None
    assert switcher.current_model is None

def test_language_detection():
    """测试语言检测功能"""
    switcher = ModelSwitcher()
    
    # 测试中文检测
    result = switcher.detect_language("这是一个中文测试")
    assert result == "zh"
    
    # 测试英文检测
    result = switcher.detect_language("This is an English test")
    assert result == "en"
```

## 📚 文档贡献

### 文档类型
- **用户文档**: README.md, USAGE.md, FAQ.md
- **开发文档**: API_REFERENCE.md, DEVELOPMENT.md
- **部署文档**: INSTALLATION.md, DEPLOYMENT.md

### 文档规范
- 使用清晰的Markdown格式
- 包含代码示例和截图
- 保持内容的准确性和时效性
- 遵循项目的文档风格

### 文档测试
```bash
# 检查文档链接
python scripts/check_docs_links.py

# 生成文档
mkdocs build

# 本地预览
mkdocs serve
```

## 🐛 Bug报告

### 报告Bug前
1. 搜索现有Issues，避免重复报告
2. 确认使用的是最新版本
3. 准备详细的复现步骤

### Bug报告模板
```markdown
## 🐛 Bug描述
简要描述遇到的问题

## 🔄 复现步骤
1. 执行操作A
2. 点击按钮B
3. 观察到错误C

## 🎯 期望行为
描述期望的正确行为

## 📱 环境信息
- OS: Windows 11
- Python: 3.11.5
- VisionAI版本: v1.0.1
- GPU: NVIDIA RTX 3060

## 📎 附加信息
- 错误日志
- 截图
- 相关配置文件
```

## 💡 功能建议

### 建议新功能前
1. 检查是否已有相关Issue或讨论
2. 考虑功能的通用性和必要性
3. 评估实现的复杂度

### 功能建议模板
```markdown
## 🚀 功能描述
详细描述建议的新功能

## 🎯 使用场景
说明功能的具体使用场景

## 💡 解决方案
提出可能的实现方案

## 🔄 替代方案
描述其他可能的解决方案

## 📊 优先级
评估功能的重要性和紧急性
```

## 📞 获取帮助

### 支持渠道

| 🆘 渠道 | 📝 用途 | 🔗 链接 |
|---------|---------|---------|
| **GitHub Issues** | Bug报告和功能请求 | [Issues](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues) |
| **GitHub Discussions** | 使用问题和经验分享 | [Discussions](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/discussions) |
| **邮件联系** | 直接联系维护者 | [peresbreedanay7156@gmail.com](mailto:peresbreedanay7156@gmail.com) |

### 提问技巧
1. **清晰描述问题**: 提供足够的上下文信息
2. **包含环境信息**: 操作系统、Python版本等
3. **提供复现步骤**: 详细的操作步骤
4. **附加相关文件**: 日志、配置文件、截图等

## 🏆 贡献者认可

我们重视每一位贡献者的努力：

- **代码贡献者**: 在README中展示
- **文档贡献者**: 在文档中署名
- **测试贡献者**: 在测试报告中感谢
- **社区贡献者**: 在社区中表彰

## 📄 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](LICENSE) 下发布。

---

**感谢您对 VisionAI-ClipsMaster 的贡献！** 🎬✨

每一个贡献都让这个项目变得更好！
