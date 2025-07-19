# VisionAI-ClipsMaster 用户协议合规检查工具

## 功能概述

用户协议合规检查工具是VisionAI-ClipsMaster项目的重要组成部分，用于验证用户协议(EULA)文档是否包含所有必要条款，并符合相关法律法规要求。

主要功能包括：

1. **关键条款检查**：验证EULA是否包含所有必需的关键条款
2. **法规合规性验证**：检查EULA是否符合相关法律法规，包括：
   - GDPR第17条（被遗忘权）
   - 中国《生成式AI服务管理暂行办法》第12条
3. **自动生成合规性报告**：生成多种格式的合规性报告（MD, JSON, TXT, HTML）
4. **集成到CI/CD流程**：可集成到持续集成流程中，自动验证EULA更新是否合规

## 组件构成

本工具包含以下主要组件：

1. `eula_checker.py`：核心检查引擎，实现条款验证和法规检查
2. `run_eula_compliance_check.py`：命令行工具，用于运行检查并生成报告
3. `docs/EULA.md`：项目用户协议文档

## 必需条款

VisionAI-ClipsMaster的EULA必须包含以下关键条款：

| 条款ID | 描述 | 必需 |
|--------|------|------|
| ownership | 用户保留原始内容所有权 | 是 |
| ai_ethics | 禁止生成非法或侵权内容 | 是 |
| data_retention | 原始素材处理后立即删除 | 是 |
| right_to_erasure | 用户有权要求删除个人数据（被遗忘权） | 是 |
| cn_ai_management | 符合中国《生成式AI服务管理暂行办法》的要求 | 是 |
| user_responsibility | 定义用户使用服务时的责任义务 | 否 |

## 法规合规性

工具会检查EULA是否符合以下法规要求：

### GDPR (一般数据保护条例)

- 第17条：被遗忘权（删除权）
  - 数据主体有权要求数据控制者删除与其相关的个人数据
  - 相关条款：right_to_erasure, data_retention

### 中国《生成式AI服务管理暂行办法》

- 第12条：服务提供者责任
  - 生成式AI服务提供者应当落实算法安全主体责任，建立健全管理制度和技术措施
  - 相关条款：cn_ai_management, ai_ethics

## 使用方法

### 基本使用

```bash
# 使用默认选项运行检查
python tests/legal_test/run_eula_compliance_check.py

# 指定EULA文件路径
python tests/legal_test/run_eula_compliance_check.py --eula path/to/eula.md

# 指定输出目录
python tests/legal_test/run_eula_compliance_check.py --output-dir reports/eula

# 生成所有格式的报告
python tests/legal_test/run_eula_compliance_check.py --formats md,json,txt,html

# 仅验证EULA是否符合基本要求
python tests/legal_test/run_eula_compliance_check.py --validate-only

# 显示详细日志
python tests/legal_test/run_eula_compliance_check.py --verbose
```

### 编程接口

```python
from tests.legal_test.eula_checker import EULACompliance

# 创建检查器
checker = EULACompliance()

# 验证EULA
results = checker.validate_eula_compliance(eula_path="docs/EULA.md")

# 检查结果
if results["success"]:
    print("EULA合规")
else:
    print("EULA不合规，缺少以下条款:")
    for missing in results["missing_required"]:
        print(f"- {missing['name']}: {missing['description']}")

# 生成报告
report = checker.generate_report()
print(report)
```

## 集成到CI/CD流程

可以将此工具集成到CI/CD流程中，在每次EULA更新后自动验证其合规性：

```yaml
# .github/workflows/eula-compliance.yml 示例
name: EULA Compliance Check

on:
  push:
    paths:
      - 'docs/EULA.md'

jobs:
  check-eula:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run EULA compliance check
        run: python tests/legal_test/run_eula_compliance_check.py --formats md,json
      - name: Upload compliance report
        uses: actions/upload-artifact@v2
        with:
          name: eula-compliance-report
          path: tests/legal_test/reports/
```

## 输出示例

### Markdown报告

```markdown
# VisionAI-ClipsMaster EULA合规性报告

## 总体合规状态
合规状态: 通过

## 条款检查结果
- [✓] ownership (必需): 用户保留原始内容所有权
- [✓] ai_ethics (必需): 禁止生成非法或侵权内容
- [✓] data_retention (必需): 原始素材处理后立即删除
- [✓] right_to_erasure (必需): 用户有权要求删除个人数据（被遗忘权）
- [✓] cn_ai_management (必需): 符合中国《生成式AI服务管理暂行办法》的要求
- [✓] user_responsibility (可选): 定义用户使用服务时的责任义务

## 法规合规性检查

### GDPR (一般数据保护条例)
- [✓] article_17: 被遗忘权（删除权）
  数据主体有权要求数据控制者删除与其相关的个人数据

### 中国《生成式AI服务管理暂行办法》
- [✓] article_12: 服务提供者责任
  生成式AI服务提供者应当落实算法安全主体责任，建立健全管理制度和技术措施
```

## 维护与扩展

### 添加新的必需条款

修改`eula_checker.py`中的`_init_clauses`方法：

```python
# 添加新条款
clauses["new_clause"] = EULAClause(
    name="new_clause",
    keywords=["关键词1", "关键词2", "关键词3"],
    description="新条款描述",
    required=True
)
```

### 添加新的法规检查

修改`eula_checker.py`中的`_init_regulations`方法：

```python
# 添加新法规
regulations["new_regulation"] = {
    "name": "新法规名称",
    "article_x": {
        "title": "条款标题",
        "description": "条款描述",
        "clauses": ["related_clause1", "related_clause2"]
    }
}
```

## 性能考虑

本工具对EULA文档的检查基于关键词匹配，其复杂度与EULA文档大小和条款数量呈线性关系，适用于定期验证和CI/CD流程。 