FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（ARM64 兼容）
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制代码
COPY grpc_service/ ./grpc_service/
COPY backend/ ./backend/
COPY generate_proto.sh .

# 生成 proto stubs
RUN bash generate_proto.sh

EXPOSE 50051

CMD ["python", "backend/app.py"]