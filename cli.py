#!/usr/bin/env python3
"""Interactive CLI for DetectedProfanity."""

from __future__ import annotations

import os
import sys

try:
    from detected_profanity import ProfanityDetector
except ImportError:
    try:
        from DetectedProfanity.detected_profanity import ProfanityDetector  # type: ignore
    except ImportError:
        try:
            from .detected_profanity import ProfanityDetector  # type: ignore
        except ImportError as e:
            print(f"Cannot import ProfanityDetector: {e}", file=sys.stderr)
            print("Ensure detected_profanity is installed (pip install -e .)", file=sys.stderr)
            raise SystemExit(1)

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None and os.environ.get("TERM") != "dumb"

_RESET = "\033[0m" if _USE_COLOR else ""
_BOLD = "\033[1m" if _USE_COLOR else ""
_DIM = "\033[2m" if _USE_COLOR else ""
_RED = "\033[91m" if _USE_COLOR else ""
_GREEN = "\033[92m" if _USE_COLOR else ""
_YELLOW = "\033[93m" if _USE_COLOR else ""
_CYAN = "\033[96m" if _USE_COLOR else ""

BANNER = f"""{_CYAN}╔════════════════════════════════════════════════════════════╗
║{_RESET}{_BOLD}         DetectedProfanity  ·  CLI                       {_RESET}{_CYAN}║
║{_DIM}   RU / EN / translit  ·  leet · homoglyph · allowlist  {_RESET}{_CYAN}║
╚════════════════════════════════════════════════════════════╝{_RESET}
"""

HELP_HINT = f"{_DIM}Enter text and press Enter — detected / not detected.  /exit to quit.{_RESET}"

_DETECTOR = ProfanityDetector()


def _print_detected(has: bool) -> None:
    """Print detected / not detected with color when available."""
    if has:
        if _USE_COLOR:
            print(f"{_RED}{_BOLD}detected{_RESET}")
        else:
            print("detected")
    else:
        if _USE_COLOR:
            print(f"{_GREEN}not detected{_RESET}")
        else:
            print("not detected")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] in ("-h", "--help", "/help", "/?", "-?"):
        print(BANNER)
        print("Usage: python cli.py [text]\n")
        print("  no args  — interactive REPL")
        print("  with args — check text and exit (detected / not detected)")
        return 0

    if argv:
        text = " ".join(argv)
        if text.strip().lower() in ("/exit", "/quit"):
            return 0
        _print_detected(_DETECTOR.contains_profanity(text))
        return 0

    if not sys.stdin.isatty():
        data = sys.stdin.read()
        if data and data.strip():
            lines = data.splitlines()
            if len(lines) == 1:
                _print_detected(_DETECTOR.contains_profanity(data.strip()))
            else:
                for line in lines:
                    if not line.strip():
                        continue
                    if line.strip().lower() in ("/exit", "/quit"):
                        break
                    _print_detected(_DETECTOR.contains_profanity(line))
            return 0

    print(BANNER)
    print(HELP_HINT)
    print()

    while True:
        try:
            if _USE_COLOR:
                line = input(f"{_CYAN}›{_RESET} ")
            else:
                line = input("> ")
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break

        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower() in ("/exit", "/quit", "/q"):
            break
        _print_detected(_DETECTOR.contains_profanity(line))

    if _USE_COLOR:
        print(f"{_DIM}Bye!{_RESET}")
    else:
        print("Bye!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
