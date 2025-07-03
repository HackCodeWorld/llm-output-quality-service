import grpc
import logging
from concurrent import futures
from backend.llm_quality_pb2_grpc import add_LLMQualityServiceServicer_to_server
from grpc_service.service import LLMQualityService

# 日志统一配置模版
logging.basicConfig(
    level=logging.DEBUG,  # 开发用DEBUG，生产改为INFO
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        logging.FileHandler("service.log", mode="w"),  # 覆盖写入日志文件
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
