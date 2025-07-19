# VisionAI-ClipsMaster 测试安全指南

本文档描述了 VisionAI-ClipsMaster 项目的测试安全措施，包括权限加固、完整性验证和最佳实践。

## 测试权限加固概述

为确保测试的可靠性和数据的安全性，VisionAI-ClipsMaster 项目实施了严格的测试权限加固措施。主要目标是：

1. **保护黄金样本（Golden Samples）**：防止参考数据被意外修改，确保测试基准的一致性
2. **隔离测试输出**：确保测试输出不会影响其他测试，并允许适当的清理
3. **防止意外修改**：通过权限控制防止测试数据的意外更改
4. **跨平台一致性**：确保在 Windows、Linux 和 macOS 上具有一致的行为

## 目录权限规则

| 目录               | Linux 权限 | Windows 属性 | 说明                             |
|-------------------|------------|-------------|----------------------------------|
| tests/golden_samples | 550 (r-xr-x---) | 只读        | 包含基准测试数据，只允许读取和执行   |
| tests/tmp_output    | 750 (rwxr-x---) | 普通        | 测试输出目录，允许写入新的测试结果   |
| tests/data          | 550 (r-xr-x---) | 只读        | 测试数据目录，只允许读取和执行       |

## 使用权限加固工具

项目提供了权限加固工具，可确保测试目录具有正确的权限设置：

### 验证权限

```bash
# Linux/macOS
./scripts/secure_tests.sh --check

# Windows
scripts\secure_tests.bat --check
```

### 修复权限

```bash
# Linux/macOS
./scripts/secure_tests.sh --fix

# Windows
scripts\secure_tests.bat --fix
```

### 自动加固

在持续集成环境中，权限加固作为测试前的准备步骤自动执行：

```yaml
- name: 设置测试权限
  run: python scripts/secure_test_permissions.py --fix
```

## 测试完整性验证

除了权限控制外，VisionAI-ClipsMaster 还实施了测试完整性验证机制：

1. **索引验证**：每个黄金样本目录都包含一个 `index.json` 文件，记录了所有样本的元数据
2. **哈希验证**：测试文件的哈希值存储在 `hashes` 子目录中，用于验证文件是否被修改
3. **自动验证**：测试运行前会自动验证黄金样本的完整性

## 添加新的黄金样本

添加新的黄金样本需要特殊权限，并遵循以下流程：

1. 使用专用脚本生成新的黄金样本：

   ```bash
   python tests/golden_samples/generate_samples.py --new "测试场景描述"
   ```

2. 生成的样本将被放入临时目录，等待审查
3. 审查后，使用管理员权限将其添加到黄金样本库中：

   ```bash
   # Linux/macOS (需要 sudo 权限)
   sudo python tests/golden_samples/run_golden_sample_generation.py --promote /path/to/temp/sample
   
   # Windows (需要管理员权限)
   python tests/golden_samples/run_golden_sample_generation.py --promote /path/to/temp/sample
   ```

4. 自动更新索引和哈希值

## 测试安全最佳实践

为确保测试的安全性和可靠性，请遵循以下最佳实践：

1. **永不手动修改黄金样本**：始终使用提供的工具添加或更新黄金样本
2. **定期验证测试完整性**：在重要测试之前运行完整性检查
3. **遵循最小权限原则**：不要给予测试目录不必要的写入权限
4. **不要忽略权限警告**：如果权限验证失败，立即修复
5. **集成到 CI/CD 流程**：在持续集成流程中包含权限和完整性检查

## 故障排除

### Q: 权限验证失败怎么办？

A: 运行修复命令：`python scripts/secure_test_permissions.py --fix`。如果仍然失败，检查是否有足够的权限执行此操作。

### Q: 在 Windows 上修改权限需要管理员权限吗？

A: 对于某些系统文件夹可能需要管理员权限。如果修复失败，请尝试以管理员身份运行命令提示符，然后重新运行脚本。

### Q: 如何取消文件的只读属性进行临时修改？

A: 不建议修改受保护的文件。如需修改黄金样本，请遵循"添加新的黄金样本"部分描述的流程。

### Q: 测试完整性检查失败，但我没有修改任何文件？

A: 可能是由于文件系统编码或行尾符号变化导致。在 Windows 和 Linux/macOS 之间切换时尤其常见。运行 `python tests/golden_samples/run_golden_sample_generation.py --rehash` 重新生成哈希值。 