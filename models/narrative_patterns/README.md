# 叙事模式库

叙事模式库包含用于短视频创作的叙事模式模型和配置。该库支持版本化管理，不同版本的模式库可以独立存在并易于切换。

## 目录结构

- `v1.0/`: 初始版本的模式库
- `v1.1/`: 改进版的模式库（增加了平台支持和新模式类型）
- `latest/`: 指向当前使用版本的链接/复制

## 版本内容

每个版本目录包含以下文件：

- `metadata.json`: 版本元数据，包含版本信息、创建日期、数据统计等
- `pattern_config.yaml`: 模式配置文件，定义模式类型、参数、评估标准等
- `fp-growth.model`: 模式挖掘模型（示例）

## 版本管理

通过版本管理系统，可以轻松创建新版本、比较版本差异和切换当前版本。详细使用方法请参阅 `src/version_management/README.md`。

基本用法示例：

```python
# 切换版本
from src.utils.pattern_loader import switch_pattern_version
switch_pattern_version("v1.1")

# 获取当前版本配置
from src.utils.pattern_loader import get_current_pattern_config
config = get_current_pattern_config()
```

## 版本特性

### v1.0（基础版）

- 6种基本模式类型：opening, climax, transition, conflict, resolution, ending
- 支持平台：抖音、快手、YouTube
- 基础评估权重和阈值配置

### v1.1（改进版）

- 新增模式类型：surprise
- 调整了评估权重，增强了情感强度和社交传播的重要性
- 新增平台支持：哔哩哔哩
- 优化了语言覆盖率

## 模式类型说明

主要的模式类型及其特点：

- **opening**：开场模式，位于视频开始部分，引起观众注意
- **climax**：高潮模式，位于视频中后段，情感强度最高
- **transition**：转场/过渡模式，连接视频不同部分
- **conflict**：冲突模式，创造紧张感和悬念
- **resolution**：解决模式，解决冲突，释放情感
- **ending**：结尾模式，收尾并提供满足感
- **surprise**：惊喜模式，制造意外转折（v1.1新增）

## 推荐模式组合

配置中包含多种推荐的模式组合，以适应不同类型的内容创作：

1. **标准叙事结构**：opening → conflict → climax → resolution → ending
2. **悬疑结构**：opening → transition → climax → ending
3. **情感冲击波**：opening → climax → conflict → resolution → ending
4. **循环递进式**：opening → conflict → transition → climax → ending 