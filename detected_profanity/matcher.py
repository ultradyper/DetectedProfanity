"""Aho-Corasick automaton — pure Python, no dependencies."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

__all__ = ["AhoCorasick", "Match", "find_matches"]


class _Node:
    """Trie node."""

    __slots__ = ("children", "fail", "output")

    def __init__(self) -> None:
        self.children: Dict[str, _Node] = {}
        self.fail: Optional[_Node] = None
        self.output: List[str] = []


@dataclass(frozen=True, slots=True)
class Match:
    """Structured match result with inclusive indices."""

    pattern: str
    start: int
    end: int

    @property
    def matched_text(self) -> str:
        return self.pattern

    @property
    def span(self) -> Tuple[int, int]:
        """Return (start, end_exclusive)."""
        return (self.start, self.end + 1)

    def __repr__(self) -> str:
        return f"Match(pattern={self.pattern!r}, start={self.start}, end={self.end})"


class AhoCorasick:
    """Aho-Corasick automaton for simultaneous multi-pattern search."""

    def __init__(self, patterns: Optional[Iterable[str]] = None) -> None:
        self._root: _Node = _Node()
        self._built: bool = False
        self._pattern_count: int = 0
        self._patterns: List[str] = []
        self._pattern_set: set[str] = set()

        if patterns is not None:
            for p in patterns:
                self.add_pattern(p)
            if self._pattern_count:
                self.build()

    def add_pattern(self, pattern: str) -> None:
        """Insert a pattern into the trie. Empty and duplicate patterns are ignored."""
        if not isinstance(pattern, str):
            raise TypeError(f"pattern must be str, got {type(pattern).__name__!r}")
        if pattern == "":
            return
        if pattern in self._pattern_set:
            return

        self._pattern_set.add(pattern)
        self._patterns.append(pattern)

        node = self._root
        for ch in pattern:
            nxt = node.children.get(ch)
            if nxt is None:
                nxt = _Node()
                node.children[ch] = nxt
            node = nxt
        if pattern not in node.output:
            node.output.append(pattern)
        self._pattern_count += 1
        self._built = False

    def build(self) -> None:
        """Build failure links (BFS). Idempotent."""
        if self._built:
            return

        root = self._root
        root.fail = None

        q: deque[_Node] = deque()
        for child in root.children.values():
            child.fail = root
            q.append(child)

        while q:
            current = q.popleft()
            for ch, child in current.children.items():
                q.append(child)
                fail_node = current.fail
                while fail_node is not None and ch not in fail_node.children:
                    fail_node = fail_node.fail
                if fail_node is None:
                    child.fail = root
                else:
                    child.fail = fail_node.children[ch]
                if child.fail.output:
                    for pat in child.fail.output:
                        if pat not in child.output:
                            child.output.append(pat)

        self._built = True

    def search(self, text: str) -> List[Tuple[int, str]]:
        """Scan text and return list of (end_index, pattern) tuples."""
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__!r}")
        if not text or self._pattern_count == 0:
            return []
        if not self._built:
            self.build()

        result: List[Tuple[int, str]] = []
        node: _Node = self._root
        root = self._root

        for idx, ch in enumerate(text):
            while node is not root and ch not in node.children:
                assert node.fail is not None
                node = node.fail
            nxt = node.children.get(ch)
            if nxt is not None:
                node = nxt
            else:
                node = root
            if node.output:
                for pat in node.output:
                    result.append((idx, pat))
        return result

    def search_iter(self, text: str) -> Iterator[Tuple[int, str]]:
        """Streaming variant of search — yields matches lazily."""
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__!r}")
        if not text or self._pattern_count == 0:
            return
        if not self._built:
            self.build()

        node: _Node = self._root
        root = self._root
        for idx, ch in enumerate(text):
            while node is not root and ch not in node.children:
                assert node.fail is not None
                node = node.fail
            nxt = node.children.get(ch)
            node = nxt if nxt is not None else root
            if node.output:
                for pat in node.output:
                    yield (idx, pat)

    def find_matches(self, text: str) -> List[Match]:
        """Return Match objects for all occurrences in text."""
        return [Match(pattern=pat, start=end - len(pat) + 1, end=end) for end, pat in self.search(text)]

    @property
    def patterns(self) -> Tuple[str, ...]:
        """Distinct patterns in insertion order."""
        return tuple(self._patterns)

    def __len__(self) -> int:
        return self._pattern_count

    def __contains__(self, pattern: object) -> bool:
        return pattern in self._pattern_set

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(patterns={self._patterns!r}, built={self._built})"


def find_matches(
    text: str,
    patterns: Iterable[str],
    *,
    automaton: Optional[AhoCorasick] = None,
) -> List[Match]:
    """Find all occurrences of patterns in text."""
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__!r}")

    if automaton is not None:
        if not isinstance(automaton, AhoCorasick):
            raise TypeError(f"automaton must be AhoCorasick, got {type(automaton).__name__!r}")
        ac = automaton
    else:
        if patterns is None:
            raise TypeError("patterns must be iterable of str, got None")
        pat_list = list(patterns)
        for p in pat_list:
            if not isinstance(p, str):
                raise TypeError(f"pattern must be str, got {type(p).__name__!r}")
        ac = AhoCorasick(pat_list)

    raw: List[Tuple[int, str]] = ac.search(text)
    return [Match(pattern=pat, start=end - len(pat) + 1, end=end) for end, pat in raw]
