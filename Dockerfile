# DeepAnalytics Pro - Docker配置
FROM node:18-alpine AS frontend-build

# 构建前端
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Python后端
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制后端代码
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/build ./frontend/build

# 安装Python依赖
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要目录
RUN mkdir -p logs static reports

# 暴露端口
EXPOSE 8000 3000

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV NODE_ENV=production

# 启动命令
CMD ["python", "main.py"] 