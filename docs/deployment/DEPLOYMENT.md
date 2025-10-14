# 🚀 VisionAI-ClipsMaster 部署指南

## 📋 概述

本指南详细介绍如何在不同环境中部署VisionAI-ClipsMaster，包括开发环境、生产环境和分发打包。

## 🏗️ 部署架构

### 系统组件
```
VisionAI-ClipsMaster
├── AI模型层 (Mistral-7B + Qwen2.5-7B)
├── 核心处理引擎 (剧本重构 + 视频拼接)
├── UI界面层 (PyQt6)
└── 配置管理 (YAML/JSON配置文件)
```

## 🔧 环境部署

### 开发环境部署

#### 1. 基础环境准备
```bash
# 克隆项目
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

#### 2. 模型配置
```bash
# 配置模型路径
python configure_model_by_hardware.py

# 下载基础模型（可选）
python scripts/download_models.py
```

#### 3. 启动开发服务
```bash
# 启动主UI程序（推荐）
python simple_ui_fixed.py

# 或启动命令行版本
python main.py
```

### 生产环境部署

#### 1. Docker部署（推荐）
```bash
# 构建镜像
docker build -t visionai-clipsmaster .

# 运行容器
docker run -d \
  --name visionai-app \
  -p 8080:8080 \
  -v /path/to/data:/app/data \
  -v /path/to/models:/app/models \
  visionai-clipsmaster
```

#### 2. 系统服务部署
```bash
# 创建系统服务（Linux）
sudo cp deployment/visionai.service /etc/systemd/system/
sudo systemctl enable visionai
sudo systemctl start visionai
```

## 📦 打包分发

### Windows可执行文件打包

#### 1. 使用PyInstaller
```bash
# 安装打包工具
pip install pyinstaller

# 执行打包
python scripts/deployment/build_package.py

# 生成的文件位于 dist/ 目录
```

#### 2. 创建安装程序
```bash
# 使用NSIS创建安装程序
makensis scripts/deployment/installer.nsi
```

### 便携版打包
```bash
# 创建便携版
python scripts/deployment/create_deployment_package.py --portable

# 输出: VisionAI-ClipsMaster-Portable.zip
```

## ⚙️ 配置管理

### 环境配置文件

#### 开发环境 (configs/environments/dev.yaml)
```yaml
debug: true
log_level: DEBUG
model_quantization: Q4_K_M
memory_limit: 4GB
```

#### 生产环境 (configs/environments/prod.yaml)
```yaml
debug: false
log_level: INFO
model_quantization: Q5_K
memory_limit: 8GB
auto_optimization: true
```

### 模型配置
```yaml
# configs/model_config.yaml
active_models:
  chinese: "qwen2.5-7b-zh"
  english: "mistral-7b-en"
  
quantization:
  default: "Q4_K_M"
  low_memory: "Q2_K"
  high_performance: "Q5_K"
```

## 🔒 安全配置

### 1. 访问控制
```yaml
# configs/security_policy.yaml
access_control:
  enable_auth: true
  session_timeout: 3600
  max_file_size: 2GB
```

### 2. 数据保护
```yaml
data_protection:
  encrypt_temp_files: true
  auto_cleanup: true
  backup_retention: 7
```

## 📊 监控和日志

### 日志配置
```yaml
# configs/logging.yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    - file: logs/visionai.log
    - console: true
```

### 性能监控
```bash
# 启动监控面板
python start_monitor_dashboard.py

# 访问: http://localhost:8080/monitor
```

## 🚨 故障排除

### 常见部署问题

#### 1. 内存不足
```bash
# 启用低内存模式
export VISIONAI_LOW_MEMORY=true
python main.py
```

#### 2. 模型加载失败
```bash
# 检查模型路径
python scripts/verify_models.py

# 重新下载模型
python scripts/download_models.py --force
```

#### 3. 依赖冲突
```bash
# 清理环境
pip uninstall -r requirements.txt -y
pip install -r requirements.txt --force-reinstall
```

## 📈 性能优化

### 1. 内存优化
- 启用模型量化: `Q4_K_M` 或 `Q2_K`
- 配置内存限制: `memory_limit: 4GB`
- 启用自动清理: `auto_cleanup: true`

### 2. CPU优化
- 启用SIMD加速: `enable_simd: true`
- 配置线程数: `max_threads: 4`
- 启用缓存: `enable_cache: true`

### 3. 存储优化
- 启用压缩: `compress_temp: true`
- 配置缓存大小: `cache_size: 1GB`
- 自动清理临时文件: `auto_cleanup_temp: true`

## 🔄 更新和维护

### 版本更新
```bash
# 备份当前配置
cp -r configs configs.backup

# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 迁移配置
python scripts/migrate_config.py
```

### 数据备份
```bash
# 备份用户数据
python scripts/backup_user_data.py

# 备份模型文件
python scripts/backup_models.py
```

## 📞 技术支持

如遇部署问题，请参考：
- [故障排除指南](TROUBLESHOOTING.md)
- [常见问题](FAQ.md)
- [GitHub Issues](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)

---

**部署成功后，您就可以开始使用VisionAI-ClipsMaster进行智能短剧混剪了！** 🎬✨
