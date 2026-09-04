"""CLI entry point: python -m detected_profanity."""

from __future__ import annotations

import argparse
import json
import sys

from . import ProfanityDetector, __version__


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="detected_profanity",
        description="Profanity detection for RU/EN/translit.",
    )
    p.add_argument(
        "text",
        nargs="*",
        help="Text to check. Reads stdin if omitted.",
    )
    p.add_argument(
        "--lang",
        choices=["ru", "en", "translit", "all"],
        default="all",
        help="Lexicon language (default: all).",
    )
    p.add_argument(
        "--censor",
        action="store_true",
        help="Output censored text.",
    )
    p.add_argument(
        "--repl",
        default="*",
        help='Replacement for --censor (default: "*").',
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output as JSON.",
    )
    p.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable normalization.",
    )
    p.add_argument(
        "--no-translit",
        action="store_true",
        help="Exclude translit forms.",
    )
    p.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.text:
        text = " ".join(args.text)
    else:
        if sys.stdin.isatty():
            parser.print_help(sys.stderr)
            return 2
        text = sys.stdin.read()

    if not text or not text.strip():
        print("empty input", file=sys.stderr)
        return 2

    lang = None if args.lang == "all" else args.lang
    det = ProfanityDetector(
        lang=lang,
        include_translit=not args.no_translit,
        use_normalization=not args.no_normalize,
    )

    has = det.contains_profanity(text)
    found = det.detect(text)

    if args.as_json:
        payload: dict[str, object] = {
            "text": text,
            "has_profanity": has,
            "matches": found,
        }
        if args.censor:
            payload["censored"] = det.censor(text, repl=args.repl)
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        if args.censor:
            print(det.censor(text, repl=args.repl))
        else:
            if has:
                print(f"profanity: YES  matches={found}")
            else:
                print("profanity: NO")

    return 1 if has else 0


if __name__ == "__main__":
    raise SystemExit(main())
