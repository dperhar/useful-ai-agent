#!/usr/bin/env python3
"""Patch Nanobot Codex provider to avoid empty user-facing error messages."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def target_path() -> Path:
    env = os.environ.get("NANOBOT_CODEX_PATCH_TARGET")
    if env:
        return Path(env)
    roots = [Path(p) for p in sys.path if p]
    roots.extend(Path(p) for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p)
    roots.extend(Path.cwd().glob("**/site-packages"))
    roots.append(Path("/usr/local/lib/python3.11/site-packages"))
    for root in roots:
        candidate = root / "nanobot/providers/openai_codex_provider.py"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("nanobot/providers/openai_codex_provider.py not found")


def patch() -> None:
    target = target_path()
    text = target.read_text(encoding="utf-8")
    if "Codex provider call failed" in text:
        return

    old = (
        "        except Exception as e:\n"
        "            msg = f\"Error calling Codex: {e}\"\n"
        "            retry_after = getattr(e, \"retry_after\", None) or self._extract_retry_after(msg)\n"
        "            return LLMResponse(content=msg, finish_reason=\"error\", retry_after=retry_after)\n"
    )
    new = (
        "        except Exception as e:\n"
        "            details = str(e).strip()\n"
        "            if not details:\n"
        "                details = f\"{type(e).__name__} with no details from upstream\"\n"
        "            logger.exception(\"Codex provider call failed: {}\", details)\n"
        "            msg = f\"Error calling Codex: {details}\"\n"
        "            retry_after = getattr(e, \"retry_after\", None) or self._extract_retry_after(msg)\n"
        "            return LLMResponse(content=msg, finish_reason=\"error\", retry_after=retry_after)\n"
    )
    if old not in text:
        raise RuntimeError("Codex provider error handler pattern not found")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


if __name__ == "__main__":
    patch()
