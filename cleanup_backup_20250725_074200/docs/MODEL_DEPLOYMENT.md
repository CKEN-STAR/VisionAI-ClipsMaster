# 模型部署指南

本文档详细说明了如何部署和管理VisionAI-ClipsMaster系统中的模型。

## 目录结构

```
models/
├── qwen/                    # 中文模型
│   ├── base/               # 基础模型文件
│   ├── quantized/          # 量化版本
│   │   └── Q4_K_M/        # 4-bit量化版本
│   └── active_config.json  # 当前激活配置
└── mistral/                # 英文模型
    ├── base/               # 基础模型文件
    ├── quantized/          # 量化版本
    │   └── Q4_K_M/        # 4-bit量化版本
    └── active_config.json  # 当前激活配置
```

## 模型更新流程

1. 下载新模型到对应的`base/`目录
2. 执行量化转换:
   ```bash
   make quantize MODEL=模型名称
   ```
3. 更新校验和文件:
   ```bash
   python tools/generate_checksums.py --model 模型名称
   ```
4. 更新激活配置:
   ```bash
   python tools/update_active_model.py --model 模型名称 --version 量化版本
   ```

## 模型验证

在部署新模型后，请运行验证脚本确保模型完整性:

```bash
python tools/verify_model.py --model 模型名称
```

验证内容包括:
- 文件完整性检查
- 元数据验证
- 校验和验证
- 内存需求验证
- 量化版本验证

## 系统要求

- 最小内存要求: 8GB RAM
- 推荐内存配置: 16GB RAM
- 磁盘空间: 每个模型约需要10GB

## 故障排除

### 常见问题

1. 模型加载失败
   - 检查文件完整性
   - 验证内存是否充足
   - 确认量化版本是否正确

2. 性能问题
   - 考虑使用更高级别的量化版本
   - 检查系统资源使用情况
   - 优化批处理大小

### 日志位置

- 系统日志: `logs/system.log`
- 模型日志: `logs/models/`
- 量化日志: `logs/quantization/`

## 安全注意事项

1. 权限控制
   - 限制模型目录的访问权限
   - 使用加密传输进行模型下载
   - 定期更新校验和

2. 备份策略
   - 定期备份模型配置
   - 保留上一个稳定版本
   - 使用版本控制管理配置文件

## 维护计划

1. 定期检查
   - 每周验证模型完整性
   - 监控系统资源使用
   - 检查日志异常

2. 更新策略
   - 按需更新量化版本
   - 定期评估模型性能
   - 及时应用安全补丁

## 联系支持

如遇到问题，请联系:
- 技术支持: support@example.com
- 问题报告: issues@example.com

## 版本历史

- v1.0.0 (2024-04-25)
  - 初始版本
  - 支持中文和英文模型
  - 实现基本的模型管理功能 