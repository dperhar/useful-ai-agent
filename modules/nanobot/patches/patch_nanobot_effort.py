#!/usr/bin/env python3
"""Patch Nanobot with one-turn effort markers plus /improve and Codex-native /goal shortcuts."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def target_path() -> Path:
    env = os.environ.get("NANOBOT_AGENT_LOOP_PATCH_TARGET")
    if env:
        return Path(env)
    roots = [Path(p) for p in sys.path if p]
    roots.extend(Path(p) for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p)
    roots.extend(Path.cwd().glob("**/site-packages"))
    for root in roots:
        candidate = root / "nanobot/agent/loop.py"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("nanobot/agent/loop.py not found")


HELPER = r'''
_USEFUL_AGENT_ONE_TURN_EFFORT_RE = re.compile(
    r"^\s*(?:"
    r"\[(?:effort|reasoning|think)\s*=\s*(none|minimal|low|medium|high|xhigh|adaptive)\]\s*"
    r"|/(?:effort|think)\s+(none|minimal|low|medium|high|xhigh|adaptive)\s+"
    r"|/(high|xhigh)(?:\s*[-—:]\s*|\s+|$)"
    r"|(high|xhigh)(?:\s*[-—]\s*|\s+)"
    r")",
    re.IGNORECASE,
)
_USEFUL_AGENT_ANYWHERE_EFFORT_RE = re.compile(
    r"(?im)(^|[\s\(\[\{])"
    r"(?:(?:/(high|xhigh))|(?:\[(?:effort|reasoning|think)\s*=\s*(high|xhigh)\])|(?:\b(high|xhigh)\b))"
    r"(?:\s*[-—:])?"
)
_USEFUL_AGENT_COMMAND_RE = re.compile(r"(?im)(^|[\s\(\[\{])/(improve|goal)(?!@[\w_])(?=\s|$)")


def _useful_agent_extract_one_turn_reasoning_effort(text: str) -> tuple[str | None, str]:
    if not isinstance(text, str):
        return None, text
    match = _USEFUL_AGENT_ONE_TURN_EFFORT_RE.match(text)
    if match:
        effort = next((group for group in match.groups() if group), None)
        cleaned = text[match.end():].lstrip()
        return (effort.lower(), cleaned or text) if effort else (None, text)
    match = _USEFUL_AGENT_ANYWHERE_EFFORT_RE.search(text)
    if not match:
        return None, text
    effort = next((group for group in match.groups()[1:] if group), None)
    if not effort:
        return None, text
    marker_start = match.start() + len(match.group(1) or "")
    cleaned = text[:marker_start] + text[match.end():]
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return effort.lower(), cleaned or text


def _useful_agent_expand_command_shortcuts(text: str) -> str:
    if not isinstance(text, str):
        return text
    match = _USEFUL_AGENT_COMMAND_RE.search(text)
    if not match:
        return text
    command = match.group(2).lower()
    marker_start = match.start() + len(match.group(1) or "")
    payload = (text[:marker_start] + text[match.end():]).strip()
    payload = re.sub(r"[ \t]{2,}", " ", payload)
    payload = re.sub(r"\n{3,}", "\n\n", payload).strip()
    if command == "goal":
        return "/goal" + (f" {payload}" if payload else "")
    if not payload:
        return "Use the improve skill on the previous assistant output."
    return "Use the improve skill on this request/output. " + payload
'''


def patch() -> None:
    target = target_path()
    text = target.read_text(encoding="utf-8")
    if "_useful_agent_expand_command_shortcuts" in text:
        return
    if "import re" not in text:
        text = text.replace("import os\n", "import os\nimport re\n", 1)
    if "_useful_agent_extract_one_turn_reasoning_effort" in text:
        text = text.replace(
            "        ctx.msg.content = _useful_agent_expand_improve_shortcut(ctx.msg.content)\n",
            "        ctx.msg.content = _useful_agent_expand_command_shortcuts(ctx.msg.content)\n",
            1,
        )
        text = text.replace(
            "        ctx.msg.content = _useful_agent_expand_improve_shortcut(ctx.msg.content)\n",
            "        ctx.msg.content = _useful_agent_expand_command_shortcuts(ctx.msg.content)\n",
            1,
        )
        text = text.replace(
            "_USEFUL_AGENT_IMPROVE_RE = re.compile(r\"(?im)(^|[\\s\\(\\[\\{])/improve(?!@[\\w_])(?=\\s|$)\")",
            "_USEFUL_AGENT_COMMAND_RE = re.compile(r\"(?im)(^|[\\s\\(\\[\\{])/(improve|goal)(?!@[\\w_])(?=\\s|$)\")",
            1,
        )
        if "_useful_agent_expand_improve_shortcut" in text:
            start = text.index("def _useful_agent_expand_improve_shortcut")
            end_marker = "\n\n\ndef "
            end = text.find(end_marker, start + 1)
            if end == -1:
                end = text.find("\n\n    async def _state_build", start)
            if end == -1:
                raise RuntimeError("Could not locate end of old /improve shortcut helper")
            replacement = '''def _useful_agent_expand_command_shortcuts(text: str) -> str:
    if not isinstance(text, str):
        return text
    match = _USEFUL_AGENT_COMMAND_RE.search(text)
    if not match:
        return text
    command = match.group(2).lower()
    marker_start = match.start() + len(match.group(1) or "")
    payload = (text[:marker_start] + text[match.end():]).strip()
    payload = re.sub(r"[ \\t]{2,}", " ", payload)
    payload = re.sub(r"\\n{3,}", "\\n\\n", payload).strip()
    if command == "goal":
        return "/goal" + (f" {payload}" if payload else "")
    if not payload:
        return "Use the improve skill on the previous assistant output."
    return "Use the improve skill on this request/output. " + payload'''
            text = text[:start] + replacement + text[end:]
        if "_USEFUL_AGENT_COMMAND_RE" not in text:
            text = text.replace(
                "_USEFUL_AGENT_ANYWHERE_EFFORT_RE = re.compile(",
                "_USEFUL_AGENT_COMMAND_RE = re.compile(r\"(?im)(^|[\\s\\(\\[\\{])/(improve|goal)(?!@[\\w_])(?=\\s|$)\")\n"
                "_USEFUL_AGENT_ANYWHERE_EFFORT_RE = re.compile(",
                1,
            )
    else:
        text = text.replace(
            'UNIFIED_SESSION_KEY = "unified:default"\n',
            'UNIFIED_SESSION_KEY = "unified:default"\n' + HELPER + "\n",
            1,
        )
        text = text.replace(
            "    async def _state_build(self, ctx: TurnContext) -> str:\n"
            "        await self.consolidator.maybe_consolidate_by_tokens(\n",
            "    async def _state_build(self, ctx: TurnContext) -> str:\n"
            "        effort, cleaned = _useful_agent_extract_one_turn_reasoning_effort(ctx.msg.content)\n"
            "        if effort:\n"
            "            ctx.msg.metadata = {**dict(ctx.msg.metadata or {}), \"_one_turn_reasoning_effort\": effort}\n"
            "            ctx.msg.content = cleaned\n"
            "            logger.info(\"One-turn reasoning effort override: {}\", effort)\n"
            "        ctx.msg.content = _useful_agent_expand_command_shortcuts(ctx.msg.content)\n"
            "        await self.consolidator.maybe_consolidate_by_tokens(\n",
            1,
        )
    text = text.replace(
        "                max_tool_result_chars=self.max_tool_result_chars,\n"
        "                hook=hook,\n",
        "                max_tool_result_chars=self.max_tool_result_chars,\n"
        "                reasoning_effort=(metadata or {}).get(\"_one_turn_reasoning_effort\"),\n"
        "                hook=hook,\n",
        1,
    )
    target.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch()
