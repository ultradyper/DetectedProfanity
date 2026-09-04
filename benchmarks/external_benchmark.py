#!/usr/bin/env python3
"""Внешний бенчмарк на публичных словарях LDNOOBW / zacanger / clean."""

from __future__ import annotations

import json
import pathlib
import sys
import time

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from detected_profanity import ProfanityDetector


def load_en_ldnoob():
    p = pathlib.Path("/tmp/en_ldnoob.txt")
    if not p.exists():
        return []
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_ru_ldnoob():
    p = pathlib.Path("/tmp/ru_ldnoob.txt")
    if not p.exists():
        return []
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_zacanger():
    p = pathlib.Path("/tmp/zacanger.json")
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return [w.strip() for w in data if isinstance(w, str) and w.strip()]
    except Exception:
        return []


def load_clean_en(n=1000):
    p = pathlib.Path("/tmp/clean_en.txt")
    if not p.exists():
        return ["the", "and", "hello", "world"][:n]
    lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip().isalpha()][:n]
    return lines[:n]


def load_clean_ru():
    from benchmarks.dataset import RU_CLEAN

    return RU_CLEAN


def eval_detector(name, fn, profane_lists, clean_lists):
    total_prof = len(sum(profane_lists, []))
    total_clean = len(sum(clean_lists, []))
    tp = 0
    fp = 0
    start = time.time()
    for lst in profane_lists:
        for w in lst:
            try:
                pred = bool(fn(w))
            except Exception:
                pred = False
            if pred:
                tp += 1
    for lst in clean_lists:
        for w in lst:
            try:
                pred = bool(fn(w))
            except Exception:
                pred = False
            if pred:
                fp += 1
    elapsed = time.time() - start
    fn_missed = total_prof - tp
    tn = total_clean - fp
    acc = (tp + tn) / (total_prof + total_clean) if (total_prof + total_clean) else 0
    prec = tp / (tp + fp) if (tp + fp) else 0
    rec = tp / (tp + fn_missed) if (tp + fn_missed) else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
    return {
        "name": name,
        "total_prof": total_prof,
        "total_clean": total_clean,
        "tp": tp, "fp": fp, "fn": fn_missed, "tn": tn,
        "accuracy": acc, "precision": prec, "recall": rec, "f1": f1,
        "time": elapsed,
    }


def main():
    print("=" * 80)
    print(" Внешний бенчмарк на публичных списках из интернета")
    print("=" * 80)
    en_ldnoob = load_en_ldnoob()
    ru_ldnoob = load_ru_ldnoob()
    zacanger = load_zacanger()
    clean_en = load_clean_en(1000)
    clean_ru = load_clean_ru()
    print(f"Loaded: en_ldnoob={len(en_ldnoob)} ru_ldnoob={len(ru_ldnoob)} zacanger={len(zacanger)} clean_en={len(clean_en)} clean_ru={len(clean_ru)}")

    det = ProfanityDetector()
    det_fn = lambda t: det.contains_profanity(t)

    try:
        from better_profanity import profanity as bp
        bp.load_censor_words()
        bp_fn = lambda t: bp.contains_profanity(t)
        bp_ok = True
    except Exception as e:
        print(f"better-profanity not available: {e}")
        bp_fn = None; bp_ok = False

    try:
        from profanity_check import predict as pc_predict
        pc_fn = lambda t: bool(pc_predict([t])[0] == 1) if t.strip() else False
        pc_fn("hello")
        pc_ok = True
    except Exception as e:
        print(f"profanity-check not available: {e}")
        pc_fn = None; pc_ok = False

    profane_lists = [en_ldnoob, zacanger]
    profane_ru = [ru_ldnoob]
    clean_lists = [clean_en]

    print("\n--- EN PROFANITY RECALL (LDNOOBW + zacanger) ---")
    for name, fn, ok in [("detected-profanity", det_fn, True), ("better-profanity", bp_fn, bp_ok), ("profanity-check", pc_fn, pc_ok)]:
        if not ok or fn is None:
            print(f"{name:20} SKIPPED")
            continue
        res = eval_detector(name, fn, profane_lists, [clean_en])
        print(f"{name:20} acc={res['accuracy']:.1%} prec={res['precision']:.1%} rec={res['recall']:.1%} f1={res['f1']:.1%} tp={res['tp']}/{res['total_prof']} fp={res['fp']}/{res['total_clean']} time={res['time']:.2f}s")

    print("\n--- RU PROFANITY RECALL (LDNOOBW ru) ---")
    for name, fn, ok in [("detected-profanity", det_fn, True), ("better-profanity", bp_fn, bp_ok), ("profanity-check", pc_fn, pc_ok)]:
        if not ok or fn is None:
            print(f"{name:20} SKIPPED")
            continue
        res = eval_detector(name, fn, profane_ru, [clean_ru])
        print(f"{name:20} acc={res['accuracy']:.1%} prec={res['precision']:.1%} rec={res['recall']:.1%} f1={res['f1']:.1%} tp={res['tp']}/{res['total_prof']} fp={res['fp']}/{res['total_clean']}")

    print("\n--- CLEAN FP ONLY (EN 1000) ---")
    for name, fn, ok in [("detected-profanity", det_fn, True), ("better-profanity", bp_fn, bp_ok), ("profanity-check", pc_fn, pc_ok)]:
        if not ok:
            continue
        fp = sum(1 for w in clean_en if fn(w))
        print(f"{name:20} FP={fp}/{len(clean_en)} FP_rate={fp/len(clean_en):.1%}")

    print("\n--- Примеры ---")
    examples = ["на#хуя", "х*й", "0хуеть", "бл@ть", "п..здец", "х у й", "bitch", "f*ck", "sh*t", "pizdec", "hui"]
    for ex in examples:
        our = det_fn(ex)
        try:
            bp_res = bp_fn(ex) if bp_ok else "SKIP"
        except Exception:
            bp_res = "ERR"
        try:
            pc_res = pc_fn(ex) if pc_ok else "SKIP"
        except Exception:
            pc_res = "ERR"
        print(f"{ex:15} ours={our} better={bp_res} pc={pc_res}")


if __name__ == "__main__":
    main()
