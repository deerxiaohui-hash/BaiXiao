"""检索质量评测脚本：对 eval_qa.json 跑 Recall@1 / Recall@3 / MRR，并对比 tfidf 与 hybrid 后端。

运行：cd backend && ./venv/Scripts/python.exe tests/evaluate.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.services.vector_store import vector_store

EVAL_FILE = Path(__file__).parent / "eval_qa.json"


def evaluate_backend(backend: str, cases: list, k: int = 5) -> dict:
    recall1 = recall3 = 0
    mrr_sum = 0.0
    garbage_ratios = []
    misses = []

    for case in cases:
        results = vector_store.search(case["question"], k=k, backend=backend)
        hits_rank = None
        for rank, (doc, _) in enumerate(results, start=1):
            if any(kw in doc.page_content for kw in case["expect_keywords"]):
                hits_rank = rank
                break

        if hits_rank:
            mrr_sum += 1.0 / hits_rank
            if hits_rank <= 1:
                recall1 += 1
            if hits_rank <= 3:
                recall3 += 1
        else:
            misses.append(case["question"])

        topk = results[:k]
        if topk:
            below = sum(1 for _, s in topk if s < 0.05)
            garbage_ratios.append(below / len(topk))

    n = len(cases)
    return {
        "backend": backend,
        "recall@1": recall1 / n,
        "recall@3": recall3 / n,
        "mrr": mrr_sum / n,
        "garbage_ratio": sum(garbage_ratios) / len(garbage_ratios) if garbage_ratios else 0.0,
        "misses": misses,
    }


def main():
    data = json.loads(EVAL_FILE.read_text(encoding="utf-8"))
    cases = data["cases"]
    print(f"评测集: {len(cases)} 条 | 索引片段数: {len(vector_store.chunks)}")
    print(f"当前配置: backend={settings.RETRIEVAL_BACKEND}, embedding={settings.EMBEDDING_MODEL}\n")

    for backend in ("tfidf", "hybrid"):
        r = evaluate_backend(backend, cases)
        print(f"[{r['backend']:>6}] Recall@1={r['recall@1']:.0%}  Recall@3={r['recall@3']:.0%}  "
              f"MRR={r['mrr']:.3f}  top5低相关占比={r['garbage_ratio']:.0%}")
        for q in r["misses"]:
            print(f"    ✗ 未命中: {q}")
        print()


if __name__ == "__main__":
    main()
