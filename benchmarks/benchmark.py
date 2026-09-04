#!/usr/bin/env python3
"""Benchmark: detected-profanity vs better-profanity / profanity-check / censure."""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_THIS = Path(__file__).resolve()
_PROJECT_ROOT = _THIS.parents[1]
_BENCH_DIR = _THIS.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

RU_CLEAN: list[tuple[str, bool, str]] = [
    ("Привет, как дела?", False, "ru_clean"),
    ("Сегодня хорошая погода", False, "ru_clean"),
    ("Я люблю читать книги", False, "ru_clean"),
    ("Мандарин очень вкусный", False, "ru_clean"),
    ("Мы поедем на море летом", False, "ru_clean"),
    ("Спасибо за помощь", False, "ru_clean"),
    ("Художник рисует картину", False, "ru_clean"),
    ("Собрание началось вовремя", False, "ru_clean"),
    ("Добрый день, уважаемые коллеги", False, "ru_clean"),
    ("На столе лежит книга", False, "ru_clean"),
]

RU_PROFANITY: list[tuple[str, bool, str]] = [
    ("Пошел на хуй", True, "ru_profanity"),
    ("Это полный пиздец", True, "ru_profanity"),
    ("Охуеть, как круто", True, "ru_profanity"),
    ("Блядь, я забыл ключи", True, "ru_profanity"),
    ("Ты еблан конченый", True, "ru_profanity"),
    ("Хуйня какая-то", True, "ru_profanity"),
    ("Заебал ты меня", True, "ru_profanity"),
    ("Сука, ты ебаная", True, "ru_profanity"),
    ("Бляди на районе", True, "ru_profanity"),
    ("Нахуя ты это сделал", True, "ru_profanity"),
]

RU_MASKED: list[tuple[str, bool, str]] = [
    ("на#хуя ты это сделал", True, "ru_masked"),
    ("х*й с ним", True, "ru_masked"),
    ("0хуеть, вот это да", True, "ru_masked"),
    ("бл@ть, опять опоздал", True, "ru_masked"),
    ("п..здец какой-то", True, "ru_masked"),
    ("х у й знает что", True, "ru_masked"),
    ("б.л.я буду", True, "ru_masked"),
    ("бляяяя, как же так", True, "ru_masked"),
    ("хуи пинаешь целый день", True, "ru_masked"),
    ("пздец просто", True, "ru_masked"),
]

EN_CLEAN: list[tuple[str, bool, str]] = [
    ("The sunshine is beautiful", False, "en_clean"),
    ("The assassin was in the game", False, "en_clean"),
    ("This is a fantastic opportunity", False, "en_clean"),
    ("Enjoy your weekend", False, "en_clean"),
    ("The weather is nice today", False, "en_clean"),
    ("I will call you later", False, "en_clean"),
    ("Looking forward to meeting you", False, "en_clean"),
    ("Wishing you all the best", False, "en_clean"),
    ("Congratulations on your success", False, "en_clean"),
    ("Travel broadens the mind", False, "en_clean"),
]

EN_PROFANITY: list[tuple[str, bool, str]] = [
    ("What the fuck is this", True, "en_profanity"),
    ("This is bullshit", True, "en_profanity"),
    ("You are a dumb ass", True, "en_profanity"),
    ("Shit happens", True, "en_profanity"),
    ("Fucking hell", True, "en_profanity"),
    ("You bastard", True, "en_profanity"),
    ("Go fuck yourself", True, "en_profanity"),
    ("This is a fucking nightmare", True, "en_profanity"),
    ("Asshole, move away", True, "en_profanity"),
    ("Bitch, please", True, "en_profanity"),
]

EN_MASKED: list[tuple[str, bool, str]] = [
    ("f#ck you", True, "en_masked"),
    ("sh*t happens", True, "en_masked"),
    ("f@ck this shit", True, "en_masked"),
    ("b!tch please", True, "en_masked"),
    ("a$$hole just left", True, "en_masked"),
    ("f u c k this", True, "en_masked"),
    ("b.i.t.c.h please", True, "en_masked"),
    ("fuuuuuck you", True, "en_masked"),
    ("sh!t happens again", True, "en_masked"),
    ("fck you buddy", True, "en_masked"),
]

DATASET: list[tuple[str, bool, str]] = RU_CLEAN + RU_PROFANITY + RU_MASKED + EN_CLEAN + EN_PROFANITY + EN_MASKED

assert len(RU_CLEAN) == 10 and len(RU_PROFANITY) == 10 and len(RU_MASKED) == 10, "RU must be 10+10+10"
assert len(EN_CLEAN) == 10 and len(EN_PROFANITY) == 10 and len(EN_MASKED) == 10, "EN must be 10+10+10"
assert len(DATASET) == 60, f"Total must be 60, got {len(DATASET)}"


@dataclass
class Metrics:
    name: str
    status: str
    detail: str = ""
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0
    total: int = 0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    time_sec: float = 0.0
    avg_ms: float = 0.0
    ru_accuracy: float = 0.0
    en_accuracy: float = 0.0
    masked_accuracy: float = 0.0
    clean_accuracy: float = 0.0
    open_profanity_accuracy: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_detected_profanity() -> tuple[Callable[[str], bool] | None, str]:
    try:
        from detected_profanity import ProfanityDetector  # type: ignore

        det = ProfanityDetector(lang="all")

        def fn(text: str) -> bool:
            return bool(det.contains_profanity(text))

        fn("warmup хуй fuck")
        return fn, "ok"
    except Exception as e:
        return None, f"error: {e}\n{traceback.format_exc()}"


def _load_better_profanity() -> tuple[Callable[[str], bool] | None, str]:
    try:
        from better_profanity import profanity as bp  # type: ignore

        try:
            bp.load_censor_words()
        except Exception:
            pass

        def fn(text: str) -> bool:
            return bool(bp.contains_profanity(text))

        fn("warmup hello")
        return fn, "ok"
    except ImportError as e:
        return None, f"skipped (not installed): {e}"
    except Exception as e:
        return None, f"error: {e}\n{traceback.format_exc()}"


def _load_profanity_check() -> tuple[Callable[[str], bool] | None, str]:
    last_err = ""
    for mod_name in ("profanity_check", "profanity-check", "alt_profanity_check"):
        try:
            import importlib

            mod = importlib.import_module("profanity_check")
            if hasattr(mod, "predict"):
                predict = getattr(mod, "predict")

                def fn(text: str, _p=predict) -> bool:  # type: ignore[no-redef]
                    try:
                        res = _p([text])
                        v = res[0]
                        return bool(int(v) == 1)
                    except Exception:
                        return False

                try:
                    fn("hello world")
                except Exception as e:
                    return None, f"error during warmup: {e}"
                return fn, "ok"
            else:
                last_err = f"module {mod_name} has no predict"
                continue
        except ImportError as e:
            last_err = f"not installed: {e}"
            continue
        except Exception as e:
            last_err = f"error: {e}"
            continue
    return None, f"skipped ({last_err})"


def _load_censure() -> tuple[Callable[[str], bool] | None, str]:
    try:
        import importlib

        last_err = ""
        for mod_path, cls_name in [
            ("censure", "Censor"),
            ("censure.censor", "Censor"),
        ]:
            try:
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name, None)
                if cls is None:
                    last_err = f"{mod_path}.{cls_name} not found"
                    continue
                try:
                    inst = cls()
                except TypeError:
                    try:
                        inst = cls(lang="en")
                    except Exception as e:
                        last_err = f"cannot instantiate {cls_name}: {e}"
                        continue

                candidates = [
                    "is_profane", "is_profane_word", "is_bad_word", "is_bad",
                    "contains_profanity", "contains_profane", "check", "is_censored",
                    "get_profane_words", "clean_line", "censor",
                ]
                fn: Callable[[str], bool] | None = None
                for meth_name in candidates:
                    if hasattr(inst, meth_name):
                        meth = getattr(inst, meth_name)
                        if meth_name in ("get_profane_words",):

                            def _fn(text: str, _m=meth) -> bool:  # type: ignore
                                try:
                                    words = _m(text)
                                    return bool(words)
                                except Exception:
                                    return False

                            fn = _fn
                            break
                        elif meth_name in ("clean_line", "censor"):

                            def _fn2(text: str, _m=meth) -> bool:  # type: ignore
                                try:
                                    cleaned = _m(text)
                                    return cleaned != text
                                except Exception:
                                    return False

                            fn = _fn2
                            break
                        else:

                            def _fn3(text: str, _m=meth) -> bool:  # type: ignore
                                try:
                                    return bool(_m(text))
                                except Exception:
                                    return False

                            fn = _fn3
                            break
                if fn is None:
                    if callable(inst):

                        def _call_fn(text: str, _inst=inst) -> bool:  # type: ignore
                            try:
                                return bool(_inst(text))
                            except Exception:
                                return False

                        fn = _call_fn
                    else:
                        last_err = f"{cls_name} has no known profanity method (attrs={dir(inst)[:20]})"
                        continue

                try:
                    fn("hello world")
                except Exception as e:
                    last_err = f"warmup failed: {e}"
                    continue
                return fn, "ok"
            except ImportError as e:
                last_err = f"not installed: {e}"
                continue
            except Exception as e:
                last_err = f"error: {e}"
                continue
        return None, f"skipped ({last_err})"
    except Exception as e:
        return None, f"error: {e}\n{traceback.format_exc()}"


LIBS: list[tuple[str, Callable[[], tuple[Callable[[str], bool] | None, str]]]] = [
    ("detected-profanity", _load_detected_profanity),
    ("better-profanity", _load_better_profanity),
    ("profanity-check", _load_profanity_check),
    ("censure", _load_censure),
]


def compute_metrics(
    name: str,
    check_fn: Callable[[str], bool] | None,
    status_msg: str,
    dataset: list[tuple[str, bool, str]] = DATASET,
) -> tuple[Metrics, list[dict[str, Any]]]:
    m = Metrics(name=name, status="ok", total=len(dataset))
    details: list[dict[str, Any]] = []

    if check_fn is None:
        if "skipped" in status_msg.lower() or "not installed" in status_msg.lower():
            m.status = "skipped"
        else:
            m.status = "error"
        m.detail = status_msg
        return m, details

    ru_ok = ru_total = 0
    en_ok = en_total = 0
    masked_ok = masked_total = 0
    clean_ok = clean_total = 0
    open_ok = open_total = 0

    tp = tn = fp = fn_cnt = 0

    start = time.perf_counter()
    for text, expected, cat in dataset:
        try:
            pred = bool(check_fn(text))
        except Exception as e:
            pred = False
            details.append({"text": text, "expected": expected, "predicted": pred, "category": cat, "error": str(e)})
        else:
            details.append({"text": text, "expected": expected, "predicted": pred, "category": cat})

        ok = pred == expected
        if expected and pred:
            tp += 1
        elif not expected and not pred:
            tn += 1
        elif not expected and pred:
            fp += 1
        elif expected and not pred:
            fn_cnt += 1

        if cat.startswith("ru"):
            ru_total += 1
            if ok:
                ru_ok += 1
        if cat.startswith("en"):
            en_total += 1
            if ok:
                en_ok += 1
        if "masked" in cat:
            masked_total += 1
            if ok:
                masked_ok += 1
        if "clean" in cat:
            clean_total += 1
            if ok:
                clean_ok += 1
        if "profanity" in cat and "masked" not in cat:
            open_total += 1
            if ok:
                open_ok += 1
        elif cat in ("ru_profanity", "en_profanity"):
            open_total += 1
            if ok:
                open_ok += 1

    elapsed = time.perf_counter() - start

    total = len(dataset)
    accuracy = (tp + tn) / total if total else 0.0
    precision = (tp / (tp + fp)) if (tp + fp) else 0.0
    recall = (tp / (tp + fn_cnt)) if (tp + fn_cnt) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    m.tp, m.tn, m.fp, m.fn = tp, tn, fp, fn_cnt
    m.accuracy = accuracy
    m.precision = precision
    m.recall = recall
    m.f1 = f1
    m.time_sec = elapsed
    m.avg_ms = (elapsed / total * 1000) if total else 0.0
    m.ru_accuracy = (ru_ok / ru_total) if ru_total else 0.0
    m.en_accuracy = (en_ok / en_total) if en_total else 0.0
    m.masked_accuracy = (masked_ok / masked_total) if masked_total else 0.0
    m.clean_accuracy = (clean_ok / clean_total) if clean_total else 0.0
    m.open_profanity_accuracy = (open_ok / open_total) if open_total else 0.0

    return m, details


def _fmt_pct(x: float) -> str:
    return f"{x*100:5.1f}%"


def _fmt_float(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}"


def print_table(metrics: list[Metrics]) -> None:
    def sort_key(m: Metrics):
        status_order = {"ok": 0, "error": 1, "skipped": 2}
        return (status_order.get(m.status, 9), -m.accuracy if m.status == "ok" else 0)

    metrics_sorted = sorted(metrics, key=sort_key)

    headers = ["Library", "Status", "Acc", "Prec", "Rec", "F1", "Time(s)", "ms/txt", "TP", "TN", "FP", "FN"]
    rows: list[list[str]] = []
    for m in metrics_sorted:
        if m.status == "ok":
            rows.append([
                m.name,
                m.status,
                _fmt_pct(m.accuracy),
                _fmt_pct(m.precision),
                _fmt_pct(m.recall),
                _fmt_pct(m.f1),
                _fmt_float(m.time_sec, 4),
                _fmt_float(m.avg_ms, 2),
                str(m.tp),
                str(m.tn),
                str(m.fp),
                str(m.fn),
            ])
        else:
            rows.append([
                m.name,
                m.status,
                "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
            ])

    cols = list(zip(*([headers] + rows))) if rows else [headers]
    col_w = [max(len(str(v)) for v in col) for col in cols]

    def sep(char: str = "-"):
        return "+" + "+".join(char * (w + 2) for w in col_w) + "+"

    def fmt_row(vals: list[str]) -> str:
        return "| " + " | ".join(str(v).ljust(w) for v, w in zip(vals, col_w)) + " |"

    print(sep("-"))
    print(fmt_row(headers))
    print(sep("="))
    for r in rows:
        print(fmt_row(r))
    print(sep("-"))

    for m in metrics_sorted:
        if m.status != "ok":
            print(f"  {m.name}: {m.detail.splitlines()[0][:120]}")

    ok_metrics = [m for m in metrics_sorted if m.status == "ok"]
    if ok_metrics:
        print("\nPer-category accuracy:")
        headers2 = ["Library", "RU (30)", "EN (30)", "Clean (20)", "Open (20)", "Masked (20)"]
        rows2: list[list[str]] = []
        for m in ok_metrics:
            rows2.append([
                m.name,
                _fmt_pct(m.ru_accuracy),
                _fmt_pct(m.en_accuracy),
                _fmt_pct(m.clean_accuracy),
                _fmt_pct(m.open_profanity_accuracy),
                _fmt_pct(m.masked_accuracy),
            ])
        cols2 = list(zip(*([headers2] + rows2)))
        col_w2 = [max(len(str(v)) for v in col) for col in cols2]

        def sep2(char="-"):
            return "+" + "+".join(char * (w + 2) for w in col_w2) + "+"

        def fmt_row2(vals):
            return "| " + " | ".join(str(v).ljust(w) for v, w in zip(vals, col_w2)) + " |"

        print(sep2("-"))
        print(fmt_row2(headers2))
        print(sep2("="))
        for r in rows2:
            print(fmt_row2(r))
        print(sep2("-"))

    if ok_metrics:
        best_acc = max(ok_metrics, key=lambda x: x.accuracy)
        best_f1 = max(ok_metrics, key=lambda x: x.f1)
        best_recall = max(ok_metrics, key=lambda x: x.recall)
        best_prec = max(ok_metrics, key=lambda x: x.precision)
        fastest = min(ok_metrics, key=lambda x: x.time_sec)
        best_masked = max(ok_metrics, key=lambda x: x.masked_accuracy)
        print("\nSummary:")
        print(f"  Best accuracy  : {best_acc.name} ({_fmt_pct(best_acc.accuracy)})")
        print(f"  Best F1        : {best_f1.name} ({_fmt_pct(best_f1.f1)})")
        print(f"  Best recall    : {best_recall.name} ({_fmt_pct(best_recall.recall)})")
        print(f"  Best precision : {best_prec.name} ({_fmt_pct(best_prec.precision)})")
        print(f"  Best masked    : {best_masked.name} ({_fmt_pct(best_masked.masked_accuracy)})")
        print(f"  Fastest        : {fastest.name} ({_fmt_float(fastest.time_sec,4)}s total, {_fmt_float(fastest.avg_ms,2)} ms/txt)")
        our = next((m for m in ok_metrics if m.name == "detected-profanity"), None)
        if our and our == best_acc:
            print("  >>> detected-profanity — лидер по accuracy <<<")
        if our and our == best_masked:
            print("  >>> detected-profanity — лидер по устойчивости к маскировкам <<<")


def try_plot(metrics: list[Metrics], out_path: Path) -> bool:
    ok_metrics = [m for m in metrics if m.status == "ok"]
    if not ok_metrics:
        print("[plot] нет OK-метрик — график не строится")
        return False
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        print("[plot] matplotlib не установлен — график пропущен (pip install matplotlib)")
        return False
    except Exception as e:
        print(f"[plot] не удалось импортировать matplotlib: {e}")
        return False

    names = [m.name for m in ok_metrics]
    acc = [m.accuracy * 100 for m in ok_metrics]
    prec = [m.precision * 100 for m in ok_metrics]
    rec = [m.recall * 100 for m in ok_metrics]
    f1 = [m.f1 * 100 for m in ok_metrics]
    times_ms = [m.avg_ms for m in ok_metrics]

    colors_acc = "#4C78A8"
    colors_prec = "#F58518"
    colors_rec = "#54A24B"
    colors_f1 = "#E45756"
    color_time = "#72B7B2"

    n = len(names)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(8, n * 1.6), 9), gridspec_kw={"height_ratios": [3, 1]})
    fig.suptitle("Benchmark: detected-profanity vs alternatives (60 фраз: 30 RU + 30 EN)", fontsize=13, fontweight="bold", y=0.98)

    x = range(n)
    w = 0.18
    offsets = [-1.5 * w, -0.5 * w, 0.5 * w, 1.5 * w]
    bars1 = ax1.bar([i + offsets[0] for i in x], acc, width=w, label="Accuracy", color=colors_acc, edgecolor="white", linewidth=0.8)
    bars2 = ax1.bar([i + offsets[1] for i in x], prec, width=w, label="Precision", color=colors_prec, edgecolor="white", linewidth=0.8)
    bars3 = ax1.bar([i + offsets[2] for i in x], rec, width=w, label="Recall", color=colors_rec, edgecolor="white", linewidth=0.8)
    bars4 = ax1.bar([i + offsets[3] for i in x], f1, width=w, label="F1", color=colors_f1, edgecolor="white", linewidth=0.8)

    ax1.set_xticks(list(x))
    ax1.set_xticklabels(names, rotation=12, ha="right", fontsize=10)
    ax1.set_ylabel("Метрика, %", fontsize=11)
    ax1.set_ylim(0, 105)
    ax1.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax1.grid(axis="y", linestyle="--", alpha=0.35)
    ax1.legend(loc="upper left", ncols=4, fontsize=9, framealpha=0.95)
    ax1.set_title("Accuracy / Precision / Recall / F1", fontsize=11, pad=10)

    for bars in (bars1, bars2, bars3, bars4):
        for bar in bars:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 1, f"{h:.0f}%", ha="center", va="bottom", fontsize=7.5, color="#333333")

    bars_t = ax2.bar(list(x), times_ms, width=0.5, color=color_time, edgecolor="white", linewidth=0.8)
    if times_ms and max(times_ms) > 0 and (max(times_ms) / max(min(times_ms), 0.01) > 12):
        ax2.set_yscale("log")
        ax2.set_ylabel("ms / фраза (log)", fontsize=10)
    else:
        ax2.set_ylabel("ms / фраза", fontsize=10)
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(names, rotation=12, ha="right", fontsize=10)
    ax2.grid(axis="y", linestyle="--", alpha=0.35)
    ax2.set_title("Скорость (меньше — лучше)", fontsize=11, pad=10)
    for bar, v in zip(bars_t, times_ms):
        label = f"{v:.2f} ms" if v < 10 else f"{v:.1f} ms"
        y = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, y * 1.08 if ax2.get_yscale() == "log" else y + max(times_ms) * 0.03,
                 label, ha="center", va="bottom", fontsize=8, color="#333333")

    fig.text(0.01, 0.01,
             "Датасет: 60 фраз | RU: 10 clean + 10 open + 10 masked | EN: 10 clean + 10 open + 10 masked",
             fontsize=7, color="#666666", ha="left", va="bottom", wrap=True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(out_path), dpi=160, bbox_inches="tight", facecolor="white")
        print(f"[plot] график сохранён: {out_path}")
        alt = out_path.with_suffix(".png")
        if alt != out_path:
            fig.savefig(str(alt), dpi=160, bbox_inches="tight")
        plt.close(fig)
        return True
    except Exception as e:
        print(f"[plot] ошибка сохранения: {e}")
        plt.close(fig)
        return False


def run_benchmark(
    dataset: list[tuple[str, bool, str]] = DATASET,
    json_path: Path | None = None,
    png_path: Path | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    if json_path is None:
        json_path = _BENCH_DIR / "results.json"
    if png_path is None:
        png_path = _BENCH_DIR / "benchmark.png"

    print("=" * 72)
    print(" Benchmark: detected-profanity vs alternatives")
    print("=" * 72)
    print(f" Датасет: {len(dataset)} фраз  (RU 30 + EN 30)")
    print(f"   RU clean: {len(RU_CLEAN)}, RU open: {len(RU_PROFANITY)}, RU masked: {len(RU_MASKED)}")
    print(f"   EN clean: {len(EN_CLEAN)}, EN open: {len(EN_PROFANITY)}, EN masked: {len(EN_MASKED)}")
    print(f" Время: {datetime.now(timezone.utc).isoformat()}")
    print("-" * 72)

    loaded: list[tuple[str, Callable[[str], bool] | None, str]] = []
    for name, loader in LIBS:
        fn, msg = loader()
        status = "OK" if fn is not None else ("SKIPPED" if "skipped" in msg.lower() or "not installed" in msg.lower() else "ERROR")
        loaded.append((name, fn, msg))
        if verbose:
            print(f" [{status:7s}] {name:22s} — {msg.splitlines()[0][:90]}")

    print("-" * 72)
    print(" Прогон...")
    all_metrics: list[Metrics] = []
    all_details: dict[str, list[dict[str, Any]]] = {}

    for name, fn, msg in loaded:
        metrics, details = compute_metrics(name, fn, msg, dataset)
        all_metrics.append(metrics)
        all_details[name] = details
        if verbose and metrics.status == "ok":
            print(f"  {name:22s} acc={_fmt_pct(metrics.accuracy)} prec={_fmt_pct(metrics.precision)} "
                  f"rec={_fmt_pct(metrics.recall)} f1={_fmt_pct(metrics.f1)} time={metrics.time_sec:.4f}s")

    print()
    print_table(all_metrics)

    print()
    plotted = try_plot(all_metrics, png_path)
    if not plotted:
        print("[plot] график не построен — показана только текстовая таблица")

    result_payload: dict[str, Any] = {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset_size": len(dataset),
            "ru_size": 30,
            "en_size": 30,
            "ru_clean": len(RU_CLEAN),
            "ru_profanity": len(RU_PROFANITY),
            "ru_masked": len(RU_MASKED),
            "en_clean": len(EN_CLEAN),
            "en_profanity": len(EN_PROFANITY),
            "en_masked": len(EN_MASKED),
            "version": "1.0",
        },
        "dataset": [{"text": t, "expected": e, "category": c} for t, e, c in dataset],
        "results": {m.name: m.to_dict() for m in all_metrics},
        "details": all_details,
        "summary": {},
    }

    ok_metrics = [m for m in all_metrics if m.status == "ok"]
    if ok_metrics:
        best_acc = max(ok_metrics, key=lambda x: x.accuracy)
        best_f1 = max(ok_metrics, key=lambda x: x.f1)
        fastest = min(ok_metrics, key=lambda x: x.time_sec)
        best_masked = max(ok_metrics, key=lambda x: x.masked_accuracy)
        result_payload["summary"] = {
            "best_accuracy": {"library": best_acc.name, "value": best_acc.accuracy},
            "best_f1": {"library": best_f1.name, "value": best_f1.f1},
            "best_recall": {"library": max(ok_metrics, key=lambda x: x.recall).name, "value": max(ok_metrics, key=lambda x: x.recall).recall},
            "best_precision": {"library": max(ok_metrics, key=lambda x: x.precision).name, "value": max(ok_metrics, key=lambda x: x.precision).precision},
            "best_masked": {"library": best_masked.name, "value": best_masked.masked_accuracy},
            "fastest": {"library": fastest.name, "time_sec": fastest.time_sec, "avg_ms": fastest.avg_ms},
            "total_libraries": len(all_metrics),
            "ok_libraries": len(ok_metrics),
            "skipped_libraries": len([m for m in all_metrics if m.status == "skipped"]),
        }

    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, ensure_ascii=False, indent=2)
        print(f"\n[json] результаты сохранены: {json_path}")
    except Exception as e:
        print(f"[json] ошибка сохранения {json_path}: {e}", file=sys.stderr)

    if ok_metrics:
        print("\n" + "=" * 72)
        print(" SUMMARY")
        print("=" * 72)
        for m in sorted(ok_metrics, key=lambda x: -x.accuracy):
            flag = " ← BEST" if m == best_acc else ""
            print(f"  {m.name:22s}  acc {_fmt_pct(m.accuracy)}  f1 {_fmt_pct(m.f1)}  "
                  f"masked {_fmt_pct(m.masked_accuracy)}  {m.avg_ms:.2f} ms/txt{flag}")
        print("=" * 72)

    return result_payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Бенчмарк detected-profanity vs alternatives",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--json", dest="json_path", type=str, default=str(_BENCH_DIR / "results.json"),
                        help="путь для results.json")
    parser.add_argument("--png", dest="png_path", type=str, default=str(_BENCH_DIR / "benchmark.png"),
                        help="путь для графика PNG")
    parser.add_argument("--no-plot", action="store_true", help="не строить график")
    parser.add_argument("--list-dataset", action="store_true", help="показать датасет и выйти")
    args = parser.parse_args()

    if args.list_dataset:
        print(f"Датасет {len(DATASET)} фраз:\n")
        for i, (text, expected, cat) in enumerate(DATASET, 1):
            label = "PROFANE" if expected else "CLEAN  "
            print(f"{i:2d}. [{label}] [{cat:12s}] {text}")
        return

    json_path = Path(args.json_path)
    png_path = Path(args.png_path)

    if args.no_plot:
        global try_plot
        orig = try_plot

        def _noop(*a, **kw):  # type: ignore
            print("[plot] --no-plot: график пропущен")
            return False

        try_plot = _noop  # type: ignore
        run_benchmark(json_path=json_path, png_path=png_path)
        try_plot = orig  # type: ignore
    else:
        run_benchmark(json_path=json_path, png_path=png_path)


if __name__ == "__main__":
    main()
