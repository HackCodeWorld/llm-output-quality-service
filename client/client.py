import json
import grpc
from backend.llm_quality_pb2 import GenerateRequest
from backend.llm_quality_pb2_grpc import LLMQualityServiceStub
from google.protobuf.json_format import MessageToDict
   
class LLMClient:
    def __init__(self, grpc_host="localhost", grpc_port=50051):
        self.channel = grpc.insecure_channel(f"{grpc_host}:{grpc_port}")
        self.stub = LLMQualityServiceStub(self.channel)

    def batch_generate_from_jsonl(self, jsonl_path, output_path="results.jsonl"):
        with open(jsonl_path, "r", encoding="utf-8") as f, open(output_path, "w", encoding="utf-8") as out_f:
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
                print(resp)  
                
                # 结构化写入结果文件
                out_f.write(json.dumps({
                    "code": resp.code,
                    "syntax_ok": resp.syntax_ok,
                    "test_results": [MessageToDict(tr) for tr in resp.test_results],
                    "exec_time_ms": resp.exec_time_ms
                }, ensure_ascii=False) + "\n")

    def close(self):
        self.channel.close()
        
# client main 调用
if __name__ == "__main__":
    client = LLMClient()
    client.batch_generate_from_jsonl("data/humaneval_164.jsonl", output_path="results.jsonl")
    client.close()