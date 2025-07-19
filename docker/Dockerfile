# VisionAI-ClipsMaster Docker镜像
# 支持多阶段构建，优化镜像大小

# 基础镜像 - 使用Python 3.10 slim版本
FROM python:3.10-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    git \
    # 视频处理
    ffmpeg \
    # 图像处理
    libopencv-dev \
    # 音频处理
    libsndfile1 \
    # 编译工具
    build-essential \
    # 清理缓存
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd --create-home --shell /bin/bash visionai
USER visionai
WORKDIR /home/visionai

# 设置Python路径
ENV PATH="/home/visionai/.local/bin:$PATH"

# 升级pip
RUN pip install --user --upgrade pip

# 构建阶段 - 安装依赖
FROM base as builder

# 复制依赖文件
COPY --chown=visionai:visionai requirements/ ./requirements/

# 安装Python依赖
RUN pip install --user -r requirements/requirements.txt

# 生产阶段 - 复制应用代码
FROM base as production

# 从构建阶段复制已安装的包
COPY --from=builder /home/visionai/.local /home/visionai/.local

# 复制应用代码
COPY --chown=visionai:visionai src/ ./src/
COPY --chown=visionai:visionai configs/ ./configs/
COPY --chown=visionai:visionai scripts/ ./scripts/
COPY --chown=visionai:visionai docker/entrypoint.sh ./entrypoint.sh

# 创建必要目录
RUN mkdir -p models data/input data/output logs

# 设置执行权限
RUN chmod +x entrypoint.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python scripts/check_environment.py || exit 1

# 暴露端口
EXPOSE 8080

# 设置入口点
ENTRYPOINT ["./entrypoint.sh"]

# 默认命令
CMD ["gui"]

# 轻量版镜像 - 4GB内存优化
FROM base as lite

# 复制轻量化依赖文件
COPY --chown=visionai:visionai requirements/requirements-lite.txt ./requirements-lite.txt

# 安装轻量化依赖
RUN pip install --user -r requirements-lite.txt

# 复制应用代码
COPY --chown=visionai:visionai src/ ./src/
COPY --chown=visionai:visionai configs/ ./configs/
COPY --chown=visionai:visionai scripts/ ./scripts/
COPY --chown=visionai:visionai docker/entrypoint.sh ./entrypoint.sh

# 创建必要目录
RUN mkdir -p models data/input data/output logs

# 设置执行权限
RUN chmod +x entrypoint.sh

# 设置轻量化配置
ENV VISIONAI_MODE=lite \
    VISIONAI_MAX_MEMORY=3800

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python scripts/check_environment.py || exit 1

# 暴露端口
EXPOSE 8080

# 设置入口点
ENTRYPOINT ["./entrypoint.sh"]

# 默认命令
CMD ["gui"]
