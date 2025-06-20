import grpc
from concurrent import futures
from llm_quality_pb2_grpc import add_LLMQualityServiceServicer_to_server
from service import LLMQualityService

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_LLMQualityServiceServicer_to_server(LLMQualityService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server listening on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
