import json

# 你检测到有问题的行号（从1开始计数）
error_lines = [2, 11, 60, 77, 96, 98, 108, 109, 120, 129, 130, 145, 146]

with open("data/HumanEval.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if i in error_lines:
            obj = json.loads(line)
            prompt = obj.get("prompt")
            code = obj.get("canonical_solution") or obj.get("code")
            print(f"Line {i} prompt:\n{prompt}\n")
            print(f"Line {i} code:\n{code}\n{'-'*40}")