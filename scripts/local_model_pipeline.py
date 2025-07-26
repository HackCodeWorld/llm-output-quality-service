import argparse
import json
import subprocess
from pathlib import Path
from client.client import LLMClient
from grpc_service.auto_corrector import AutoCorrector
import ast


def call_ollama(prompt: str, model: str) -> str:
    """Call local Ollama model and return generated code."""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        raise RuntimeError("ollama command not found. Is Ollama installed?")


def generate_with_model(dataset_path: str, model: str, output_path: str) -> None:
    """Generate code for each item in dataset using local model."""
    with open(dataset_path, "r", encoding="utf-8") as f, open(output_path, "w", encoding="utf-8") as out_f:
        for line in f:
            item = json.loads(line)
            prompt = item.get("prompt") or item.get("text") or ""
            code = call_ollama(prompt, model)
            out = {
                "task_id": item.get("task_id"),
                "prompt": prompt,
                "code": code,
                "test": item.get("test") or item.get("test_list"),
                "entry_point": item.get("entry_point", ""),
                "model": model,
            }
            out_f.write(json.dumps(out, ensure_ascii=False) + "\n")


def run_evaluation(dataset_type: str, input_path: str, output_path: str, workers: int = 4) -> None:
    client = LLMClient(dataset_type=dataset_type)
    client.batch_generate_from_jsonl(input_path, output_path=output_path, max_workers=workers)
    client.close()


def complexity_score(code: str) -> int:
    try:
        tree = ast.parse(code)
        return len(list(ast.walk(tree)))
    except Exception:
        return 0


def run_qa(results_path: str, output_path: str) -> None:
    ac = AutoCorrector()
    with open(results_path, "r", encoding="utf-8") as f, open(output_path, "w", encoding="utf-8") as out_f:
        for line in f:
            item = json.loads(line)
            raw_code = item.get("raw_code", item.get("code", ""))
            formatted, ok, errors = ac.auto_correct_code(raw_code)
            qa_info = {
                "task_id": item.get("task_id"),
                "syntax_ok": ok,
                "syntax_errors": errors,
                "complexity": complexity_score(raw_code),
            }
            out_f.write(json.dumps(qa_info, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local model evaluation pipeline")
    parser.add_argument("dataset", help="path to dataset jsonl")
    parser.add_argument("dataset_type", choices=["humaneval", "mbpp"], help="dataset type")
    parser.add_argument("--model", default="wizardcoder:7b-python", help="Ollama model name")
    args = parser.parse_args()

    generate_with_model(args.dataset, args.model, "model_outputs.jsonl")
    run_evaluation(args.dataset_type, "model_outputs.jsonl", "results_wizardcoder.jsonl")
    run_qa("results_wizardcoder.jsonl", "results_wizardcoder_qa.jsonl")

    subprocess.run(["python3", "scripts/passk_eval.py", "results_wizardcoder.jsonl", "--ks", "1", "10"])


if __name__ == "__main__":
    main()