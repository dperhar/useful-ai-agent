#!/usr/bin/env python3
"""Patch Nanobot channel manager to deliver media attached to streamed turns."""

from __future__ import annotations

import os
from pathlib import Path


TARGET = Path(os.environ.get(
    "NANOBOT_STREAMED_MEDIA_PATCH_TARGET",
    "/usr/local/lib/python3.11/site-packages/nanobot/channels/manager.py",
))


def patch() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if "_useful_agent_send_streamed_media_only" in text:
        return

    old = """        elif msg.metadata.get("_stream_delta") or msg.metadata.get("_stream_end"):
            await channel.send_delta(msg.chat_id, msg.content, msg.metadata)
        elif not msg.metadata.get("_streamed"):
            await channel.send(msg)
"""
    new = """        elif msg.metadata.get("_stream_delta") or msg.metadata.get("_stream_end"):
            await channel.send_delta(msg.chat_id, msg.content, msg.metadata)
        elif msg.metadata.get("_streamed"):
            # _useful_agent_send_streamed_media_only:
            # Text has already been delivered through stream deltas, but generated
            # images/files are attached only to the final outbound. Send media
            # without duplicating the streamed text.
            if msg.media:
                media_metadata = dict(msg.metadata or {})
                media_metadata.pop("_streamed", None)
                await channel.send(OutboundMessage(
                    channel=msg.channel,
                    chat_id=msg.chat_id,
                    content="",
                    reply_to=msg.reply_to,
                    media=msg.media,
                    metadata=media_metadata,
                    buttons=[],
                ))
        else:
            await channel.send(msg)
"""
    if old not in text:
        raise RuntimeError("Target ChannelManager _send_once block not found")
    TARGET.write_text(text.replace(old, new, 1), encoding="utf-8")


if __name__ == "__main__":
    patch()
