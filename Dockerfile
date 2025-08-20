# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装构建依赖（ARM64需要gcc来编译psutil）
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码和启动脚本
COPY app/ ./app/
COPY entrypoint.sh ./entrypoint.sh

# 创建非root用户并设置权限
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chmod +x /app/entrypoint.sh
USER app

# 暴露端口
EXPOSE 12345

# 健康检查 - 使用更可靠的方式
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:12345/health', timeout=5)" || exit 1

# 启动命令 - 使用更健壮的启动脚本
CMD ["./entrypoint.sh"]
