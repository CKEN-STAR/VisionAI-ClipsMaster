# ❓ VisionAI-ClipsMaster 常见问题解答

> **故障排除和解决方案 - 快速解决使用中遇到的问题**

## 🚀 安装和启动问题

### Q1: 启动时提示"Python版本不兼容"
**问题**: 运行时显示Python版本过低的错误

**解决方案**:
```bash
# 检查当前Python版本
python --version

# 如果版本低于3.8，需要升级Python
# Windows: 从python.org下载最新版本
# Linux: sudo apt install python3.11
# macOS: brew install python@3.11

# 验证安装
python3.11 --version
```

### Q2: 启动时间超过10秒
**问题**: 程序启动非常缓慢

**解决方案**:
```bash
# 使用优化启动器
python optimized_quick_launcher.py

# 如果仍然慢，检查系统资源
# 1. 关闭不必要的后台程序
# 2. 清理临时文件
# 3. 重启计算机

# 运行性能诊断
python startup_benchmark.py
```

### Q3: 依赖安装失败
**问题**: pip install时出现错误

**解决方案**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用镜像源 (中国用户)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 分步安装依赖
pip install PyQt6>=6.4.0
pip install torch>=2.0.0
pip install transformers>=4.20.0

# 如果仍有问题，创建虚拟环境
python -m venv fresh_env
fresh_env\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Q4: FFmpeg未找到错误
**问题**: 启动时提示FFmpeg not found

**解决方案**:
```bash
# 方法1: 自动安装 (推荐)
# 启动程序时会自动下载安装

# 方法2: 手动安装
# Windows:
# 1. 下载FFmpeg: https://ffmpeg.org/download.html
# 2. 解压到 tools/ffmpeg/ 目录

# Linux:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# 验证安装
ffmpeg -version
```

## 🧠 AI模型问题

### Q5: 模型下载失败
**问题**: AI模型下载中断或失败

**解决方案**:
```bash
# 检查网络连接
ping huggingface.co

# 使用镜像源 (中国用户)
# 在设置中配置镜像源:
# https://hf-mirror.com
# https://hub.nuaa.cf

# 手动下载模型
python -c "
from src.core.enhanced_model_downloader import EnhancedModelDownloader
downloader = EnhancedModelDownloader()
downloader.download_model('qwen2.5-7b', use_mirror=True)
"

# 检查磁盘空间 (模型需要3-7GB)
df -h  # Linux/macOS
dir   # Windows
```

### Q6: 模型加载失败
**问题**: 模型下载完成但无法加载

**解决方案**:
```bash
# 检查模型文件完整性
python -c "
import os
model_dir = 'models/qwen2.5-7b-instruct-q5'
if os.path.exists(model_dir):
    files = os.listdir(model_dir)
    print(f'模型文件: {files}')
else:
    print('模型目录不存在')
"

# 重新下载模型
rm -rf models/qwen2.5-7b-instruct-q5  # 删除损坏的模型
python optimized_quick_launcher.py     # 重新启动并下载

# 检查内存是否足够
# Q5模型需要约4GB内存
# Q4模型需要约3GB内存
# Q8模型需要约6GB内存
```

### Q7: AI重构结果不理想
**问题**: 生成的字幕质量不好

**解决方案**:
```bash
# 1. 调整重构参数
# 在界面中设置:
# - 重构强度: 0.6-0.8 (适中)
# - 保留原意: 70-80%
# - 爆款元素: 60-70%

# 2. 检查输入质量
# - 确保SRT格式正确
# - 时间轴连续无重叠
# - 字幕内容完整

# 3. 尝试不同模型
# 中文: qwen2.5-7b-instruct-q5
# 英文: mistral-7b-instruct-q5

# 4. 提供更多上下文
# 在字幕中包含更多剧情信息
```

## 💾 内存和性能问题

### Q8: 内存使用过高
**问题**: 程序占用内存超过400MB

**解决方案**:
```bash
# 启用低内存模式
python optimized_quick_launcher.py --memory-mode low

# 在设置中配置内存限制
# 最大内存: 350MB
# 启用垃圾回收: 是
# 预加载模型: 否

# 使用更小的模型
# Q4量化版本 (约3GB)
# Q2量化版本 (约2GB)

# 监控内存使用
python -c "
import psutil
process = psutil.Process()
print(f'内存使用: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

### Q9: 处理速度很慢
**问题**: AI重构或导出速度过慢

**解决方案**:
```bash
# 1. 检查CPU使用率
# 任务管理器 (Windows) 或 top (Linux/macOS)

# 2. 优化系统设置
# - 关闭不必要的后台程序
# - 设置高性能电源模式
# - 确保有足够的磁盘空间

# 3. 使用更快的存储
# - SSD比HDD快很多
# - 确保项目在本地磁盘上

# 4. 调整处理参数
# - 减少批处理大小
# - 降低重构强度
# - 使用较小的模型

# 5. 检查网络连接
# 如果使用在线模型，确保网络稳定
```

### Q10: 4GB RAM设备运行问题
**问题**: 在4GB内存设备上运行困难

**解决方案**:
```bash
# 1. 使用专门的4GB优化配置
python optimized_quick_launcher.py --memory-mode ultra-low

# 2. 关闭其他应用程序
# 释放尽可能多的内存

# 3. 使用最小模型
# Q2量化版本 (约2GB)

# 4. 启用虚拟内存
# Windows: 设置页面文件大小
# Linux: 配置swap分区

# 5. 分批处理
# 不要一次处理太多字幕文件

# 6. 监控内存使用
python memory_check.py
```

## 📁 文件和格式问题

### Q11: SRT文件无法导入
**问题**: 字幕文件导入失败

**解决方案**:
```bash
# 1. 检查文件格式
# 确保是标准SRT格式:
# 1
# 00:00:01,000 --> 00:00:05,000
# 字幕内容

# 2. 检查文件编码
# 使用UTF-8编码保存文件

# 3. 验证时间格式
# 时间格式必须是: HH:MM:SS,mmm

# 4. 检查文件权限
# 确保文件可读

# 5. 使用示例文件测试
cp tests/fixtures/sample.srt test_input.srt
# 尝试导入测试文件
```

### Q12: 导出的剪映项目无法打开
**问题**: 生成的项目文件在剪映中打开失败

**解决方案**:
```bash
# 1. 检查剪映版本
# 确保使用剪映专业版 3.0+

# 2. 验证导出文件
# 检查JSON格式是否正确
python -c "
import json
with open('output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print('JSON格式正确')
"

# 3. 检查视频文件路径
# 确保视频文件存在且路径正确

# 4. 重新导出
# 使用不同的导出设置

# 5. 查看详细错误信息
# 在剪映中查看具体错误提示
```

### Q13: 视频和字幕不同步
**问题**: 导出后视频和字幕时间不匹配

**解决方案**:
```bash
# 1. 检查原始SRT时间轴
# 确保时间轴连续且正确

# 2. 验证视频文件
# 确保视频文件完整且未损坏

# 3. 调整同步设置
# 在导出设置中微调时间偏移

# 4. 使用时间轴验证工具
python -c "
from src.utils.timecode_validator import validate_srt
result = validate_srt('input.srt')
print(f'时间轴验证: {result}')
"

# 5. 重新处理
# 使用更精确的时间轴匹配
```

## 🌐 网络和连接问题

### Q14: 网络连接超时
**问题**: 下载模型或更新时网络超时

**解决方案**:
```bash
# 1. 检查网络连接
ping google.com
ping github.com

# 2. 配置代理 (如需要)
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# 3. 使用镜像源
# 在设置中配置:
# PyPI镜像: https://pypi.tuna.tsinghua.edu.cn/simple/
# HuggingFace镜像: https://hf-mirror.com

# 4. 增加超时时间
pip install --timeout 300 -r requirements.txt

# 5. 离线安装
# 下载离线安装包
```

### Q15: 防火墙阻止连接
**问题**: 企业防火墙阻止网络访问

**解决方案**:
```bash
# 1. 配置防火墙例外
# 添加Python.exe到防火墙白名单

# 2. 使用企业代理
# 配置代理设置

# 3. 离线部署
# 在有网络的机器上下载所有依赖
# 然后传输到目标机器

# 4. 联系IT部门
# 申请必要的网络权限

# 5. 使用本地模型
# 不依赖在线模型服务
```

## 🔧 高级问题

### Q16: 自定义模型训练失败
**问题**: 训练自己的模型时出错

**解决方案**:
```bash
# 1. 检查训练数据格式
# 确保数据配对正确

# 2. 验证数据质量
# 至少需要100对高质量样本

# 3. 调整训练参数
# 降低学习率和批大小

# 4. 检查GPU内存
# 训练需要更多内存

# 5. 使用预训练模型
# 基于现有模型进行微调
```

### Q17: 批量处理中断
**问题**: 处理大量文件时程序崩溃

**解决方案**:
```bash
# 1. 减少批处理大小
# 一次处理较少的文件

# 2. 启用断点续传
# 程序会自动从中断处继续

# 3. 增加内存限制
# 为批处理分配更多内存

# 4. 检查磁盘空间
# 确保有足够的存储空间

# 5. 使用稳定版本
# 避免使用开发版本
```

### Q18: 多语言支持问题
**问题**: 非中英文语言处理异常

**解决方案**:
```bash
# 1. 检查语言支持
# 目前主要支持中文和英文

# 2. 使用语言检测
# 确保正确识别语言类型

# 3. 转换为支持的语言
# 先翻译为中文或英文

# 4. 等待更新
# 更多语言支持正在开发中

# 5. 贡献语言包
# 帮助添加新语言支持
```

## 📞 获取更多帮助

### 官方支持渠道

1. **GitHub Issues**: https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues
   - 报告Bug和技术问题
   - 功能请求和建议

2. **GitHub Discussions**: https://github.com/CKEN-STAR/VisionAI-ClipsMaster/discussions
   - 使用问题讨论
   - 经验分享

3. **文档中心**: 项目根目录docs/文件夹
   - 详细技术文档
   - API参考手册

### 问题报告模板

当报告问题时，请提供以下信息：

```
**环境信息**:
- 操作系统: Windows 10/11, Linux, macOS
- Python版本: python --version
- 项目版本: git describe --tags

**问题描述**:
- 具体的错误信息
- 重现步骤
- 预期行为 vs 实际行为

**日志信息**:
- 错误日志内容
- 启动日志
- 相关截图

**已尝试的解决方案**:
- 列出已经尝试的方法
- 结果如何
```

### 社区资源

- **用户手册**: 查看USAGE.md获取详细使用指南
- **开发文档**: 查看DEVELOPMENT.md了解技术细节
- **示例项目**: examples/目录下的示例代码
- **测试用例**: tests/目录下的测试示例

---

**还有问题？** 不要犹豫，在GitHub上创建Issue或参与Discussions讨论！我们的社区随时准备帮助您！🤝
