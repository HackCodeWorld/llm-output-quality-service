import json

with open("data/humaneval_llm_batch.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        obj = json.loads(line)
        print(f"Line {i} code:\n{obj['canonical_solution']}\n{'-'*40}")