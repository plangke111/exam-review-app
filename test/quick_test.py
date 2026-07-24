"""快速回归测试 - 每样本1次"""
import json, time, os, sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.essay_grader import EnglishGrader, PoliticsGrader
from run_tests import TESTS

eg = EnglishGrader()
pg = PoliticsGrader()
results = {}
passed = 0
total = len(TESTS)
mae_list = []

print(f"Quick Regression Test - {datetime.now().strftime('%H:%M:%S')}")
print(f"Model: {os.environ.get('LLM_MODEL','?')} | Samples: {total}")
print()

for tc in TESTS:
    tid = tc["id"]
    grader = pg if tc["type"] == "politics" else eg
    start = time.time()
    try:
        if tc["type"] == "english_big":
            r = grader.grade_big(student_answer=tc["answer"], prompt=tc["prompt"],
                                  exam_type=tc.get("exam","英语一"), max_score=tc["max"])
        elif tc["type"] == "english_small":
            r = grader.grade_small(student_answer=tc["answer"], prompt=tc["prompt"],
                                    exam_type=tc.get("exam","英语一"), max_score=tc["max"])
        else:
            r = grader.grade_single(student_answer=tc["answer"], question=tc["question"],
                                     materials=tc["materials"], max_score=tc["max"],
                                     subject_hint="马原",
                                     reference_scoring_points=tc.get("scoring",""))
        score = r.get("score", "?")
        elapsed = time.time() - start
        in_range = tc["low"] <= score <= tc["high"] if isinstance(score, (int, float)) else False
        delta = abs(score - tc["target"]) if isinstance(score, (int, float)) else 999
        mae_list.append(delta)
        if in_range:
            passed += 1
        status = "OK" if in_range else ("LOW" if isinstance(score,(int,float)) and score < tc["low"] else "HIGH")
        print(f"[{status:6s}] {tid} score={score} target={tc['target']}[{tc['low']}-{tc['high']}] t={elapsed:.0f}s")
        results[tid] = {"score": score, "band": r.get("band","?"), "delta": delta, "in_range": in_range}
    except Exception as e:
        print(f"[ERROR] {tid}: {str(e)[:100]}")
        results[tid] = {"score": None, "error": str(e)[:200]}

# Summary
print(f"\n{'='*60}")
print(f"Pass: {passed}/{total} ({passed/total*100:.0f}%)")
if mae_list:
    import statistics
    print(f"MAE: {statistics.mean(mae_list):.2f} Median: {statistics.median(mae_list):.1f} Max: {max(mae_list)}")

failed = [(tid, r) for tid, r in results.items() if not r.get("in_range", False)]
if failed:
    print(f"\nFailed ({len(failed)}):")
    for tid, r in failed:
        tc = [t for t in TESTS if t["id"] == tid][0]
        s = r.get("score","ERR")
        print(f"  {tid}: got={s} target={tc['target']}[{tc['low']}-{tc['high']}]")

Path("test/quick_results.json").write_text(
    json.dumps({"time": datetime.now().isoformat(), "passed": passed, "total": total,
                "results": {tid: {"score": v.get("score"), "in_range": v.get("in_range")}
                           for tid, v in results.items()}},
               ensure_ascii=False, indent=2))
print("\nSaved: test/quick_results.json")
