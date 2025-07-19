# VisionAI-ClipsMaster CI/CD 流水线

本文档描述了 VisionAI-ClipsMaster 项目的持续集成和持续部署 (CI/CD) 流水线配置及使用指南。

## 概述

VisionAI-ClipsMaster 使用 GitHub Actions 实现自动化的构建、测试和部署流程。流水线包括以下主要组件：

- **持续集成 (CI)**: 自动执行代码检查、测试和构建
- **持续部署 (CD)**: 自动部署到各种环境
- **文档自动生成**: 更新并发布项目文档
- **翻译工作流**: 自动翻译项目文档

## 持续集成工作流

CI 工作流文件位于 `.github/workflows/ci.yml`，在以下情况下触发：

- 推送到 `main` 或 `develop` 分支
- 向 `main` 或 `develop` 分支提交拉取请求
- 手动触发

### CI 工作流组件

CI 工作流包含以下主要任务：

#### 1. 测试 (test)

- 在多个 Python 版本（3.8, 3.9, 3.10）上运行测试
- 测试与多个剪映版本的兼容性
- 运行单元测试和集成测试
- 生成测试覆盖率报告

```yaml
# 测试任务配置示例
test:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ["3.8", "3.9", "3.10"]
      jianying: ["3.0.0", "2.9.5"]  # 剪映版本兼容性测试
```

#### 2. 代码质量检查 (lint)

- 使用 Black 检查代码格式
- 使用 isort 检查导入排序
- 使用 flake8 进行语法和风格检查

#### 3. 覆盖率分析 (coverage-analysis)

- 分析测试覆盖率
- 生成覆盖率徽章
- 上传详细报告

#### 4. 集成测试 (integration-test)

- 设置测试环境
- 下载测试用小型模型
- 测试核心功能
- 验证应用能否正常启动

#### 5. 依赖检查 (dependency-check)

- 检查依赖项的安全漏洞
- 使用 safety 和 pip-audit 进行审计

#### 6. 安全扫描 (security)

- 使用 Bandit 进行安全代码扫描
- 检查已知的安全漏洞

#### 7. Docker 镜像构建 (docker)

- 构建多平台 Docker 镜像（amd64, arm64）
- 推送到 DockerHub
- 仅在成功测试后推送

#### 8. 文档生成 (docs)

- 使用 Sphinx 构建文档
- 部署到 GitHub Pages

## 部署工作流

部署工作流文件位于 `.github/workflows/deploy.yml`，在以下情况下触发：

- 推送带有版本标签的提交（以 'v' 开头）
- 手动触发

### 部署工作流组件

部署工作流包含以下主要任务：

#### 1. 构建软件包 (build-package)

- 提取版本号
- 构建 Python 包
- 创建发布包

#### 2. 创建发布 (create-release)

- 创建 GitHub 发布
- 上传构建的软件包

#### 3. 构建 Docker 镜像 (build-docker)

- 构建带有版本标签的 Docker 镜像
- 推送到 DockerHub

## 翻译工作流

翻译工作流文件位于 `.github/workflows/translate-docs.yml`，负责文档的多语言支持。

## 如何使用

### 运行 CI 测试

CI 测试会在推送代码或创建拉取请求时自动运行。你也可以手动触发：

1. 访问项目的 GitHub 仓库
2. 点击 "Actions" 标签
3. 从左侧选择 "VisionAI-ClipsMaster CI"
4. 点击 "Run workflow" 按钮

### 创建新版本发布

要创建新的版本发布：

1. 确保主分支代码已经通过所有测试
2. 创建并推送一个新的标签，例如：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. 部署工作流将自动构建软件包并创建发布

### 本地运行测试

在提交代码前在本地运行测试：

```bash
# 运行单元测试
pytest tests/unit/

# 运行带覆盖率报告的测试
pytest --cov=src tests/

# 运行代码质量检查
black --check src/ tests/
isort --check src/ tests/
flake8 src/ tests/
```

## CI/CD 监控

可以在以下位置查看构建状态：

- GitHub 仓库的 "Actions" 标签页
- 拉取请求中的自动状态检查
- README 中的构建状态徽章

## 最佳实践

1. **频繁提交并运行测试**：小批量、频繁地提交代码，及早发现问题。

2. **编写全面的测试**：确保高测试覆盖率，特别是核心功能。

3. **关注安全扫描**：及时修复安全扫描中发现的漏洞。

4. **保持依赖更新**：定期更新依赖项，减少安全风险。

5. **遵循代码风格**：遵循项目的代码风格指南，使 CI 检查顺利通过。

## 故障排除

### Q: CI 测试失败怎么办？

A: 检查 GitHub Actions 日志，找出失败的具体测试。本地复现问题，修复后再提交。

### Q: Docker 镜像构建失败？

A: 检查 Dockerfile 配置和依赖项。确保所有必要的文件都包含在构建上下文中。

### Q: 如何调试 CI 环境中的问题？

A: 添加调试输出，使用 `actions/setup-node@v2` 的 `debug: true` 选项，或添加环境变量 `ACTIONS_RUNNER_DEBUG: true`。

### Q: 版本标签推送后没有触发部署？

A: 确保标签格式正确（以 'v' 开头），并且拥有必要的权限。查看 GitHub Actions 日志以获取更详细信息。 