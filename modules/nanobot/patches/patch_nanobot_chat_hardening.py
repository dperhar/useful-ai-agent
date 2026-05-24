#!/usr/bin/env python3
"""Patch Nanobot Telegram chat edge cases for slash commands, albums, and fallback formatting."""

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


def patch() -> None:
    target = target_path()
    text = target.read_text(encoding="utf-8")

    if "TELEGRAM_MEDIA_GROUP_DEBOUNCE_SECONDS" not in text:
        text = text.replace(
            "TELEGRAM_REPLY_CONTEXT_MAX_LEN = TELEGRAM_MAX_MESSAGE_LEN  # Max length for reply context in user message\n",
            "TELEGRAM_REPLY_CONTEXT_MAX_LEN = TELEGRAM_MAX_MESSAGE_LEN  # Max length for reply context in user message\n"
            "TELEGRAM_MEDIA_GROUP_DEBOUNCE_SECONDS = float(os.environ.get(\"NANOBOT_MEDIA_GROUP_DEBOUNCE_SECONDS\", \"15\"))\n",
            1,
        )

    text = text.replace(
        r'r"^/(?:new|stop|restart|status|dream|history|goal|pairing|model)(?:@\w+)?(?:\s+.*)?$"',
        r'r"^/(?:new|stop|restart|status|dream|history|goal|pairing|model|high|xhigh|improve|effort|think)(?:@\w+)?(?:\s+.*)?$"',
        1,
    )

    text = text.replace(
        "                await self._call_with_retry(\n"
        "                    self._app.bot.send_message,\n"
        "                    chat_id=chat_id,\n"
        "                    text=text,\n",
        "                plain = _strip_md_block(text)\n"
        "                await self._call_with_retry(\n"
        "                    self._app.bot.send_message,\n"
        "                    chat_id=chat_id,\n"
        "                    text=plain,\n",
        1,
    )

    text = text.replace(
        "                # Fall back to raw markdown (not HTML) so users don't see raw tags.\n"
        "                primary_plain = split_message(raw_text, TELEGRAM_MAX_MESSAGE_LEN)[0] if len(raw_text) > TELEGRAM_MAX_MESSAGE_LEN else raw_text\n",
        "                # Fall back to stripped markdown so users do not see raw ** markers.\n"
        "                plain_text = _strip_md_block(raw_text)\n"
        "                primary_plain = split_message(plain_text, TELEGRAM_MAX_MESSAGE_LEN)[0] if len(plain_text) > TELEGRAM_MAX_MESSAGE_LEN else plain_text\n",
        1,
    )

    text = text.replace(
        "            if key not in self._media_group_tasks:\n"
        "                self._media_group_tasks[key] = asyncio.create_task(self._flush_media_group(key))\n",
        "            if task := self._media_group_tasks.pop(key, None):\n"
        "                task.cancel()\n"
        "            self._media_group_tasks[key] = asyncio.create_task(self._flush_media_group(key))\n",
        1,
    )

    text = text.replace(
        "            await asyncio.sleep(0.6)\n",
        "            await asyncio.sleep(TELEGRAM_MEDIA_GROUP_DEBOUNCE_SECONDS)\n",
        1,
    )
    text = text.replace(
        "        finally:\n"
        "            self._media_group_tasks.pop(key, None)\n",
        "        finally:\n"
        "            if self._media_group_tasks.get(key) is asyncio.current_task():\n"
        "                self._media_group_tasks.pop(key, None)\n",
        1,
    )

    target.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch()
