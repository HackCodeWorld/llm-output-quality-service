import argparse
import json
import math
from collections import defaultdict


def estimate_pass_at_k(n: int, c: int, k: int) -> float:
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def main():
    parser = argparse.ArgumentParser(description="Compute pass@k from result file")
    parser.add_argument("results", help="path to results.jsonl")
    parser.add_argument("--ks", nargs="*", type=int, default=[1, 10], help="k values")
    args = parser.parse_args()

    grouped = defaultdict(list)
    with open(args.results, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            tid = item.get("task_id")
            if tid is None:
                continue
            passed = all(tr.get("passed") for tr in item.get("test_results", []))
            grouped[tid].append(passed)

    if not grouped:
        print("No task_id found in results")
        return

    for k in args.ks:
        acc = 0.0
        for results in grouped.values():
            acc += estimate_pass_at_k(len(results), sum(results), k)
        acc /= len(grouped)
        print(f"pass@{k}: {acc:.4f}")


if __name__ == "__main__":
    main()