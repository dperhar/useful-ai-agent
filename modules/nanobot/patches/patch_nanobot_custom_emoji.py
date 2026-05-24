#!/usr/bin/env python3
"""Patch Nanobot Telegram channel with custom emoji ID extraction."""

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
    roots.append(Path("/usr/local/lib/python3.11/site-packages"))
    for root in roots:
        candidate = root / "nanobot/channels/telegram.py"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("nanobot/channels/telegram.py not found")


HELPERS = r'''

    @staticmethod
    def _custom_emoji_id_file() -> str:
        return os.environ.get("NANOBOT_GUEST_CUSTOM_EMOJI_ID_FILE", str(Path.home() / ".nanobot/.useful-agent-guest-custom-emoji-id"))

    @classmethod
    def _get_guest_custom_emoji_id(cls) -> str:
        custom_emoji_id = os.environ.get("NANOBOT_GUEST_CUSTOM_EMOJI_ID", "").strip()
        if custom_emoji_id:
            return custom_emoji_id
        path = cls._custom_emoji_id_file()
        try:
            return Path(path).read_text(encoding="utf-8").strip()
        except Exception:
            return ""

    @staticmethod
    def _utf16_len(text: str) -> int:
        return len(text.encode("utf-16-le")) // 2

    @staticmethod
    def _custom_emoji_ids_from_message(message) -> list[str]:
        ids: list[str] = []
        for entity in list(getattr(message, "entities", None) or []) + list(getattr(message, "caption_entities", None) or []):
            if getattr(entity, "type", None) == "custom_emoji":
                custom_emoji_id = getattr(entity, "custom_emoji_id", None)
                if custom_emoji_id and custom_emoji_id not in ids:
                    ids.append(custom_emoji_id)
        return ids

    async def _on_custom_emoji_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Extract and persist custom_emoji_id from a Telegram custom emoji entity."""
        if not update.message or not update.effective_user:
            return
        message = update.message
        sender_id = self._sender_id(update.effective_user)
        if not self.is_allowed(sender_id):
            return
        ids = self._custom_emoji_ids_from_message(message)
        if not ids:
            await message.reply_text("No custom emoji entity found. Send: /emoji_id <your custom emoji>")
            return
        custom_emoji_id = ids[0]
        path = Path(self._custom_emoji_id_file())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(custom_emoji_id + "\n", encoding="utf-8")
        os.environ["NANOBOT_GUEST_CUSTOM_EMOJI_ID"] = custom_emoji_id
        await message.reply_text(f"custom_emoji_id saved: {custom_emoji_id}")
'''


def patch() -> None:
    target = target_path()
    text = target.read_text(encoding="utf-8")
    if "_on_custom_emoji_id" in text:
        return

    if "from pathlib import Path\n" not in text:
        text = text.replace("from typing import", "from pathlib import Path\nfrom typing import", 1)

    text = text.replace(
        "        # Add command handlers (using Regex to support @username suffixes before bot initialization)\n"
        "        self._app.add_handler(MessageHandler(filters.Regex(r\"^/start(?:@\\w+)?$\"), self._on_start))\n",
        "        # Add command handlers (using Regex to support @username suffixes before bot initialization)\n"
        "        self._app.add_handler(MessageHandler(filters.Regex(r\"^/emoji_id(?:@\\w+)?(?:\\s+.*)?$\"), self._on_custom_emoji_id))\n"
        "        self._app.add_handler(MessageHandler(filters.Regex(r\"^/start(?:@\\w+)?$\"), self._on_start))\n",
        1,
    )

    text = text.replace(
        "    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n",
        HELPERS + "\n    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n",
        1,
    )

    text = text.replace(
        '        custom_emoji_id = os.environ.get("NANOBOT_GUEST_CUSTOM_EMOJI_ID", "").strip()\n'
        '        if custom_emoji_id and text.startswith("😈"):\n'
        '            content["entities"] = [{\n'
        '                "type": "custom_emoji",\n'
        '                "offset": 0,\n'
        '                "length": 2,\n'
        '                "custom_emoji_id": custom_emoji_id,\n'
        '            }]\n',
        '        custom_emoji_id = TelegramChannel._get_guest_custom_emoji_id()\n'
        '        marker = os.environ.get("NANOBOT_GUEST_CUSTOM_EMOJI_MARKER", "Ж")\n'
        '        if custom_emoji_id and text.startswith(marker):\n'
        '            content["entities"] = [{\n'
        '                "type": "custom_emoji",\n'
        '                "offset": 0,\n'
        '                "length": TelegramChannel._utf16_len(marker),\n'
        '                "custom_emoji_id": custom_emoji_id,\n'
        '            }]\n',
        1,
    )

    target.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch()
