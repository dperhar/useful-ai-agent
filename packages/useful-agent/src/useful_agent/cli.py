from __future__ import annotations

import argparse
import getpass
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


APP_SUPPORT = Path(os.environ.get("USEFUL_AGENT_APP_SUPPORT", Path.home() / "Library/Application Support/UsefulAIAgent"))
LOG_DIR = Path(os.environ.get("USEFUL_AGENT_LOG_DIR", Path.home() / "Library/Logs/UsefulAIAgent"))
WORKSPACE = Path(os.environ.get("USEFUL_AGENT_WORKSPACE", Path.home() / "Useful AI Agent Workspace"))
VAULT = APP_SUPPORT / "backups"
RUNTIME = APP_SUPPORT / "runtime"
LAUNCH_AGENTS = Path.home() / "Library/LaunchAgents"
REPO_DIR = APP_SUPPORT / "source/useful-ai-agent"
SERVICE = "UsefulAIAgentBackup"
ACCOUNT = "bundle-password"


def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, text=True, capture_output=capture)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "README.md").exists() and (parent / "modules").exists():
            return parent
    if REPO_DIR.exists():
        return REPO_DIR
    return Path.cwd()


def ensure_dirs() -> None:
    for path in [APP_SUPPORT, LOG_DIR, WORKSPACE, VAULT, RUNTIME, LAUNCH_AGENTS]:
        path.mkdir(parents=True, exist_ok=True)


def write(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def copy_template(name: str, target: Path, replacements: dict[str, str] | None = None, mode: int | None = None) -> None:
    src = repo_root() / name
    text = src.read_text(encoding="utf-8")
    for key, value in (replacements or {}).items():
        text = text.replace("{{" + key + "}}", value)
    write(target, text, mode)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def keychain_get(service: str, account: str) -> str | None:
    try:
        out = run(["security", "find-generic-password", "-w", "-s", service, "-a", account], capture=True)
        return out.stdout.strip()
    except Exception:
        return None


def keychain_set(service: str, account: str, value: str) -> None:
    run(["security", "add-generic-password", "-U", "-s", service, "-a", account, "-w", value])


def install_guided(args: argparse.Namespace) -> None:
    ensure_dirs()
    if platform.system() != "Darwin":
        raise SystemExit("Useful AI Agent v1 supports macOS only.")
    if platform.machine() not in {"arm64", "aarch64"}:
        raise SystemExit("Useful AI Agent v1 expects Apple Silicon for the full Transcripted profile.")

    print("Creating router-first workspace...")
    replacements = {"WORKSPACE": str(WORKSPACE)}
    copy_template("modules/router/templates/AGENTS.md", WORKSPACE / "AGENTS.md", replacements)
    copy_template("modules/router/templates/CLAUDE.md", WORKSPACE / "CLAUDE.md", replacements)
    copy_template("modules/router/templates/cursor-router.mdc", WORKSPACE / ".cursor/rules/useful-agent-router.mdc", replacements)
    for folder in ["Canon", "Projects", "Clients", "Personal", "Inbox", "Archive", "Harness"]:
        (WORKSPACE / folder).mkdir(parents=True, exist_ok=True)
    copy_template("modules/router/templates/scoped-harness-AGENTS.md", WORKSPACE / "Harness/AGENTS.md", replacements)

    print("Installing Python packages in managed runtime...")
    if not command_exists("uv"):
        raise SystemExit("uv missing. Re-run bootstrap/macos.sh.")
    run(["uv", "venv", str(RUNTIME / "venv")])
    python = RUNTIME / "venv/bin/python"
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "nanobot-ai", "mempalace"])

    print("Installing skills...")
    skills_dst = WORKSPACE / "Harness/skills"
    skills_dst.mkdir(parents=True, exist_ok=True)
    for src in (repo_root() / "skills").glob("*"):
        if src.is_dir():
            dst = skills_dst / src.name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    for name in ["context-architecture-setup", "context-architecture-cleanup", "improve"]:
        src = repo_root() / name
        if src.is_dir():
            dst = skills_dst / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    print("Writing Nanobot config...")
    token = args.telegram_token or keychain_get("UsefulAIAgentTelegram", "bot-token")
    if not token and args.guided:
        print("Create a bot in Telegram BotFather, enable required modes, then paste the token.")
        token = getpass.getpass("Telegram bot token: ").strip()
    if token:
        keychain_set("UsefulAIAgentTelegram", "bot-token", token)
    else:
        print("WARN: Telegram token not configured. Run useful-agent install --telegram-token TOKEN later.")

    nanobot_config = build_nanobot_config(token or "PASTE_TOKEN_FROM_KEYCHAIN")
    write(APP_SUPPORT / "nanobot/config.json", json.dumps(nanobot_config, indent=2) + "\n", 0o600)
    copy_template("modules/nanobot/templates/run-nanobot.sh", APP_SUPPORT / "bin/run-nanobot.sh", {
        "APP_SUPPORT": str(APP_SUPPORT),
        "WORKSPACE": str(WORKSPACE),
        "PYTHON": str(python),
    }, 0o755)
    copy_template("modules/nanobot/templates/com.usefulaiagent.nanobot.plist", LAUNCH_AGENTS / "com.usefulaiagent.nanobot.plist", {
        "APP_SUPPORT": str(APP_SUPPORT),
    })
    copy_template("modules/transcripted/transcripted-mcp", APP_SUPPORT / "bin/transcripted-mcp", {}, 0o755)

    print("Writing backup and health scripts...")
    copy_template("modules/backups/templates/backup.sh", APP_SUPPORT / "bin/backup.sh", {
        "WORKSPACE": str(WORKSPACE),
        "VAULT": str(VAULT),
        "SERVICE": SERVICE,
        "ACCOUNT": ACCOUNT,
    }, 0o755)
    copy_template("modules/governance/check.sh", APP_SUPPORT / "bin/check.sh", {
        "APP_SUPPORT": str(APP_SUPPORT),
        "WORKSPACE": str(WORKSPACE),
    }, 0o755)

    desktop = Path.home() / "Desktop"
    if desktop.exists():
        write(desktop / "Start Useful AI Agent.command", f'#!/bin/zsh\n"{APP_SUPPORT}/bin/run-nanobot.sh"\n', 0o755)
        write(desktop / "Check Useful AI Agent.command", f'#!/bin/zsh\n"{APP_SUPPORT}/bin/check.sh"; read "?Press enter to close."\n', 0o755)

    print("Installing LaunchAgent...")
    run(["launchctl", "bootout", f"gui/{os.getuid()}/com.usefulaiagent.nanobot"], check=False)
    run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(LAUNCH_AGENTS / "com.usefulaiagent.nanobot.plist")], check=False)

    print("Transcripted setup:")
    print("- Install from official source: https://transcripted.app/")
    print("- Approve microphone/screen/audio permissions.")
    print("- Then run useful-agent check.")
    check(argparse.Namespace(json=False))


def build_nanobot_config(token: str) -> dict:
    return {
        "agents": {"defaults": {"workspace": str(WORKSPACE), "reasoningEffort": "medium"}},
        "channels": {
            "telegram": {"enabled": True, "token": token, "allowFrom": []},
            "websocket": {"enabled": True, "host": "127.0.0.1", "port": 8765, "websocketRequiresToken": True},
        },
        "tools": {
            "mcpServers": {
                "mempalace": {
                    "command": str(RUNTIME / "venv/bin/mempalace-mcp"),
                    "args": ["--palace", str(APP_SUPPORT / "mempalace/palace")],
                    "toolTimeout": 60,
                },
                "transcripted": {
                    "command": str(APP_SUPPORT / "bin/transcripted-mcp"),
                    "args": [],
                    "env": {
                        "TRANSCRIPTED_CAPTURES_DIR": str(Path.home() / "Library/Application Support/Transcripted/captures")
                    },
                    "toolTimeout": 60,
                },
            }
        },
    }


def check(args: argparse.Namespace) -> None:
    ensure_dirs()
    checks = [
        ("macOS", platform.system() == "Darwin"),
        ("Apple Silicon", platform.machine() in {"arm64", "aarch64"}),
        ("uv", command_exists("uv")),
        ("git", command_exists("git")),
        ("workspace", (WORKSPACE / "AGENTS.md").exists()),
        ("nanobot config", (APP_SUPPORT / "nanobot/config.json").exists()),
        ("nanobot launcher", (APP_SUPPORT / "bin/run-nanobot.sh").exists()),
        ("mempalace venv", (RUNTIME / "venv/bin/mempalace").exists()),
        ("transcripted app data", (Path.home() / "Library/Application Support/Transcripted/captures").exists()),
        ("backup vault", VAULT.exists()),
    ]
    status = [{"name": name, "ok": ok} for name, ok in checks]
    if args.json:
        print(json.dumps(status, indent=2))
        return
    for item in status:
        print(("OK   " if item["ok"] else "WARN ") + item["name"])


def start(_: argparse.Namespace) -> None:
    run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(LAUNCH_AGENTS / "com.usefulaiagent.nanobot.plist")], check=False)
    run(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/com.usefulaiagent.nanobot"], check=False)


def stop(_: argparse.Namespace) -> None:
    run(["launchctl", "bootout", f"gui/{os.getuid()}/com.usefulaiagent.nanobot"], check=False)


def logs(_: argparse.Namespace) -> None:
    for path in sorted(LOG_DIR.glob("*.log"))[-5:]:
        print(f"== {path} ==")
        print(path.read_text(errors="replace")[-4000:])


def backup(_: argparse.Namespace) -> None:
    script = APP_SUPPORT / "bin/backup.sh"
    if not script.exists():
        raise SystemExit("Backup script missing. Run useful-agent install --guided.")
    run([str(script)])


def open_console(_: argparse.Namespace) -> None:
    run(["open", "http://127.0.0.1:8765"], check=False)


def open_telegram(_: argparse.Namespace) -> None:
    run(["open", "tg://resolve?domain=BotFather"], check=False)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="useful-agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("install")
    p.add_argument("--guided", action="store_true")
    p.add_argument("--telegram-token")
    p.set_defaults(func=install_guided)

    p = sub.add_parser("check")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=check)

    sub.add_parser("start").set_defaults(func=start)
    sub.add_parser("stop").set_defaults(func=stop)
    sub.add_parser("restart").set_defaults(func=lambda a: (stop(a), start(a)))
    sub.add_parser("logs").set_defaults(func=logs)
    sub.add_parser("backup").set_defaults(func=backup)
    sub.add_parser("open-console").set_defaults(func=open_console)
    sub.add_parser("open-telegram-setup").set_defaults(func=open_telegram)
    sub.add_parser("update").set_defaults(func=lambda _: run(["uv", "tool", "upgrade", "useful-agent"], check=False))
    sub.add_parser("uninstall").set_defaults(func=lambda _: print("Run docs/uninstall.md checklist; workspace/backups are never auto-deleted."))

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
