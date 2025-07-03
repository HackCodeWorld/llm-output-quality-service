import json
import grpc
from backend.llm_quality_pb2 import GenerateRequest
from backend.llm_quality_pb2_grpc import LLMQualityServiceStub

class LLMClient:
    def __init__(self, grpc_host="localhost", grpc_port=50051):
        self.channel = grpc.insecure_channel(f"{grpc_host}:{grpc_port}")
        self.stub = LLMQualityServiceStub(self.channel)

    def batch_generate_from_jsonl(self, jsonl_path):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                prompt = item.get("prompt", "")
                response = item.get("canonical_solution", "")
                raw_test_code = item.get("test", "")
                entry_point = item.get("entry_point", "")
                req = GenerateRequest(
                    prompt=prompt,
                    response=response,
                    raw_test_code=raw_test_code,
                    entry_point=entry_point
                )
                resp = self.stub.Generate(req)
                print(resp)  # 可自定义处理

    def close(self):
        self.channel.close()

# 用法示例
if __name__ == "__main__":
    client = LLMClient()
    client.batch_generate_from_jsonl("data/humaneval_164.jsonl")
    client.close()