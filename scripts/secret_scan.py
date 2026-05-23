#!/usr/bin/env python3
"""Small repo-wide scanner for private paths and obvious secrets."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".build", "__pycache__", ".mypy_cache", ".pytest_cache"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".bundle", ".enc"}

PRIVATE_HOME = "/Users/" + "a1"
PRIVATE_DESKTOP_A = "Desktop/" + "';L"
PRIVATE_DESKTOP_B = "Desktop/" + "\\';L"

PATTERNS = [
    ("private-mac-path", re.compile(re.escape(PRIVATE_HOME) + "|" + re.escape(PRIVATE_DESKTOP_A) + "|" + re.escape(PRIVATE_DESKTOP_B))),
    ("telegram-token", re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("api-key-assignment", re.compile(r"(?i)\b(api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}")),
]

ALLOWLIST = [
    ("docs/security-privacy.md", "client_secret"),
    ("README.md", "token"),
    ("modules/nanobot/templates/com.usefulaiagent.nanobot.plist", "UsefulAIAgent"),
]


def allowed(rel: str, line: str) -> bool:
    return any(rel == path and token in line for path, token in ALLOWLIST)


def main() -> int:
    failures: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        rel = str(path.relative_to(ROOT))
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if allowed(rel, line):
                continue
            for name, pattern in PATTERNS:
                if pattern.search(line):
                    failures.append(f"{rel}:{line_no}: {name}")
    if failures:
        print("\n".join(failures))
        return 1
    print("secret scan ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
