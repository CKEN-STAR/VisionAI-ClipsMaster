# 🚀 VisionAI-ClipsMaster 部署指南

> **生产环境部署和配置 - 从开发到生产的完整部署方案**

## 📋 部署概述

VisionAI-ClipsMaster支持多种部署方式，从单机部署到分布式集群，满足不同规模的使用需求。

### 🎯 部署目标

- **高可用性**: 99.9%服务可用性
- **高性能**: 启动时间≤5秒，内存使用≤400MB
- **可扩展性**: 支持水平扩展
- **易维护性**: 自动化部署和监控

## 🏗️ 部署架构

### 单机部署架构

```
┌─────────────────────────────────────┐
│           VisionAI-ClipsMaster      │
├─────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌──────┐ │
│  │   UI    │  │   AI    │  │ Export│ │
│  │ Layer   │  │ Engine  │  │Engine │ │
│  └─────────┘  └─────────┘  └──────┘ │
├─────────────────────────────────────┤
│           System Resources          │
│  CPU: 4核+ | RAM: 4GB+ | SSD: 5GB+ │
└─────────────────────────────────────┘
```

### 分布式部署架构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │    │  AI Engine  │    │  Storage    │
│   Server    │◄──►│   Cluster   │◄──►│   Layer     │
│             │    │             │    │             │
│ - UI Layer  │    │ - Model API │    │ - File Store│
│ - Load Bal. │    │ - Queue Mgr │    │ - Cache     │
│ - Gateway   │    │ - Workers   │    │ - Database  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🎯 部署方式选择

### 方式1: 标准单机部署 (推荐)

**适用场景**:
- 个人用户或小团队
- 处理量 < 100个项目/天
- 4GB-8GB RAM设备

**优势**:
- 部署简单，维护成本低
- 资源占用少
- 响应速度快

### 方式2: Docker容器部署

**适用场景**:
- 需要环境隔离
- 多环境部署 (开发/测试/生产)
- 云平台部署

**优势**:
- 环境一致性
- 易于扩展
- 便于CI/CD集成

### 方式3: 分布式集群部署

**适用场景**:
- 企业级应用
- 处理量 > 1000个项目/天
- 高可用性要求

**优势**:
- 高可用性
- 水平扩展
- 负载均衡

## 🔧 标准单机部署

### 环境准备

#### 系统要求
```bash
# 最低配置
CPU: 双核 2.0GHz+
RAM: 4GB (推荐8GB+)
存储: 5GB可用空间 (SSD推荐)
网络: 稳定互联网连接

# 推荐配置
CPU: 四核 3.0GHz+
RAM: 16GB
存储: 20GB SSD
网络: 100Mbps+
```

#### 软件依赖
```bash
# 操作系统
Windows 10/11 (推荐)
Ubuntu 20.04+ / CentOS 8+
macOS 10.15+

# 运行时环境
Python 3.8+ (推荐3.11+)
Git 2.20+
FFmpeg 4.0+
```

### 部署步骤

#### 步骤1: 环境初始化
```bash
# 创建部署目录
mkdir -p /opt/visionai-clipsmaster
cd /opt/visionai-clipsmaster

# 创建专用用户 (Linux)
sudo useradd -r -s /bin/false visionai
sudo chown -R visionai:visionai /opt/visionai-clipsmaster
```

#### 步骤2: 代码部署
```bash
# 克隆项目
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git .

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 步骤3: 配置文件设置
```bash
# 创建生产配置
cp configs/config.example.json configs/production.json

# 编辑配置文件
nano configs/production.json
```

**生产配置示例**:
```json
{
  "environment": "production",
  "debug": false,
  "memory_limit_mb": 400,
  "startup_optimization": true,
  "logging": {
    "level": "INFO",
    "file": "/var/log/visionai/app.log",
    "max_size": "100MB",
    "backup_count": 5
  },
  "models": {
    "default_chinese": "qwen2.5-7b-instruct-q5",
    "default_english": "mistral-7b-instruct-q5",
    "auto_download": true,
    "cache_dir": "/opt/visionai-clipsmaster/models"
  },
  "performance": {
    "enable_gpu": false,
    "max_workers": 4,
    "batch_size": 8,
    "timeout_seconds": 300
  }
}
```

#### 步骤4: 系统服务配置

**Linux Systemd服务**:
```bash
# 创建服务文件
sudo nano /etc/systemd/system/visionai-clipsmaster.service
```

```ini
[Unit]
Description=VisionAI-ClipsMaster Service
After=network.target

[Service]
Type=simple
User=visionai
Group=visionai
WorkingDirectory=/opt/visionai-clipsmaster
Environment=PATH=/opt/visionai-clipsmaster/venv/bin
ExecStart=/opt/visionai-clipsmaster/venv/bin/python optimized_quick_launcher.py --config production
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable visionai-clipsmaster
sudo systemctl start visionai-clipsmaster

# 检查服务状态
sudo systemctl status visionai-clipsmaster
```

**Windows服务**:
```powershell
# 使用NSSM创建Windows服务
nssm install VisionAI-ClipsMaster
nssm set VisionAI-ClipsMaster Application "C:\VisionAI-ClipsMaster\venv\Scripts\python.exe"
nssm set VisionAI-ClipsMaster AppParameters "optimized_quick_launcher.py --config production"
nssm set VisionAI-ClipsMaster AppDirectory "C:\VisionAI-ClipsMaster"
nssm start VisionAI-ClipsMaster
```

## 🐳 Docker容器部署

### Dockerfile

```dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建非root用户
RUN useradd -m -u 1000 visionai && \
    chown -R visionai:visionai /app
USER visionai

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# 启动命令
CMD ["python", "optimized_quick_launcher.py", "--config", "docker"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  visionai-clipsmaster:
    build: .
    container_name: visionai-clipsmaster
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./logs:/app/logs
    environment:
      - ENVIRONMENT=production
      - MEMORY_LIMIT_MB=400
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  nginx:
    image: nginx:alpine
    container_name: visionai-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - visionai-clipsmaster
```

### 部署命令

```bash
# 构建和启动
docker-compose up -d

# 查看日志
docker-compose logs -f visionai-clipsmaster

# 更新部署
docker-compose pull
docker-compose up -d --force-recreate

# 停止服务
docker-compose down
```

## ☁️ 云平台部署

### AWS部署

#### EC2实例配置
```bash
# 推荐实例类型
t3.medium (2 vCPU, 4GB RAM) - 基础使用
t3.large (2 vCPU, 8GB RAM) - 推荐配置
c5.xlarge (4 vCPU, 8GB RAM) - 高性能

# 存储配置
根卷: 20GB gp3 SSD
数据卷: 50GB gp3 SSD (可选)
```

#### 安全组配置
```bash
# 入站规则
SSH (22): 管理员IP
HTTP (80): 0.0.0.0/0
HTTPS (443): 0.0.0.0/0
Custom (8080): VPC内部

# 出站规则
All traffic: 0.0.0.0/0
```

#### 部署脚本
```bash
#!/bin/bash
# AWS EC2 部署脚本

# 更新系统
sudo yum update -y

# 安装依赖
sudo yum install -y python3 python3-pip git ffmpeg

# 克隆项目
cd /opt
sudo git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 设置权限
sudo chown -R ec2-user:ec2-user /opt/VisionAI-ClipsMaster

# 安装Python依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置服务
sudo cp deploy/aws/visionai.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable visionai
sudo systemctl start visionai
```

### Azure部署

#### 容器实例配置
```yaml
# azure-container-instance.yaml
apiVersion: 2019-12-01
location: eastus
name: visionai-clipsmaster
properties:
  containers:
  - name: visionai-app
    properties:
      image: visionai/clipsmaster:latest
      resources:
        requests:
          cpu: 2
          memoryInGb: 4
      ports:
      - port: 8080
        protocol: TCP
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 8080
```

### Google Cloud部署

#### Cloud Run配置
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: visionai-clipsmaster
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/memory: "512Mi"
        run.googleapis.com/cpu: "2"
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/visionai-clipsmaster
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          limits:
            memory: "512Mi"
            cpu: "2"
```

## 📊 监控和维护

### 健康检查

#### 应用健康检查
```python
# health_check.py
import requests
import sys
import time

def check_health():
    try:
        response = requests.get('http://localhost:8080/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print("✅ 应用健康状态正常")
                return True
        print("❌ 应用健康检查失败")
        return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

if __name__ == "__main__":
    if not check_health():
        sys.exit(1)
```

#### 系统监控脚本
```bash
#!/bin/bash
# monitor.sh - 系统监控脚本

# 检查服务状态
if ! systemctl is-active --quiet visionai-clipsmaster; then
    echo "❌ 服务未运行，尝试重启..."
    systemctl restart visionai-clipsmaster
    sleep 10
fi

# 检查内存使用
MEMORY_USAGE=$(ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem -C python | head -2 | tail -1 | awk '{print $4}')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "⚠️ 内存使用过高: ${MEMORY_USAGE}%"
    # 发送告警
fi

# 检查磁盘空间
DISK_USAGE=$(df /opt/visionai-clipsmaster | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️ 磁盘空间不足: ${DISK_USAGE}%"
    # 清理日志文件
    find /var/log/visionai -name "*.log" -mtime +7 -delete
fi
```

### 日志管理

#### 日志轮转配置
```bash
# /etc/logrotate.d/visionai
/var/log/visionai/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 visionai visionai
    postrotate
        systemctl reload visionai-clipsmaster
    endscript
}
```

### 备份策略

#### 自动备份脚本
```bash
#!/bin/bash
# backup.sh - 自动备份脚本

BACKUP_DIR="/backup/visionai"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/visionai-clipsmaster/configs/

# 备份模型文件 (可选，文件较大)
# tar -czf $BACKUP_DIR/models_$DATE.tar.gz /opt/visionai-clipsmaster/models/

# 备份数据库 (如果使用)
# mysqldump -u user -p database > $BACKUP_DIR/database_$DATE.sql

# 清理旧备份 (保留30天)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "✅ 备份完成: $DATE"
```

## 🔧 故障排除

### 常见部署问题

#### 问题1: 服务启动失败
```bash
# 检查日志
journalctl -u visionai-clipsmaster -f

# 常见原因和解决方案
1. 端口被占用: 修改配置文件中的端口
2. 权限不足: 检查文件权限和用户配置
3. 依赖缺失: 重新安装requirements.txt
4. 配置错误: 验证配置文件格式
```

#### 问题2: 内存使用过高
```bash
# 监控内存使用
top -p $(pgrep -f visionai)

# 解决方案
1. 启用低内存模式
2. 调整模型量化级别
3. 增加系统内存
4. 优化批处理大小
```

#### 问题3: 性能问题
```bash
# 性能诊断
python startup_benchmark.py

# 优化建议
1. 使用SSD存储
2. 增加CPU核心数
3. 优化网络连接
4. 启用缓存机制
```

## 📞 获取支持

### 部署支持

- **文档**: 查看详细部署文档
- **社区**: GitHub Discussions
- **问题报告**: GitHub Issues
- **企业支持**: 联系项目维护者

### 监控和告警

- **Prometheus**: 指标收集
- **Grafana**: 可视化监控
- **AlertManager**: 告警通知
- **ELK Stack**: 日志分析

---

**部署成功！** 您的VisionAI-ClipsMaster现在已经在生产环境中运行。记得定期检查系统状态和性能指标！🚀✨
