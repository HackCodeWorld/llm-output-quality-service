import grpc
import logging
from logging.handlers import RotatingFileHandler
from concurrent import futures
from backend.llm_quality_pb2_grpc import add_LLMQualityServiceServicer_to_server
from grpc_service.service import LLMQualityService

# 日志统一配置模版（文件大小轮转，追加写入）
logging.basicConfig(
    level=logging.DEBUG,  # 开发用DEBUG，生产改为INFO
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        RotatingFileHandler(
            "service.log",           # 日志文件名
            mode="a",                # 追加写入
            maxBytes=20*1024*1024,   # 单个日志文件最大20MB
            backupCount=10,          # 最多保留10个历史日志文件
            encoding="utf-8"
        ),
    ]
)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_LLMQualityServiceServicer_to_server(LLMQualityService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server listening on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
