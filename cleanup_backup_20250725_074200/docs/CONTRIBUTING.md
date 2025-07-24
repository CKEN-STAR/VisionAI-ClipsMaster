# 贡献指南

感谢您对 VisionAI-ClipsMaster 项目的关注！我们欢迎各种形式的贡献，包括但不限于代码贡献、文档改进、bug报告和功能建议。

## 开发环境设置

1. Fork 并克隆项目：
```bash
git clone https://github.com/YOUR-USERNAME/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. 安装开发依赖：
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. 安装pre-commit钩子：
```bash
pre-commit install
```

## 代码规范

我们使用以下工具确保代码质量：

- **Black**: 代码格式化
- **isort**: 导入语句排序
- **flake8**: 代码风格检查
- **mypy**: 类型检查

请确保您的代码通过所有这些检查。您可以运行：
```bash
# 格式化代码
black .
isort .

# 运行检查
flake8 .
mypy .
```

## 提交规范

提交信息应遵循以下格式：
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）包括：
- feat: 新功能
- fix: 修复bug
- docs: 文档更改
- style: 格式化修改
- refactor: 代码重构
- test: 添加测试
- chore: 构建过程或辅助工具的变动

示例：
```
feat(validator): 添加视频帧率检测功能

- 实现帧率检测算法
- 添加相关单元测试
- 更新文档

Closes #123
```

## 测试规范

1. 所有新功能必须包含测试
2. 所有测试必须通过
3. 测试覆盖率不得降低

运行测试：
```bash
pytest tests -v
```

## Pull Request流程

1. 确保您的代码与主分支同步
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -am 'feat: add some feature'`
4. 推送到您的fork：`git push origin feature/your-feature`
5. 提交Pull Request

## Pull Request检查清单

- [ ] 代码符合项目规范
- [ ] 添加/更新了相关测试
- [ ] 更新了相关文档
- [ ] 所有CI检查通过
- [ ] 提交信息符合规范

## 文档贡献

1. 文档使用Markdown格式
2. 位于`docs/`目录下
3. 使用清晰的章节结构
4. 包含适当的代码示例

## Bug报告

提交bug报告时，请包含：

1. 问题描述
2. 复现步骤
3. 期望行为
4. 实际行为
5. 环境信息
   - Python版本
   - 操作系统
   - 相关依赖版本

## 功能请求

提交功能请求时，请说明：

1. 用例场景
2. 解决的问题
3. 建议的实现方案

## 行为准则

请参阅我们的[行为准则](CODE_OF_CONDUCT.md)。

## 许可

通过贡献代码，您同意您的贡献将在MIT许可下发布。

## 联系方式

如有任何问题，请通过以下方式联系我们：

- 提交Issue
- 发送邮件至：support@visionai.com

感谢您的贡献！ 