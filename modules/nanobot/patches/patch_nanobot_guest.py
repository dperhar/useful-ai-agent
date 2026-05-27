#!/usr/bin/env python3
"""Patch Nanobot Telegram channel for Telegram Bot API Guest Mode."""

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


HELPERS = r'''

    async def _on_guest_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle Bot API guest_message updates from chats where bot is not a member."""
        raw = (getattr(update, "api_kwargs", None) or {}).get("guest_message")
        if not isinstance(raw, dict):
            return

        guest_query_id = raw.get("guest_query_id")
        if not guest_query_id:
            self.logger.warning("guest_message missing guest_query_id")
            return

        caller = raw.get("guest_bot_caller_user") or raw.get("from") or {}
        sender_id = self._useful_agent_sender_id_from_raw_user(caller)
        if not self.is_allowed(sender_id):
            self.logger.warning("Access denied for guest sender {}", sender_id)
            return

        bot_id, bot_username = await self._ensure_bot_identity()
        content = self._useful_agent_guest_content_from_raw(raw, bot_username)
        metadata = self._useful_agent_guest_metadata(raw, caller, guest_query_id)

        if os.environ.get("NANOBOT_GUEST_REPLY_MODE", "placeholder").strip().lower() == "placeholder":
            try:
                placeholder = os.environ.get("NANOBOT_GUEST_PLACEHOLDER_TEXT", "Шнырь готовит ответ...")
                inline_message_id = await self._useful_agent_answer_guest_query(guest_query_id, placeholder)
                if inline_message_id:
                    metadata["guest_inline_message_id"] = inline_message_id
            except Exception as e:
                self.logger.warning("guest placeholder failed for {}: {}", guest_query_id, e)

        await self.bus.publish_inbound(
            InboundMessage(
                channel=self.name,
                sender_id=str(sender_id),
                chat_id=f"guest:{guest_query_id}",
                content=content,
                media=[],
                metadata=metadata,
                session_key_override=f"telegram:guest:{guest_query_id}",
            )
        )

    @staticmethod
    def _useful_agent_sender_id_from_raw_user(user: dict) -> str:
        sid = str(user.get("id", "unknown"))
        username = user.get("username")
        return f"{sid}|{username}" if username else sid

    @staticmethod
    def _useful_agent_guest_content_from_raw(raw: dict, bot_username: str | None) -> str:
        text = raw.get("text") or raw.get("caption") or ""
        if bot_username:
            text = re.sub(rf"@{re.escape(bot_username)}\b", "", text, flags=re.IGNORECASE)
        reply = raw.get("reply_to_message") or {}
        reply_text = reply.get("text") or reply.get("caption") or ""
        if reply_text:
            reply_text = re.sub(r"\s*\[truncated\]\s*", " ", reply_text).strip()
            reply_text = reply_text[:TELEGRAM_REPLY_CONTEXT_MAX_LEN].rstrip()
            reply_from = reply.get("from") or {}
            label = reply_from.get("username") or reply_from.get("first_name") or "message"
            text = f"[Guest reply to {label}: {reply_text}]\n{text}".strip()
        return text.strip() or "[empty guest message]"

    @staticmethod
    def _useful_agent_guest_visible_body(text: str) -> str:
        body = text if text and text != "[empty message]" else "[empty response]"
        body = _strip_md_block(body)
        body = re.sub(r"\s*\[truncated\]\s*", " ", body).strip()
        return body or "[empty response]"

    @staticmethod
    def _useful_agent_guest_text_chunks(text: str) -> list[str]:
        return split_message(TelegramChannel._useful_agent_guest_visible_body(text), TELEGRAM_MAX_MESSAGE_LEN) or ["[empty response]"]

    async def _useful_agent_send_guest_followup_chunks(self, msg: OutboundMessage, chunks: list[str]) -> None:
        if len(chunks) <= 1:
            return
        targets: list[tuple[str, int, bool]] = []
        guest_chat_id = msg.metadata.get("guest_caller_chat_id")
        if guest_chat_id is not None:
            with suppress(Exception):
                targets.append(("guest_caller_chat", int(guest_chat_id), True))
        user_id = msg.metadata.get("user_id")
        if user_id is not None and str(user_id) != str(guest_chat_id):
            with suppress(Exception):
                targets.append(("caller_private_chat", int(user_id), False))
        for target_name, target_id, reply_in_target in targets:
            try:
                reply_params = None
                if reply_in_target and msg.metadata.get("message_id"):
                    reply_params = ReplyParameters(
                        message_id=int(msg.metadata["message_id"]),
                        allow_sending_without_reply=True,
                    )
                for i, chunk in enumerate(chunks[1:]):
                    await self._call_with_retry(
                        self._app.bot.send_message,
                        chat_id=target_id,
                        text=chunk,
                        reply_parameters=reply_params if i == 0 else None,
                    )
                self.logger.info("sent {} guest continuation chunk(s) via {}", len(chunks) - 1, target_name)
                return
            except Exception as e:
                self.logger.warning("guest continuation via {} failed: {}", target_name, e)
        self.logger.error(
            "guest response has {} continuation chunk(s), but Telegram did not allow follow-up delivery",
            len(chunks) - 1,
        )

    async def _useful_agent_send_guest_final(self, msg: OutboundMessage) -> None:
        chunks = self._useful_agent_guest_text_chunks(msg.content)
        inline_message_id = msg.metadata.get("guest_inline_message_id")
        if inline_message_id:
            await self._useful_agent_edit_guest_inline_message(str(inline_message_id), chunks[0])
        elif msg.metadata.get("guest_query_id"):
            await self._useful_agent_answer_guest_query(str(msg.metadata["guest_query_id"]), chunks[0])
        await self._useful_agent_send_guest_followup_chunks(msg, chunks)

    @staticmethod
    def _useful_agent_guest_metadata(raw: dict, caller: dict, guest_query_id: str) -> dict:
        caller_chat = raw.get("guest_bot_caller_chat") or raw.get("chat") or {}
        return {
            "guest_query_id": guest_query_id,
            "is_guest": True,
            "message_id": raw.get("message_id"),
            "user_id": caller.get("id"),
            "username": caller.get("username"),
            "first_name": caller.get("first_name"),
            "guest_caller_chat_id": caller_chat.get("id"),
            "guest_caller_chat_type": caller_chat.get("type"),
            "is_group": caller_chat.get("type") != "private",
        }

    async def _useful_agent_answer_guest_query(self, guest_query_id: str, text: str) -> str | None:
        import httpx

        body = self._useful_agent_guest_text_chunks(text)[0]
        payload = {
            "guest_query_id": guest_query_id,
            "result": {
                "type": "article",
                "id": f"nanobot-{int(time.time() * 1000)}",
                "title": os.environ.get("NANOBOT_GUEST_RESULT_TITLE", "Шнырь думает"),
                "description": os.environ.get("NANOBOT_GUEST_RESULT_DESCRIPTION", "готовлю ответ"),
                "input_message_content": {"message_text": body},
            },
        }
        url = f"https://api.telegram.org/bot{self.config.token}/answerGuestQuery"
        async with httpx.AsyncClient(timeout=30.0, proxy=self.config.proxy or None) as client:
            response = await client.post(url, json=payload)
            data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"answerGuestQuery failed: {data.get('description') or data}")
        result = data.get("result") or {}
        return result.get("inline_message_id")

    async def _useful_agent_edit_guest_inline_message(self, inline_message_id: str, text: str) -> None:
        import httpx

        body = self._useful_agent_guest_text_chunks(text or "[empty response]")[0]
        payload = {"inline_message_id": inline_message_id, "text": body}
        url = f"https://api.telegram.org/bot{self.config.token}/editMessageText"
        async with httpx.AsyncClient(timeout=30.0, proxy=self.config.proxy or None) as client:
            response = await client.post(url, json=payload)
            data = response.json()
        if not data.get("ok") and "message is not modified" not in str(data.get("description", "")).lower():
            raise RuntimeError(f"editMessageText failed: {data.get('description') or data}")
'''


def patch() -> None:
    target = target_path()
    text = target.read_text(encoding="utf-8")
    if "_on_guest_update" in text:
        return
    text = text.replace(
        "from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters\n",
        "from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, TypeHandler, filters\n",
        1,
    )
    if "import os\n" not in text:
        text = text.replace("import time\n", "import time\nimport os\n", 1)
    if "import re\n" not in text:
        text = text.replace("import time\n", "import time\nimport re\n", 1)
    text = text.replace(
        "from nanobot.bus.events import OutboundMessage\n",
        "from nanobot.bus.events import InboundMessage, OutboundMessage\n",
        1,
    )
    text = text.replace(
        "        self._app.add_error_handler(self._on_error)\n\n"
        "        # Add command handlers",
        "        self._app.add_error_handler(self._on_error)\n"
        "        self._app.add_handler(TypeHandler(Update, self._on_guest_update), group=-1)\n\n"
        "        # Add command handlers",
        1,
    )
    text = text.replace('            allowed_updates = ["message", "callback_query"]\n', '            allowed_updates = ["message", "guest_message", "callback_query"]\n', 1)
    text = text.replace('            allowed_updates = ["message"]\n', '            allowed_updates = ["message", "guest_message"]\n', 1)
    text = text.replace(
        "        if not self._app:\n"
        "            self.logger.warning(\"bot not running\")\n"
        "            return\n\n"
        "        # Only stop typing indicator and remove reaction for final responses\n",
        "        if not self._app:\n"
        "            self.logger.warning(\"bot not running\")\n"
        "            return\n\n"
        "        if msg.metadata.get(\"guest_inline_message_id\"):\n"
        "            if not (msg.content or \"\").strip() or msg.metadata.get(\"_progress\", False):\n"
        "                return\n"
        "            await self._useful_agent_send_guest_final(msg)\n"
        "            return\n\n"
        "        if msg.metadata.get(\"guest_query_id\"):\n"
        "            if not (msg.content or \"\").strip() or msg.metadata.get(\"_progress\", False):\n"
        "                return\n"
        "            await self._useful_agent_send_guest_final(msg)\n"
        "            return\n\n"
        "        # Only stop typing indicator and remove reaction for final responses\n",
        1,
    )
    text = text.replace(
        "    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n",
        HELPERS + "\n    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n",
        1,
    )
    target.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch()
