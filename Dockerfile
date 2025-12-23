# Dockerfile
# 多阶段构建：构建阶段
FROM python:3.11-slim as builder

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        python3-dev \
        musl-dev \
        libssl-dev \
        libffi-dev \
        default-libmysqlclient-dev \
        pkg-config \
        curl \
        gnupg \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --user -r requirements.txt

# 多阶段构建：运行阶段
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
        curl \
        nginx \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 django \
    && mkdir -p /app/staticfiles /app/media /app/logs \
    && chown -R django:django /app

# 从构建阶段复制已安装的包
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制项目文件
COPY --chown=django:django . .

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 复制启动脚本
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# 切换到非root用户
USER django

# 设置环境变量
ENV DJANGO_SETTINGS_MODULE=blog_project.settings_production
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000 80

# 启动脚本
ENTRYPOINT ["./entrypoint.sh"]