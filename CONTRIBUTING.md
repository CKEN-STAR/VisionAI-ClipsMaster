# 贡献指南

感谢您对 VisionAI-ClipsMaster 项目的关注！我们欢迎各种形式的贡献。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request流程](#pull-request流程)

---

## 行为准则

请阅读并遵守我们的行为准则，确保社区友好、包容。

- 尊重所有贡献者
- 使用友好、专业的语言
- 接受建设性的批评
- 关注项目和社区的最佳利益

---

## 如何贡献

### 报告Bug

1. 在提交Bug前，请先搜索现有Issue
2. 使用Bug报告模板创建Issue
3. 提供详细的复现步骤
4. 附上错误日志和截图

### 功能建议

1. 在提交建议前，请先搜索现有Issue
2. 使用功能请求模板创建Issue
3. 清晰描述功能需求和使用场景
4. 说明该功能的价值

### 代码贡献

1. Fork项目仓库
2. 创建特性分支
3. 编写代码和测试
4. 提交Pull Request

---

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 3. 安装依赖

```bash
# 安装运行依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-qt black flake8
```

### 4. 运行测试

```bash
pytest test/
```

---

## 代码规范

### Python代码风格

- 遵循 PEP 8 规范
- 使用 Black 格式化代码
- 使用 flake8 进行代码检查
- 最大行长度: 120字符

### 命名规范

```python
# 类名: PascalCase
class CloudAIEngine:
    pass

# 函数和变量: snake_case
def generate_viral_subtitle():
    subtitle_text = ""

# 常量: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# 私有成员: 前缀下划线
def _internal_method():
    pass
```

### 文档字符串

```python
def process_subtitle(subtitle: str, language: str = "zh") -> Dict[str, Any]:
    """
    处理字幕文本
    
    Args:
        subtitle: 原始字幕文本
        language: 语言代码，默认"zh"
        
    Returns:
        处理后的字幕数据字典
        
    Raises:
        ValueError: 当字幕格式无效时
    """
    pass
```

### 类型注解

```python
from typing import List, Dict, Optional, Any

def analyze_emotion(
    text: str,
    threshold: float = 0.5
) -> Optional[Dict[str, Any]]:
    pass
```

---

## 提交规范

### Commit Message格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug修复 |
| docs | 文档更新 |
| style | 代码格式（不影响功能） |
| refactor | 重构（不是新功能或修复） |
| perf | 性能优化 |
| test | 测试相关 |
| chore | 构建/工具相关 |

### 示例

```
feat(cloud): 添加硅基流动平台支持

- 实现SiliconFlowProvider类
- 添加API连接测试功能
- 支持Qwen3和DeepSeek模型

Closes #123
```

---

## Pull Request流程

### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 开发和测试

```bash
# 编写代码
# 运行测试
pytest test/

# 格式化代码
black src/

# 代码检查
flake8 src/
```

### 3. 提交更改

```bash
git add .
git commit -m "feat(module): 添加新功能"
```

### 4. 推送分支

```bash
git push origin feature/your-feature-name
```

### 5. 创建Pull Request

1. 在GitHub上创建Pull Request
2. 填写PR模板
3. 等待代码审查
4. 根据反馈修改代码
5. 合并到主分支

### PR检查清单

- [ ] 代码符合项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 所有测试通过
- [ ] 没有引入新的警告

---

## 问题反馈

如有任何问题，请通过以下方式联系：

- 创建GitHub Issue
- 发送邮件至项目维护者

感谢您的贡献！🎉
