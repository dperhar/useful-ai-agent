from __future__ import annotations

import argparse
import getpass
import json
import os
import platform
import secrets
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
TELEGRAM_SERVICE = "UsefulAIAgentTelegram"
WEBSOCKET_SERVICE = "UsefulAIAgentWebSocket"


def run(cmd: list[str], *, check: bool = True, capture: bool = False, input_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, text=True, capture_output=capture, input=input_text)


def repo_root() -> Path:
    env = os.environ.get("USEFUL_AGENT_SOURCE_DIR")
    if env and (Path(env) / "modules").exists():
        return Path(env)

    source_file = APP_SUPPORT / "source-dir"
    if source_file.exists():
        source = Path(source_file.read_text(encoding="utf-8").strip())
        if (source / "modules").exists():
            return source

    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "README.md").exists() and (parent / "modules").exists():
            return parent
    if REPO_DIR.exists():
        return REPO_DIR
    return Path.cwd()


def ensure_dirs() -> None:
    for path in [APP_SUPPORT, LOG_DIR, WORKSPACE, VAULT, RUNTIME, LAUNCH_AGENTS, APP_SUPPORT / "bin"]:
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


def find_uv() -> str | None:
    for candidate in [
        shutil.which("uv"),
        str(Path.home() / ".local/bin/uv"),
        "/opt/homebrew/bin/uv",
        "/usr/local/bin/uv",
    ]:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def keychain_get(service: str, account: str) -> str | None:
    try:
        out = run(["security", "find-generic-password", "-w", "-s", service, "-a", account], capture=True)
        return out.stdout.strip()
    except Exception:
        return None


def keychain_set(service: str, account: str, value: str) -> bool:
    try:
        run(["security", "add-generic-password", "-U", "-s", service, "-a", account, "-w", value])
        return True
    except Exception:
        return False


def secret_file(name: str) -> Path:
    return APP_SUPPORT / "secrets" / name


def get_or_create_secret(service: str, account: str, filename: str) -> str:
    existing = keychain_get(service, account)
    if existing:
        return existing

    path = secret_file(filename)
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value

    value = secrets.token_urlsafe(32)
    if not keychain_set(service, account, value):
        write(path, value + "\n", 0o600)
    return value


def parse_allowed_users(raw: str | None) -> list[int | str]:
    if not raw:
        return []
    users: list[int | str] = []
    for part in raw.replace(",", " ").split():
        if not part:
            continue
        users.append(int(part) if part.lstrip("-").isdigit() else part)
    return users


def install_guided(args: argparse.Namespace) -> None:
    ensure_dirs()
    write(APP_SUPPORT / "source-dir", str(repo_root()) + "\n", 0o644)

    if platform.system() != "Darwin":
        raise SystemExit("Useful AI Agent v1 supports macOS only.")
    if platform.machine() not in {"arm64", "aarch64"}:
        raise SystemExit("Useful AI Agent v1 expects Apple Silicon for the full native profile.")

    uv = find_uv()
    if not uv:
        raise SystemExit("uv missing. Run bootstrap/macos.sh first.")

    print("1/8 preflight ok")
    install_workspace()

    print("2/8 installing Python runtime packages")
    run([uv, "venv", str(RUNTIME / "venv")])
    python = RUNTIME / "venv/bin/python"
    nanobot = RUNTIME / "venv/bin/nanobot"
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "nanobot-ai", "mempalace", "httpx"])

    print("3/8 installing skills")
    install_skills()

    print("4/8 configuring Telegram and WebSocket")
    token, allowed_users = collect_telegram(args)
    websocket_secret = get_or_create_secret(WEBSOCKET_SERVICE, "token-issue-secret", "websocket-token-issue-secret")
    config = build_nanobot_config(token, allowed_users, websocket_secret)
    write(APP_SUPPORT / "nanobot/config.json", json.dumps(config, indent=2) + "\n", 0o600)

    print("5/8 installing local MCP/tools")
    copy_template("modules/transcripted/transcripted-mcp", APP_SUPPORT / "bin/transcripted-mcp", {}, 0o755)
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

    print("6/8 applying Nanobot runtime patches")
    apply_nanobot_patches(python)

    print("7/8 installing LaunchAgent and desktop helpers")
    copy_template("modules/nanobot/templates/run-nanobot.sh", APP_SUPPORT / "bin/run-nanobot.sh", {
        "APP_SUPPORT": str(APP_SUPPORT),
        "WORKSPACE": str(WORKSPACE),
        "NANOBOT": str(nanobot),
    }, 0o755)
    copy_template("modules/nanobot/templates/com.usefulaiagent.nanobot.plist", LAUNCH_AGENTS / "com.usefulaiagent.nanobot.plist", {
        "APP_SUPPORT": str(APP_SUPPORT),
    })
    install_desktop_helpers()

    print("8/8 smoke tests")
    failures = smoke_test(nanobot)
    if failures:
        print("Install stopped before LaunchAgent start:")
        for failure in failures:
            print(f"- {failure}")
        print("Fix the items above, then run useful-agent start.")
        return

    run(["launchctl", "bootout", f"gui/{os.getuid()}/com.usefulaiagent.nanobot"], check=False)
    run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(LAUNCH_AGENTS / "com.usefulaiagent.nanobot.plist")], check=False)
    run(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/com.usefulaiagent.nanobot"], check=False)
    check(argparse.Namespace(json=False))


def install_workspace() -> None:
    print("Creating router-first workspace")
    replacements = {"WORKSPACE": str(WORKSPACE)}
    copy_template("modules/router/templates/AGENTS.md", WORKSPACE / "AGENTS.md", replacements)
    copy_template("modules/router/templates/CLAUDE.md", WORKSPACE / "CLAUDE.md", replacements)
    copy_template("modules/router/templates/cursor-router.mdc", WORKSPACE / ".cursor/rules/useful-agent-router.mdc", replacements)
    for folder in ["Canon", "Projects", "Clients", "Personal", "Inbox", "Archive", "Harness"]:
        (WORKSPACE / folder).mkdir(parents=True, exist_ok=True)
    copy_template("modules/router/templates/scoped-harness-AGENTS.md", WORKSPACE / "Harness/AGENTS.md", replacements)


def install_skills() -> None:
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


def collect_telegram(args: argparse.Namespace) -> tuple[str | None, list[int | str]]:
    token = args.telegram_token or keychain_get(TELEGRAM_SERVICE, "bot-token")
    if not token and args.guided:
        print("Create a Telegram bot in BotFather. Enable Guest Chat Mode, Allow Groups, and Group Privacy as needed.")
        token = getpass.getpass("Telegram bot token (hidden): ").strip()
    if token:
        keychain_set(TELEGRAM_SERVICE, "bot-token", token)

    allowed_users = parse_allowed_users(args.allow_user)
    if not allowed_users and args.guided and token:
        print("Telegram needs at least one allowed user id. Get it from @userinfobot or Telegram bot logs.")
        allowed_users = parse_allowed_users(input("Allowed Telegram user id(s), comma separated: ").strip())

    if token and not allowed_users:
        print("WARN: Telegram token is set, but allowed users are empty. Telegram channel will stay disabled.")
    return token, allowed_users


def build_nanobot_config(token: str | None, allowed_users: list[int | str], websocket_secret: str) -> dict:
    telegram_enabled = bool(token and allowed_users)
    return {
        "agents": {"defaults": {"workspace": str(WORKSPACE), "reasoningEffort": "medium"}},
        "channels": {
            "telegram": {
                "enabled": telegram_enabled,
                "token": token or "",
                "allowFrom": allowed_users,
                "guestMode": {"enabled": True, "replyMode": "final_only"},
            },
            "websocket": {
                "enabled": True,
                "host": "127.0.0.1",
                "port": 8765,
                "websocketRequiresToken": True,
                "tokenIssueSecret": websocket_secret,
            },
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


def apply_nanobot_patches(python: Path) -> None:
    patch_dir = repo_root() / "modules/nanobot/patches"
    for script in ["patch_nanobot_effort.py", "patch_nanobot_guest.py", "patch_nanobot_quote.py"]:
        run([str(python), str(patch_dir / script)])


def smoke_test(nanobot: Path) -> list[str]:
    failures: list[str] = []
    if not nanobot.exists():
        failures.append(f"nanobot console script missing: {nanobot}")
    config_path = APP_SUPPORT / "nanobot/config.json"
    if not config_path.exists():
        failures.append("Nanobot config missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        telegram = config.get("channels", {}).get("telegram", {})
        if telegram.get("enabled") and not telegram.get("allowFrom"):
            failures.append("Telegram enabled with empty allowFrom")
        websocket = config.get("channels", {}).get("websocket", {})
        if websocket.get("enabled") and not websocket.get("tokenIssueSecret"):
            failures.append("WebSocket enabled without tokenIssueSecret")
    patch_failures = verify_nanobot_patches()
    failures.extend(patch_failures)
    return failures


def verify_nanobot_patches() -> list[str]:
    failures: list[str] = []
    target = RUNTIME / "venv/lib"
    loop_files = list(target.glob("python*/site-packages/nanobot/agent/loop.py"))
    telegram_files = list(target.glob("python*/site-packages/nanobot/channels/telegram.py"))
    if not loop_files or "_useful_agent_extract_one_turn_reasoning_effort" not in loop_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot effort patch marker missing")
    if not telegram_files or "_on_guest_update" not in telegram_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot guest mode patch marker missing")
    if not telegram_files or "_extract_text_quote" not in telegram_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot quote patch marker missing")
    return failures


def install_desktop_helpers() -> None:
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        write(desktop / "Start Useful AI Agent.command", f'#!/bin/zsh\n"{APP_SUPPORT}/bin/run-nanobot.sh"\n', 0o755)
        write(desktop / "Check Useful AI Agent.command", f'#!/bin/zsh\n"useful-agent" doctor; read "?Press enter to close."\n', 0o755)


def doctor_status() -> list[dict[str, object]]:
    config_path = APP_SUPPORT / "nanobot/config.json"
    config: dict = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            config = {}
    telegram = config.get("channels", {}).get("telegram", {}) if config else {}
    websocket = config.get("channels", {}).get("websocket", {}) if config else {}
    return [
        {"name": "macOS", "ok": platform.system() == "Darwin"},
        {"name": "Apple Silicon", "ok": platform.machine() in {"arm64", "aarch64"}},
        {"name": "uv", "ok": find_uv() is not None},
        {"name": "git", "ok": command_exists("git")},
        {"name": "workspace AGENTS.md", "ok": (WORKSPACE / "AGENTS.md").exists()},
        {"name": "nanobot config", "ok": config_path.exists()},
        {"name": "nanobot launcher", "ok": (APP_SUPPORT / "bin/run-nanobot.sh").exists()},
        {"name": "nanobot console script", "ok": (RUNTIME / "venv/bin/nanobot").exists()},
        {"name": "telegram allowed users", "ok": bool(telegram.get("allowFrom")), "enabled": bool(telegram.get("enabled"))},
        {"name": "websocket local-only", "ok": websocket.get("host") == "127.0.0.1"},
        {"name": "websocket secret", "ok": bool(websocket.get("tokenIssueSecret"))},
        {"name": "mempalace mcp", "ok": (RUNTIME / "venv/bin/mempalace-mcp").exists()},
        {"name": "transcripted captures", "ok": (Path.home() / "Library/Application Support/Transcripted/captures").exists()},
        {"name": "backup vault", "ok": VAULT.exists()},
    ]


def check(args: argparse.Namespace) -> None:
    status = doctor_status()
    if args.json:
        print(json.dumps(status, indent=2))
        return
    for item in status:
        print(("OK   " if item["ok"] else "WARN ") + str(item["name"]))


def configure_telegram(args: argparse.Namespace) -> None:
    ensure_dirs()
    token, allowed_users = collect_telegram(args)
    config_path = APP_SUPPORT / "nanobot/config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else build_nanobot_config(None, [], get_or_create_secret(WEBSOCKET_SERVICE, "token-issue-secret", "websocket-token-issue-secret"))
    config["channels"]["telegram"] = build_nanobot_config(token, allowed_users, config["channels"]["websocket"].get("tokenIssueSecret") or get_or_create_secret(WEBSOCKET_SERVICE, "token-issue-secret", "websocket-token-issue-secret"))["channels"]["telegram"]
    write(config_path, json.dumps(config, indent=2) + "\n", 0o600)
    print("Telegram config updated. Run useful-agent restart.")


def configure_websocket(_: argparse.Namespace) -> None:
    ensure_dirs()
    secret = get_or_create_secret(WEBSOCKET_SERVICE, "token-issue-secret", "websocket-token-issue-secret")
    config_path = APP_SUPPORT / "nanobot/config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else build_nanobot_config(None, [], secret)
    config.setdefault("channels", {}).setdefault("websocket", {})
    config["channels"]["websocket"].update({
        "enabled": True,
        "host": "127.0.0.1",
        "port": 8765,
        "websocketRequiresToken": True,
        "tokenIssueSecret": secret,
    })
    write(config_path, json.dumps(config, indent=2) + "\n", 0o600)
    print("WebSocket secret configured in Keychain or local 0600 fallback. It was not printed.")


def configure_adapters(args: argparse.Namespace) -> None:
    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    replacements = {"WORKSPACE": str(target)}
    copy_template("modules/router/templates/AGENTS.md", target / "AGENTS.md", replacements)
    copy_template("modules/router/templates/CLAUDE.md", target / "CLAUDE.md", replacements)
    copy_template("modules/router/templates/cursor-router.mdc", target / ".cursor/rules/useful-agent-router.mdc", replacements)
    print(f"Installed Codex/Claude/Cursor workspace adapters in {target}")


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
    print("Nanobot WebSocket is local-only at 127.0.0.1:8765 and is not a browser console.")
    print("Run: useful-agent doctor")


def open_telegram(_: argparse.Namespace) -> None:
    run(["open", "tg://resolve?domain=BotFather"], check=False)


def menu_install(_: argparse.Namespace) -> None:
    ensure_dirs()
    app_dir = Path.home() / "Applications/Useful Agent.app"
    macos = app_dir / "Contents/MacOS"
    resources = app_dir / "Contents/Resources"
    macos.mkdir(parents=True, exist_ok=True)
    resources.mkdir(parents=True, exist_ok=True)
    binary = macos / "UsefulAgentMenuBar"
    source = repo_root() / "apps/menu-bar/Sources/UsefulAgentMenuBar/main.swift"
    run(["swiftc", str(source), "-o", str(binary)])
    binary.chmod(0o755)
    write(app_dir / "Contents/Info.plist", """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>UsefulAgentMenuBar</string>
<key>CFBundleIdentifier</key><string>com.usefulaiagent.menubar</string>
<key>CFBundleName</key><string>Useful Agent</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
</dict></plist>
""")
    run(["open", str(app_dir)], check=False)
    print(f"Installed unsigned local menu bar app: {app_dir}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="useful-agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("install")
    p.add_argument("--guided", action="store_true")
    p.add_argument("--telegram-token")
    p.add_argument("--allow-user")
    p.set_defaults(func=install_guided)

    for name in ["check", "doctor"]:
        p = sub.add_parser(name)
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=check)

    configure = sub.add_parser("configure")
    configure_sub = configure.add_subparsers(dest="configure_cmd", required=True)
    p = configure_sub.add_parser("telegram")
    p.add_argument("--guided", action="store_true")
    p.add_argument("--telegram-token")
    p.add_argument("--allow-user")
    p.set_defaults(func=configure_telegram)
    configure_sub.add_parser("websocket").set_defaults(func=configure_websocket)
    p = configure_sub.add_parser("adapters")
    p.add_argument("--target", default=str(WORKSPACE))
    p.set_defaults(func=configure_adapters)

    menu = sub.add_parser("menu")
    menu_sub = menu.add_subparsers(dest="menu_cmd", required=True)
    menu_sub.add_parser("install").set_defaults(func=menu_install)

    sub.add_parser("start").set_defaults(func=start)
    sub.add_parser("stop").set_defaults(func=stop)
    sub.add_parser("restart").set_defaults(func=lambda a: (stop(a), start(a)))
    sub.add_parser("logs").set_defaults(func=logs)
    sub.add_parser("backup").set_defaults(func=backup)
    sub.add_parser("open-console").set_defaults(func=open_console)
    sub.add_parser("open-telegram-setup").set_defaults(func=open_telegram)
    sub.add_parser("update").set_defaults(func=lambda _: run([find_uv() or "uv", "tool", "upgrade", "useful-agent"], check=False))
    sub.add_parser("uninstall").set_defaults(func=lambda _: print("Run docs/uninstall.md checklist; workspace/backups are never auto-deleted."))

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
