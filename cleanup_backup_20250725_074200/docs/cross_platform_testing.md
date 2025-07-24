# VisionAI-ClipsMaster 跨平台测试文档

## 概述

VisionAI-ClipsMaster 的跨平台测试系统用于确保应用程序在不同操作系统（Windows、Linux 和 macOS）上的兼容性。该测试系统验证了关键组件在不同平台上的行为一致性，包括文件路径处理、库加载、环境检测等。

## 测试组件

跨平台测试系统由以下组件组成：

1. **平台工具库** (`platform_utils.py`): 提供跨平台操作的通用工具函数，如库加载、路径处理等。
2. **跨平台测试模块** (`cross_platform_test.py`): 包含针对不同平台特性的单元测试。
3. **测试运行器** (`run_cross_platform_tests.py`): 用于在不同环境中运行测试，包括本地测试和Docker容器测试。
4. **平台特定脚本**:
   - `run_cross_platform_tests.bat` (Windows)
   - `run_cross_platform_tests.sh` (Linux/macOS)
5. **Docker 测试环境** (`Dockerfile`): 用于在容器中模拟不同平台环境。

## 测试内容

跨平台测试涵盖以下方面：

1. **本地库加载**: 测试在不同平台上加载动态链接库的能力。
2. **平台特定路径处理**: 验证路径分隔符和临时目录的正确处理。
3. **环境检测**: 确保环境检测功能在不同平台上正确工作。
4. **操作系统兼容性**: 验证应用程序对不同操作系统版本的支持。
5. **资源管理**: 测试内存和磁盘资源的跨平台监控。
6. **文件操作**: 验证文件创建、读写和删除的跨平台兼容性。

## 运行测试

### Windows

在 Windows 上运行测试：

```batch
tests\device_compatibility\run_cross_platform_tests.bat
```

安装测试依赖：

```batch
tests\device_compatibility\run_cross_platform_tests.bat --install-deps
```

### Linux/macOS

在 Linux 或 macOS 上运行测试：

```bash
./tests/device_compatibility/run_cross_platform_tests.sh
```

安装测试依赖：

```bash
./tests/device_compatibility/run_cross_platform_tests.sh --install-deps
```

### 使用 Docker 进行测试

使用 Docker 在不同平台环境中运行测试：

```bash
python tests/device_compatibility/run_cross_platform_tests.py --mode docker --platforms all
```

## 测试报告生成

生成详细的测试报告：

```bash
python tests/device_compatibility/run_cross_platform_tests.py --report
```

报告将保存在 `test_output/cross_platform_report.md` 文件中。

## 扩展测试

要添加新的跨平台测试，请按照以下步骤操作：

1. 在 `TestPlatformCompatibility` 类中添加新的测试方法。
2. 确保测试方法使用适当的 mock 对象来模拟平台特定行为。
3. 使用 `self.subTest` 来测试多个平台场景。
4. 更新文档以反映新的测试内容。

## 已知限制

1. 某些平台特定功能（如内存探针）可能需要平台特定的编译工具。
2. Docker 测试环境不支持完全模拟 macOS，只能测试基本兼容性。
3. 某些硬件相关功能可能无法在虚拟环境中完全测试。

## 故障排除

如果测试失败，请检查以下几点：

1. 确保已安装所有必要的依赖项。
2. 检查平台特定的路径和库名称是否正确。
3. 在 Docker 测试中，确保 Docker 服务正在运行。
4. 检查日志文件以获取详细的错误信息。 