import json
import grpc
from backend.llm_quality_pb2 import GenerateRequest, TestCase
from backend.llm_quality_pb2_grpc import LLMQualityServiceStub
from google.protobuf.json_format import MessageToDict

# 命令行第一个参数：数据集类型（humaneval、mbpp、apps等）
# 命令行第二个参数：jsonl 文件路径
# 加新数据集：只需在 FIELD_ADAPTERS 里加一行 lambda
class LLMClient:
    FIELD_ADAPTERS = {
        # 整 - 大段测试代码模式
        "humaneval": lambda item: {
            "prompt": item.get("prompt", ""),
            "response": item.get("canonical_solution", ""),
            "raw_test_code": item.get("test", ""),
            "entry_point": item.get("entry_point", ""),
            "test_cases": [] # keypoint：不要传 test_cases
        },
        # 单测模式
        "mbpp": lambda item: {
            "prompt": item.get("text", ""),
            "response": item.get("code", ""),
            "raw_test_code": "",  # keypoint：不要传 raw_test_code
            "entry_point": item.get("entry_point", ""),
            "test_cases": [
                {
                    "input": line.split("==")[0].replace("assert", "").strip(),
                    "expected": line.split("==")[1].strip()
                }
                for line in item.get("test_list", [])
                if "==" in line
            ]
        },
        # 可继续加扩展其他数据集...
    }

    def __init__(self, grpc_host="localhost", grpc_port=50051, dataset_type="humaneval"):
        self.channel = grpc.insecure_channel(f"{grpc_host}:{grpc_port}")
        self.stub = LLMQualityServiceStub(self.channel)
        self.dataset_type = dataset_type

    def extract_fields(self, item):
        if self.dataset_type in self.FIELD_ADAPTERS:
            return self.FIELD_ADAPTERS[self.dataset_type](item)
        # fallback
        return {
            "prompt": item.get("prompt", ""),
            "response": item.get("response", item.get("code", "")),
            "raw_test_code": item.get("test", ""),
            "entry_point": item.get("entry_point", ""),
        }

    def batch_generate_from_jsonl(self, jsonl_path, output_path="results.jsonl"):
        with open(jsonl_path, "r", encoding="utf-8") as f, open(output_path, "a", encoding="utf-8") as out_f:
            for line in f:
                item = json.loads(line)
                fields = self.extract_fields(item)
                # 只在 test_cases 非空时传 test_cases
                if fields.get("test_cases"):
                    req = GenerateRequest(
                        prompt=fields["prompt"],
                        response=fields["response"],
                        entry_point=fields["entry_point"],
                        test_cases=[
                            TestCase(input=tc["input"], expected=tc["expected"])
                            for tc in fields["test_cases"]
                        ]
                    )
                # raw_test_code模式
                else:
                    req = GenerateRequest(
                        prompt=fields["prompt"],
                        response=fields["response"],
                        raw_test_code=fields["raw_test_code"],
                        entry_point=fields["entry_point"]
                    )
                    
                resp = self.stub.Generate(req)
                result = {
                    "code": resp.code,
                    "syntax_ok": resp.syntax_ok,
                    "test_results": [MessageToDict(tr) for tr in resp.test_results],
                    "exec_time_ms": resp.exec_time_ms
                }
                print(json.dumps(result, ensure_ascii=False))
                out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
                
    def close(self):
        self.channel.close()

if __name__ == "__main__":
    import sys
    dataset_type = sys.argv[1] if len(sys.argv) > 1 else "humaneval"
    jsonl_path = sys.argv[2] if len(sys.argv) > 2 else "data/humaneval_164.jsonl"
    client = LLMClient(dataset_type=dataset_type)
    client.batch_generate_from_jsonl(jsonl_path, output_path="results.jsonl")
    client.close()