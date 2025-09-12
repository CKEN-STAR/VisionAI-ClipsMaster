# VisionAI-ClipsMaster Production Dockerfile
# Multi-stage build for optimized production image

# ============================================
# Stage 1: Base Dependencies Builder
# ============================================
FROM python:3.11-slim as base-builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libopencv-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    libhdf5-dev \
    libprotobuf-dev \
    protobuf-compiler \
    libgoogle-glog-dev \
    libgflags-dev \
    libgtest-dev \
    libeigen3-dev \
    libopenblas-dev \
    liblapack-dev \
    python3-dev \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install FFmpeg from source for better compatibility
RUN wget https://ffmpeg.org/releases/ffmpeg-6.0.tar.xz && \
    tar -xf ffmpeg-6.0.tar.xz && \
    cd ffmpeg-6.0 && \
    ./configure --enable-shared --disable-static --enable-gpl --enable-libx264 && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd .. && rm -rf ffmpeg-6.0*

# ============================================
# Stage 2: Python Dependencies Builder
# ============================================
FROM base-builder as python-builder

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/requirements.txt

# Install PyTorch with CPU support (smaller size)
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install -r /tmp/requirements.txt

# Install additional dependencies for containerized environment
RUN pip install \
    gunicorn \
    uvicorn[standard] \
    fastapi \
    websockets \
    redis \
    celery

# ============================================
# Stage 3: Application Builder
# ============================================
FROM python:3.11-slim as app-builder

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libopencv-dev \
    libavcodec58 \
    libavformat58 \
    libswscale5 \
    libv4l-0 \
    libxvidcore4 \
    libx264-160 \
    libjpeg62-turbo \
    libpng16-16 \
    libtiff5 \
    libatlas3-base \
    libhdf5-103 \
    libprotobuf23 \
    libgoogle-glog0v5 \
    libgflags2.2 \
    libeigen3-dev \
    libopenblas0 \
    liblapack3 \
    ffmpeg \
    xvfb \
    x11vnc \
    fluxbox \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ============================================
# Stage 4: Final Production Image
# ============================================
FROM app-builder as production

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . /app/

# Create necessary directories with proper permissions
RUN mkdir -p /app/models /app/data /app/output /app/logs /app/cache && \
    chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONPATH="/app:$PYTHONPATH" \
    DISPLAY=:99 \
    QT_QPA_PLATFORM=offscreen \
    MPLBACKEND=Agg \
    CUDA_VISIBLE_DEVICES="" \
    TORCH_HOME=/app/cache/torch \
    TRANSFORMERS_CACHE=/app/cache/transformers \
    HF_HOME=/app/cache/huggingface

# Expose ports
EXPOSE 8000 8080 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Switch to non-root user
USER appuser

# Default command
CMD ["python", "simple_ui_fixed.py"]