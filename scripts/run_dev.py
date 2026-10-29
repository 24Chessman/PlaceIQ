"""Run the pipeline on the 5 DEV requirements only; results -> eval/dev_run.json.   python scripts/run_dev.py"""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import K_RETRIEVE, MODEL  # noqa: E402  (also sets PYTHONUTF8 / HF_HOME)
from src import llm, pipeline  # noqa: E402


def vram():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout
    return int(out.split()[0])


def main():
    reqs = [json.loads(l) for l in (ROOT / "data" / "requirements.jsonl").read_text(encoding="utf-8").splitlines()]
    dev = [r for r in reqs if r["split"] == "dev"]
    assert len(dev) == 5
    baseline = vram()
    peak = {"v": baseline, "stop": False}

    def sample():
        while not peak["stop"]:
            peak["v"] = max(peak["v"], vram())
            time.sleep(0.5)

    threading.Thread(target=sample, daemon=True).start()
    warm = llm.warm_up()
    pipeline.retriever()  # load embedder + index before timing the requirements
    print(f"model={MODEL} warm-up/cold-load={warm:.1f}s k={K_RETRIEVE}", flush=True)
    results = {}
    t0 = time.perf_counter()
    for r in dev:
        res = pipeline.run(r["text"], k=K_RETRIEVE)
        results[r["id"]] = res
        tm = res["timing"]
        print(f"{r['id']}: parse {tm['parse_s']:.1f}s retrieve {tm['retrieve_s']:.2f}s rerank {tm['rerank_s']:.1f}s "
              f"({tm['rerank_per_candidate_s']:.2f}s/cand, {tm['n_candidates']} cand) cached_parse={tm['parse_cached']}",
              flush=True)
    peak["stop"] = True
    out = dict(model=MODEL, k=K_RETRIEVE, cold_load_s=warm, vram_baseline_mib=baseline, vram_peak_mib=peak["v"],
               total_wall_s=time.perf_counter() - t0, results=results)
    (ROOT / "eval").mkdir(exist_ok=True)
    (ROOT / "eval" / "dev_run.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"done in {out['total_wall_s']:.0f}s, peak VRAM {peak['v']} MiB -> eval/dev_run.json")


if __name__ == "__main__":
    main()
