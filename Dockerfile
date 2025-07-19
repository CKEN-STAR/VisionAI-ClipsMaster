# 构建阶段
FROM python:3.10-slim as builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt requirements-dev.txt ./

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-dev.txt \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# 运行阶段
FROM python:3.10-slim

# 添加非root用户
RUN groupadd -r visionai && useradd -r -g visionai visionai

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制wheels
COPY --from=builder /build/wheels /wheels

# 安装Python包
RUN pip install --no-cache-dir /wheels/*

# 复制项目文件
COPY --chown=visionai:visionai src/ ./src/
COPY --chown=visionai:visionai tests/ ./tests/
COPY --chown=visionai:visionai configs/ ./configs/
COPY --chown=visionai:visionai setup.cfg pyproject.toml ./

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/app/configs \
    PATH="/home/visionai/.local/bin:${PATH}"

# 切换到非root用户
USER visionai

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8000

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 设置卷挂载点
VOLUME ["/app/data", "/app/logs", "/app/configs"]

# 设置入口点
ENTRYPOINT ["python", "-m", "src.main"]

# 添加标签
LABEL maintainer="VisionAI Team <support@visionai.com>" \
      version="1.0" \
      description="VisionAI-ClipsMaster - 媒体文件验证和处理工具" \
      org.opencontainers.image.source="https://github.com/visionai/clipsmaster" 