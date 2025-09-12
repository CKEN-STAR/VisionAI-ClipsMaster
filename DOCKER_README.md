# VisionAI-ClipsMaster Docker 容器化解决方案

## 🎯 概述

VisionAI-ClipsMaster 的完整 Docker 容器化解决方案，旨在解决以下问题：
- 避免在每个环境中重复安装 2.5GB 的 Python 依赖包
- 提供标准化的运行环境，确保跨平台一致性
- 优化容器体积，同时保持所有功能完整性

## 📁 文件结构

```
VisionAI-ClipsMaster/
├── Dockerfile                    # 生产环境镜像
├── Dockerfile.dev               # 开发环境镜像
├── docker-compose.yml           # 生产环境服务编排
├── docker-compose.dev.yml       # 开发环境服务编排
├── .dockerignore               # Docker 忽略文件
├── .env.example                # 环境变量模板
├── docker-start.sh             # Linux/Mac 启动脚本
├── docker-start.bat            # Windows 批处理脚本
├── docker-start.ps1            # Windows PowerShell 脚本
└── docker/
    ├── nginx/
    │   └── nginx.conf          # Nginx 反向代理配置
    ├── postgres/
    │   └── init.sql            # PostgreSQL 初始化脚本
    └── healthcheck.py          # 健康检查脚本
```

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- Docker Compose v2.0+

### 2. 初始化设置

**Windows (PowerShell):**
```powershell
.\docker-start.ps1 setup
```

**Windows (命令提示符):**
```cmd
docker-start.bat setup
```

**Linux/Mac:**
```bash
chmod +x docker-start.sh
./docker-start.sh setup
```

### 3. 构建和启动

**生产环境:**
```bash
# 构建镜像
.\docker-start.ps1 build

# 启动服务
.\docker-start.ps1 start
```

**开发环境:**
```bash
# 构建开发镜像
.\docker-start.ps1 build-dev

# 启动开发服务
.\docker-start.ps1 start-dev
```

## 🌐 服务访问

### 生产环境服务
- **主应用程序**: http://localhost:8000
- **Web 界面**: http://localhost:8080
- **API 接口**: http://localhost:5000
- **Nginx 代理**: http://localhost:80

### 开发环境服务
- **主应用程序**: http://localhost:8000
- **Jupyter Lab**: http://localhost:8888
- **Jupyter Notebook**: http://localhost:8889

## 🛠️ 管理命令

### 基本操作
```bash
# 查看服务状态
.\docker-start.ps1 status

# 查看日志
.\docker-start.ps1 logs

# 查看特定服务日志
.\docker-start.ps1 logs visionai-app

# 重启服务
.\docker-start.ps1 restart

# 停止服务
.\docker-start.ps1 stop
```

### 维护操作
```bash
# 更新服务
.\docker-start.ps1 update

# 备份数据
.\docker-start.ps1 backup

# 清理所有容器和数据（谨慎使用）
.\docker-start.ps1 clean
```

## 📊 容器架构

### 生产环境架构
```
┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  VisionAI App   │
│   (Port 80)     │    │   (Port 8000)   │
└─────────────────┘    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Redis     │    │ PostgreSQL  │    │   Celery    │
│ (Port 6379) │    │ (Port 5432) │    │   Workers   │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 开发环境架构
```
┌─────────────────┐    ┌─────────────────┐
│  VisionAI Dev   │    │  Jupyter Lab    │
│   (Port 8000)   │    │   (Port 8888)   │
└─────────────────┘    └─────────────────┘
        │
┌─────────────┐
│   Redis     │
│ (Port 6380) │
└─────────────┘
```

## 💾 数据持久化

### 挂载卷
- `./models` → `/app/models` - AI 模型文件
- `./data` → `/app/data` - 输入数据
- `./output` → `/app/output` - 输出结果
- `./logs` → `/app/logs` - 日志文件
- `./cache` → `/app/cache` - 缓存文件
- `./configs` → `/app/configs` - 配置文件

### 数据库卷
- `postgres-data` - PostgreSQL 数据
- `redis-data` - Redis 数据

## ⚙️ 环境配置

### 环境变量配置
复制 `.env.example` 到 `.env` 并根据需要修改：

```bash
# 应用配置
APP_ENV=production
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://visionai:visionai123@postgres:5432/visionai

# Redis 配置
REDIS_URL=redis://redis:6379/0

# AI/ML 配置
TORCH_HOME=/app/cache/torch
TRANSFORMERS_CACHE=/app/cache/transformers
```

### 自定义配置
- 修改 `docker-compose.yml` 中的端口映射
- 调整 `docker/nginx/nginx.conf` 中的代理设置
- 更新 `docker/postgres/init.sql` 中的数据库初始化脚本

## 🔧 开发指南

### 开发环境特性
- **热重载**: 代码更改自动重启
- **Jupyter 支持**: 内置 Jupyter Lab 和 Notebook
- **调试工具**: 包含 ipdb、pytest 等调试工具
- **代码质量**: 集成 black、flake8、mypy 等工具

### 开发工作流
1. 启动开发环境：`.\docker-start.ps1 start-dev`
2. 在 `http://localhost:8888` 访问 Jupyter Lab
3. 修改代码，容器会自动重启
4. 运行测试：`docker-compose -f docker-compose.dev.yml exec visionai-dev pytest`

## 🚨 故障排除

### 常见问题

**1. 容器启动失败**
```bash
# 查看详细日志
.\docker-start.ps1 logs

# 检查 Docker 状态
docker info
```

**2. 端口冲突**
```bash
# 检查端口占用
netstat -an | findstr :8000

# 修改 docker-compose.yml 中的端口映射
```

**3. 权限问题 (Linux)**
```bash
# 修复文件权限
sudo chown -R $USER:$USER ./models ./data ./output ./logs
```

**4. 内存不足**
```bash
# 增加 Docker 内存限制
# Docker Desktop -> Settings -> Resources -> Memory
```

### 健康检查
```bash
# 运行健康检查脚本
python docker/healthcheck.py
```

## 📈 性能优化

### 生产环境优化
- 使用多阶段构建减少镜像体积
- CPU 版本的 PyTorch 减少依赖大小
- Nginx 反向代理提高性能
- Redis 缓存加速数据访问

### 资源限制
在 `docker-compose.yml` 中调整资源限制：
```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2'
```

## 🔒 安全考虑

- 使用非 root 用户运行容器
- 网络隔离和防火墙配置
- 敏感信息使用环境变量
- 定期更新基础镜像

## 📚 最佳实践

1. **定期备份**: 使用 `.\docker-start.ps1 backup` 备份数据
2. **监控日志**: 定期检查应用日志
3. **资源监控**: 监控 CPU、内存、磁盘使用情况
4. **安全更新**: 定期更新 Docker 镜像
5. **测试环境**: 在生产部署前先在开发环境测试

## 🆘 支持

如遇问题，请：
1. 查看日志：`.\docker-start.ps1 logs`
2. 运行健康检查：`python docker/healthcheck.py`
3. 检查 GitHub Issues
4. 联系技术支持

---

**注意**: 首次启动可能需要较长时间来下载和构建镜像。请耐心等待并确保网络连接稳定。
