#!/usr/bin/env python3
"""Patch Nanobot Telegram replies to preserve selected Telegram quote text."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def target_path() -> Path:
    env = os.environ.get("NANOBOT_TELEGRAM_PATCH_TARGET")
    if env:
        return Path(env)
    roots = [Path(p) for p in sys.path if p]
    roots.extend(Path(p) for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p)
    roots.extend(Path.cwd().glob("**/site-packages"))
    for root in roots:
        candidate = root / "nanobot/channels/telegram.py"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("nanobot/channels/telegram.py not found")


HELPER = '''    @staticmethod
    def _extract_text_quote(message) -> str | None:
        """Extract Telegram's selected quote text from the incoming reply."""
        quote = getattr(message, "quote", None)
        if quote is None:
            quote = (getattr(message, "api_kwargs", None) or {}).get("quote")
        if not quote:
            return None
        if isinstance(quote, dict):
            text = quote.get("text")
        else:
            text = getattr(quote, "text", None)
        if not text:
            return None
        return text[:TELEGRAM_REPLY_CONTEXT_MAX_LEN] + ("..." if len(text) > TELEGRAM_REPLY_CONTEXT_MAX_LEN else "")

'''


def patch() -> None:
    target = target_path()
    text = target.read_text(encoding="utf-8")

    if "_extract_text_quote" not in text:
        text = text.replace(
            "    @staticmethod\n"
            "    def _derive_topic_session_key(message) -> str | None:\n",
            HELPER + "    @staticmethod\n"
            "    def _derive_topic_session_key(message) -> str | None:\n",
            1,
        )

    text = text.replace(
        "        text = getattr(reply, \"text\", None) or getattr(reply, \"caption\", None) or \"\"\n",
        "        quote_text = self._extract_text_quote(message)\n"
        "        text = quote_text or getattr(reply, \"text\", None) or getattr(reply, \"caption\", None) or \"\"\n",
        1,
    )
    text = text.replace(
        "            return f\"[Reply to bot: {text}]\"\n",
        "            prefix = \"Quote from bot\" if quote_text else \"Reply to bot\"\n"
        "            return f\"[{prefix}: {text}]\"\n",
        1,
    )
    text = text.replace(
        "            return f\"[Reply to @{reply_user.username}: {text}]\"\n",
        "            prefix = \"Quote from\" if quote_text else \"Reply to\"\n"
        "            return f\"[{prefix} @{reply_user.username}: {text}]\"\n",
        1,
    )
    text = text.replace(
        "            return f\"[Reply to {reply_user.first_name}: {text}]\"\n",
        "            prefix = \"Quote from\" if quote_text else \"Reply to\"\n"
        "            return f\"[{prefix} {reply_user.first_name}: {text}]\"\n",
        1,
    )
    text = text.replace(
        "            return f\"[Reply to: {text}]\"\n",
        "            prefix = \"Quote\" if quote_text else \"Reply to\"\n"
        "            return f\"[{prefix}: {text}]\"\n",
        1,
    )
    text = text.replace(
        "        reply_text = reply.get(\"text\") or reply.get(\"caption\") or \"\"\n",
        "        quote = raw.get(\"quote\") or {}\n"
        "        reply_text = quote.get(\"text\") or reply.get(\"text\") or reply.get(\"caption\") or \"\"\n",
        1,
    )
    text = text.replace(
        "            text = f\"[Guest reply to {label}: {reply_text[:TELEGRAM_REPLY_CONTEXT_MAX_LEN]}]\\n{text}\".strip()\n",
        "            kind = \"quote from\" if quote.get(\"text\") else \"reply to\"\n"
        "            text = f\"[Guest {kind} {label}: {reply_text[:TELEGRAM_REPLY_CONTEXT_MAX_LEN]}]\\n{text}\".strip()\n",
        1,
    )

    target.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch()
