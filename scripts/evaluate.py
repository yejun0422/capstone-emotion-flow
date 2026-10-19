"""
샘플 축어록을 실제 모델로 분석해 samples/answers.json의 정답과 비교한다.

    (backend 가상환경을 켠 상태에서, 프로젝트 최상위 폴더에서)
    python scripts/evaluate.py                              # 튜닝표 + 최종 점수
    python scripts/evaluate.py --window 3 --threshold 0.4   # 특정 값만 보기

실행할 때마다 모델로 샘플을 분석하고, 결과는 화면에만 출력한다. (파일을 만들지 않음)
결과를 남기고 싶으면 python scripts/evaluate.py > 결과.txt 처럼 직접 저장한다.

분석 대상을 고르는 방법은 backend/app/services/pipeline.py와 같다.
(파싱 → 화자 정리 → 마스킹 → 내담자 발화 중 괄호류를 떼고도 내용이 남은 것)
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

# 윈도우에서 결과를 파일로 저장(> out.txt)해도 한글·기호가 깨지지 않게
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services import masking, parser  # noqa: E402
from app.services.text_rules import clean_text, is_analyzable  # noqa: E402

SAMPLES = ROOT / "samples"
TOLERANCE = 2                     # 전환점: 정답 발화 번호 ±2 (내담자 발화 하나)까지 맞은 것으로 본다
WINDOWS = [2, 3, 4, 5]
THRESHOLDS = [round(0.20 + 0.05 * i, 2) for i in range(11)]   # 0.20 ~ 0.70


# ── 1. 모델 점수 모으기 ─────────────────────────────────────

def build_utterances(path: Path):
    """pipeline.py와 같은 방법으로 발화를 만들고, 분석할 내담자 발화를 고른다."""
    rows = parser.parse(path.read_bytes(), path.name)
    names = parser.get_speakers(rows)
    rows = parser.map_speakers(rows)
    rows = masking.mask_utterances(rows, names)
    targets = []
    for r in rows:
        if r["speaker"] == "내담자":
            cleaned = clean_text(r["text"])
            if is_analyzable(cleaned):
                targets.append((r["index"], cleaned))
    return rows, targets


def collect(answers: dict) -> dict:
    from app.services.analyzer import analyze, load_model   # 모델은 필요할 때만 불러온다

    print("모델을 불러오는 중...")
    load_model()
    cache = {"files": {}}
    for f in answers["files"]:
        rows, targets = build_utterances(SAMPLES / f["file"])
        scores = analyze([t for _, t in targets]) if targets else []
        by_index = {i: s for (i, _), s in zip(targets, scores)}
        cache["files"][f["file"]] = [
            {"index": r["index"], "speaker": r["speaker"], "scores": by_index.get(r["index"])}
            for r in rows
        ]
        print(f"  {f['file']}: 내담자 발화 {len(targets)}개 분석")
    print()
    return cache


# ── 2. 발화별 정답률 ────────────────────────────────────────

def similar(a: str, b: str, pairs) -> bool:
    return any({a, b} == set(p) for p in pairs)


def utterance_report(answers, cache, split):
    pairs = answers["similarPairs"]
    rows = []      # (정답 목록, 예측, 1등 점수, 1·2등 차이)
    bad_held = []
    for f in answers["files"]:
        if split and f["split"] != split:
            continue
        utts = {u["index"]: u for u in cache["files"][f["file"]]}
        for idx, labels in f["labels"].items():
            u = utts[int(idx)]
            if labels is None:
                if u["scores"] is not None:
                    bad_held.append((f["file"], idx))
                continue
            if u["scores"] is None:
                bad_held.append((f["file"], idx))
                continue
            ranked = sorted(u["scores"].items(), key=lambda kv: kv[1], reverse=True)
            rows.append((labels, ranked[0][0], ranked[0][1], ranked[0][1] - ranked[1][1], ranked[1][0]))

    n = len(rows)
    strict = sum(1 for lab, top, *_ in rows if top in lab)
    lenient = sum(1 for lab, top, *_ in rows if top in lab or any(similar(top, l, pairs) for l in lab))
    print(f"  발화 {n}개 — 엄격 정답률 {strict / n:.1%}, 완화 정답률 {lenient / n:.1%}")
    if bad_held:
        print(f"  주의: 판단 보류 여부가 정답과 다른 발화 {bad_held}")

    wrong = Counter((lab[0], top) for lab, top, *_ in rows if top not in lab)
    if wrong:
        top5 = ", ".join(f"{a}→{b} {c}개" for (a, b), c in wrong.most_common(5))
        print(f"  자주 틀린 경우 (정답→예측): {top5}")
    return rows


def confidence_report(rows):
    print("\n  1등 점수 구간별 정답률 (엄격) — 확신 낮음 기준(LOW_CONFIDENCE) 정하기용")
    edges = [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
    for lo, hi in zip(edges, edges[1:]):
        part = [r for r in rows if lo <= r[2] < hi]
        if part:
            acc = sum(1 for lab, top, *_ in part if top in lab) / len(part)
            print(f"    {lo:.1f} ~ {min(hi, 1.0):.1f}: {len(part):3d}개  정답률 {acc:5.1%}  {'█' * round(acc * 20)}")

    print("\n  1·2등 점수 차이 구간별 — 복합 감정 기준 정하기용")
    print("    (정답이 두 개인 발화에서, 모델 1·2등이 두 정답과 일치하는지도 같이 봄)")
    edges = [0.0, 0.1, 0.2, 0.3, 0.5, 1.01]
    for lo, hi in zip(edges, edges[1:]):
        part = [r for r in rows if lo <= r[3] < hi]
        if not part:
            continue
        acc = sum(1 for lab, top, *_ in part if top in lab) / len(part)
        top2_hit = sum(1 for lab, top, _, _, second in part if len(lab) > 1 and {top, second} == set(lab))
        dual = sum(1 for lab, *_ in part if len(lab) > 1)
        print(f"    {lo:.1f} ~ {min(hi, 1.0):.1f}: {len(part):3d}개  1등 정답률 {acc:5.1%}"
              + (f"  (정답 두 개짜리 {dual}개 중 1·2등이 정확히 일치 {top2_hit}개)" if dual else ""))


# ── 3. 전환점 ──────────────────────────────────────────────

def score_turning(found, f, lenient):
    optional = set(f["optionalTurningPoints"]) | (set(f["softTurningPoints"]) if lenient else set())
    required = set(f["turningPoints"]) - optional
    hit = {r for r in required if any(abs(r - x) <= TOLERANCE for x in found)}
    fp = [x for x in found if not any(abs(x - r) <= TOLERANCE for r in required | optional)]
    tp_found = len(found) - len(fp)
    return len(hit), len(required), tp_found, len(found)


def turning_scores(answers, cache, split, window, threshold, lenient):
    from app.services.postprocess import find_turning_points

    hit = req = tpf = found_n = 0
    detail = []
    for f in answers["files"]:
        if f["split"] != split:
            continue
        found = find_turning_points(cache["files"][f["file"]], window=window, threshold=threshold)
        h, q, t, n = score_turning(found, f, lenient)
        hit, req, tpf, found_n = hit + h, req + q, tpf + t, found_n + n
        detail.append((f["file"], f["turningPoints"], found))
    recall = hit / req if req else 1.0
    precision = tpf / found_n if found_n else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1, detail


def grid(answers, cache):
    print("== 전환점 튜닝 (튜닝용 6편, 엄격 F1 기준으로 고름)")
    best = None
    table = []
    for w in WINDOWS:
        for t in THRESHOLDS:
            ps, rs, fs, _ = turning_scores(answers, cache, "tune", w, t, lenient=False)
            pl, rl, fl, _ = turning_scores(answers, cache, "tune", w, t, lenient=True)
            table.append((w, t, ps, rs, fs, fl))
            key = (fs, fl, ps)
            if best is None or key > best[0]:
                best = (key, w, t)
    print("  window  threshold   정밀도  재현율  F1(엄격)  F1(완화)")
    for w, t, p, r, fs, fl in sorted(table, key=lambda x: (-x[4], -x[5]))[:10]:
        mark = " ◀" if (w, t) == best[1:] else ""
        print(f"    {w}       {t:.2f}      {p:5.1%}  {r:5.1%}   {fs:.3f}     {fl:.3f}{mark}")
    return best[1], best[2]


def chance_f1(answers, cache, split, detail, lenient, trials=300):
    """같은 개수의 전환점을 분석된 내담자 발화 중 무작위로 찍었을 때의 평균 F1 (우연 기준선)."""
    rng = random.Random(0)
    files = {f["file"]: f for f in answers["files"]}
    total = 0.0
    for _ in range(trials):
        hit = req = tpf = found_n = 0
        for name, _, found in detail:
            f = files[name]
            pool = [u["index"] for u in cache["files"][name] if u["scores"]]
            fake = sorted(rng.sample(pool, min(len(found), len(pool))))
            h, q, t, n = score_turning(fake, f, lenient)
            hit, req, tpf, found_n = hit + h, req + q, tpf + t, found_n + n
        r = hit / req if req else 1.0
        p = tpf / found_n if found_n else 1.0
        total += 2 * p * r / (p + r) if p + r else 0.0
    return total / trials


def show(answers, cache, split, w, t):
    for lenient in (False, True):
        p, r, f1, detail = turning_scores(answers, cache, split, w, t, lenient)
        base = chance_f1(answers, cache, split, detail, lenient)
        print(f"  {'완화' if lenient else '엄격'}: 정밀도 {p:.1%}, 재현율 {r:.1%}, F1 {f1:.3f}"
              f"  (같은 개수를 무작위로 찍으면 F1 {base:.3f})")
    for name, ans, found in detail:
        print(f"    {name:24s} 정답 {ans}  찾음 {found}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int)
    ap.add_argument("--threshold", type=float)
    args = ap.parse_args()

    answers = json.loads((SAMPLES / "answers.json").read_text(encoding="utf-8"))
    cache = collect(answers)

    for split, name in (("tune", "튜닝용 6편"), ("test", "평가용 4편"), (None, "전체 10편")):
        print(f"== 발화별 감정 ({name})")
        rows = utterance_report(answers, cache, split)
        if split is None:
            confidence_report(rows)
        print()

    if args.window and args.threshold is not None:
        w, t = args.window, args.threshold
    else:
        w, t = grid(answers, cache)
        print()
    print(f"== 전환점 — 튜닝용 6편 (window={w}, threshold={t})")
    show(answers, cache, "tune", w, t)
    print(f"\n== 전환점 — 평가용 4편 (window={w}, threshold={t}) ← 보고서용 최종 점수")
    show(answers, cache, "test", w, t)


if __name__ == "__main__":
    main()