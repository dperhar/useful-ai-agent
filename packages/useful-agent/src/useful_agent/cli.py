from __future__ import annotations

import argparse
import getpass
import json
import os
import platform
import secrets
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


APP_SUPPORT = Path(os.environ.get("USEFUL_AGENT_APP_SUPPORT", Path.home() / "Library/Application Support/UsefulAIAgent"))
LOG_DIR = Path(os.environ.get("USEFUL_AGENT_LOG_DIR", Path.home() / "Library/Logs/UsefulAIAgent"))
WORKSPACE = Path(os.environ.get("USEFUL_AGENT_WORKSPACE", Path.home() / "Useful AI Agent Workspace"))
VAULT = APP_SUPPORT / "backups"
RUNTIME = APP_SUPPORT / "runtime"
RESTORES = APP_SUPPORT / "restores"
CONFIG_FILE = APP_SUPPORT / "config.json"
LAUNCH_AGENTS = Path.home() / "Library/LaunchAgents"
REPO_DIR = APP_SUPPORT / "source/useful-ai-agent"
SERVICE = "UsefulAIAgentBackup"
ACCOUNT = "bundle-password"
TELEGRAM_SERVICE = "UsefulAIAgentTelegram"
WEBSOCKET_SERVICE = "UsefulAIAgentWebSocket"
BACKUP_BRANCH = "backup-snapshot"


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
    for path in [APP_SUPPORT, LOG_DIR, WORKSPACE, VAULT, RUNTIME, RESTORES, LAUNCH_AGENTS, APP_SUPPORT / "bin"]:
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


def default_mirror_path() -> Path | None:
    icloud = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs"
    if icloud.exists():
        return icloud / "UsefulAIAgentBackups"
    return None


def default_config() -> dict:
    mirror = default_mirror_path()
    return {
        "backup": {
            "mirror_enabled": mirror is not None,
            "mirror_path": str(mirror) if mirror else "",
        }
    }


def load_config() -> dict:
    config = default_config()
    if CONFIG_FILE.exists():
        try:
            loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config.update(loaded)
                config["backup"] = {**default_config()["backup"], **loaded.get("backup", {})}
        except json.JSONDecodeError:
            pass
    return config


def save_config(config: dict) -> None:
    write(CONFIG_FILE, json.dumps(config, indent=2) + "\n", 0o600)


def ensure_config() -> dict:
    config = load_config()
    if not CONFIG_FILE.exists():
        save_config(config)
    return config


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
    ensure_config()
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
    copy_template("modules/backups/templates/backup.sh", APP_SUPPORT / "bin/backup.sh", {}, 0o755)
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
            "imageGeneration": {
                "enabled": True,
                "provider": "codex_cli",
                "model": "gpt-image-2",
                "defaultAspectRatio": "4:5",
                "defaultImageSize": "1K",
                "maxImagesPerTurn": 2,
            },
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
    for script in ["patch_nanobot_effort.py", "patch_nanobot_guest.py", "patch_nanobot_quote.py", "patch_nanobot_chat_hardening.py", "patch_nanobot_codex_errors.py", "patch_nanobot_custom_emoji.py", "patch_nanobot_codex_image_generation.py", "patch_nanobot_streamed_media_delivery.py"]:
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
    loop_text = loop_files[0].read_text(encoding="utf-8") if loop_files else ""
    if "_useful_agent_extract_one_turn_reasoning_effort" not in loop_text:
        failures.append("Nanobot effort patch marker missing")
    if "_useful_agent_expand_command_shortcuts" not in loop_text:
        failures.append("Nanobot /improve and /goal command marker patch missing")
    if not telegram_files or "_on_guest_update" not in telegram_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot guest mode patch marker missing")
    if not telegram_files or "_extract_text_quote" not in telegram_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot quote patch marker missing")
    if not telegram_files or "TELEGRAM_MEDIA_GROUP_DEBOUNCE_SECONDS" not in telegram_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot chat hardening patch marker missing")
    if not telegram_files or "_on_custom_emoji_id" not in telegram_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot custom emoji extractor patch marker missing")
    codex_files = list(target.glob("python*/site-packages/nanobot/providers/openai_codex_provider.py"))
    if not codex_files or "Codex provider call failed" not in codex_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot Codex error diagnostics patch marker missing")
    image_files = list(target.glob("python*/site-packages/nanobot/agent/tools/image_generation.py"))
    if not image_files or "_CodexCLIImageGenerationClient" not in image_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot Codex CLI image generation patch marker missing")
    manager_files = list(target.glob("python*/site-packages/nanobot/channels/manager.py"))
    if not manager_files or "_useful_agent_send_streamed_media_only" not in manager_files[0].read_text(encoding="utf-8"):
        failures.append("Nanobot streamed media delivery patch marker missing")
    if not command_exists("codex"):
        failures.append("Codex CLI missing. Install/login to Codex before enabling subscription image generation.")
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
    app_config = load_config()
    backup_config = app_config.get("backup", {})
    mirror_path = Path(str(backup_config.get("mirror_path") or "")).expanduser() if backup_config.get("mirror_path") else None
    latest_backups = discover_backups(limit=1)
    menu_app = Path.home() / "Applications/Useful Agent.app"
    patch_failures = verify_nanobot_patches() if (RUNTIME / "venv").exists() else ["Nanobot runtime not installed"]
    return [
        {"name": "macOS", "ok": platform.system() == "Darwin", "status": "ok" if platform.system() == "Darwin" else "fail"},
        {"name": "Apple Silicon", "ok": platform.machine() in {"arm64", "aarch64"}, "status": "ok" if platform.machine() in {"arm64", "aarch64"} else "fail"},
        {"name": "uv", "ok": find_uv() is not None, "status": "ok" if find_uv() else "manual_required"},
        {"name": "git", "ok": command_exists("git"), "status": "ok" if command_exists("git") else "manual_required"},
        {"name": "codex cli", "ok": command_exists("codex"), "status": "ok" if command_exists("codex") else "manual_required"},
        {"name": "workspace AGENTS.md", "ok": (WORKSPACE / "AGENTS.md").exists()},
        {"name": "nanobot config", "ok": config_path.exists()},
        {"name": "nanobot launcher", "ok": (APP_SUPPORT / "bin/run-nanobot.sh").exists()},
        {"name": "nanobot console script", "ok": (RUNTIME / "venv/bin/nanobot").exists()},
        {"name": "telegram allowed users", "ok": bool(telegram.get("allowFrom")), "enabled": bool(telegram.get("enabled")), "status": "ok" if telegram.get("allowFrom") else "manual_required"},
        {"name": "websocket local-only", "ok": websocket.get("host") == "127.0.0.1"},
        {"name": "websocket secret", "ok": bool(websocket.get("tokenIssueSecret"))},
        {"name": "image generation via Codex CLI", "ok": config.get("tools", {}).get("imageGeneration", {}).get("provider") == "codex_cli"},
        {"name": "mempalace mcp", "ok": (RUNTIME / "venv/bin/mempalace-mcp").exists()},
        {"name": "transcripted captures", "ok": (Path.home() / "Library/Application Support/Transcripted/captures").exists(), "status": "ok" if (Path.home() / "Library/Application Support/Transcripted/captures").exists() else "manual_required"},
        {"name": "backup vault", "ok": VAULT.exists()},
        {"name": "backup mirror configured", "ok": bool(backup_config.get("mirror_path")), "enabled": bool(backup_config.get("mirror_enabled")), "path": backup_config.get("mirror_path", "")},
        {"name": "backup mirror writable", "ok": bool(mirror_path and mirror_path.exists() and os.access(mirror_path, os.W_OK)), "status": "ok" if mirror_path and mirror_path.exists() and os.access(mirror_path, os.W_OK) else "warn"},
        {"name": "latest backup restorable candidate", "ok": bool(latest_backups), "latest": latest_backups[0] if latest_backups else None},
        {"name": "menu bar app installed", "ok": menu_app.exists(), "status": "ok" if menu_app.exists() else "warn"},
        {"name": "nanobot command patches", "ok": not patch_failures, "failures": patch_failures},
    ]


def check(args: argparse.Namespace) -> None:
    status = doctor_status()
    if args.json:
        print(json.dumps(status, indent=2))
        return
    for item in status:
        label = "OK   " if item["ok"] else ("TODO " if item.get("status") == "manual_required" else "WARN ")
        print(label + str(item["name"]))


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


def backup_password() -> str:
    existing = os.environ.get("USEFUL_AGENT_BACKUP_PASSWORD") or keychain_get(SERVICE, ACCOUNT)
    if existing:
        return existing
    print("Set backup password. It is stored in macOS Keychain, not in repo/logs.")
    password = getpass.getpass("Backup encryption password: ")
    confirm = getpass.getpass("Confirm backup encryption password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match.")
    keychain_set(SERVICE, ACCOUNT, password)
    return password


def openssl_encrypt(input_path: Path, output_path: Path, password: str) -> None:
    run([
        "openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "600000", "-md", "sha256",
        "-pass", "stdin", "-in", str(input_path), "-out", str(output_path),
    ], input_text=password)


def openssl_decrypt(input_path: Path, output_path: Path, password: str) -> None:
    run([
        "openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "600000", "-md", "sha256",
        "-pass", "stdin", "-in", str(input_path), "-out", str(output_path),
    ], input_text=password)


def copy_backup_to_mirror(artifact: Path, manifest: Path, config: dict) -> dict:
    backup_config = config.get("backup", {})
    enabled = bool(backup_config.get("mirror_enabled"))
    mirror_path = Path(str(backup_config.get("mirror_path") or "")).expanduser() if backup_config.get("mirror_path") else None
    result = {"enabled": enabled, "path": str(mirror_path) if mirror_path else "", "copied": False, "error": ""}
    if not enabled:
        return result
    if mirror_path is None:
        result["error"] = "mirror path is empty"
        return result
    try:
        mirror_path.mkdir(parents=True, exist_ok=True)
        mirror_artifact = mirror_path / artifact.name
        shutil.copy2(artifact, mirror_artifact)
        mirror_artifact.chmod(0o600)
        if os.environ.get("USEFUL_AGENT_SKIP_IMMUTABLE") != "1":
            run(["chflags", "uchg", str(mirror_artifact)], check=False)
        shutil.copy2(manifest, mirror_path / manifest.name)
        shutil.copy2(manifest, mirror_path / "workspace-latest.manifest.json")
        result["copied"] = True
    except Exception as exc:
        result["error"] = str(exc)
    return result


def create_backup(_: argparse.Namespace) -> None:
    ensure_dirs()
    config = ensure_config()
    password = backup_password()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    report = VAULT / f"backup-{ts}.report.txt"
    temp_root = Path(tempfile.mkdtemp(prefix="useful-agent-backup."))
    try:
        bundle = temp_root / "workspace.bundle"
        encrypted = temp_root / "workspace.bundle.enc"
        verify_bundle = temp_root / "verify.bundle"
        restore_smoke = temp_root / "restore"

        if not (WORKSPACE / ".git").exists():
            run(["git", "-C", str(WORKSPACE), "init"])
        run(["git", "-C", str(WORKSPACE), "config", "user.name", "Useful AI Agent Backup"])
        run(["git", "-C", str(WORKSPACE), "config", "user.email", "useful-agent-backup@local"])
        run(["git", "-C", str(WORKSPACE), "add", "-A"])
        has_head = run(["git", "-C", str(WORKSPACE), "rev-parse", "--verify", "HEAD"], check=False, capture=True).returncode == 0
        staged_clean = run(["git", "-C", str(WORKSPACE), "diff", "--cached", "--quiet"], check=False).returncode == 0
        if not has_head or not staged_clean:
            run(["git", "-C", str(WORKSPACE), "commit", "--allow-empty", "-m", f"Useful Agent backup snapshot {ts}"])

        head = run(["git", "-C", str(WORKSPACE), "rev-parse", "--short", "HEAD"], capture=True).stdout.strip()
        run(["git", "-C", str(WORKSPACE), "branch", "-f", BACKUP_BRANCH, "HEAD"])
        run(["git", "-C", str(WORKSPACE), "bundle", "create", str(bundle), f"refs/heads/{BACKUP_BRANCH}"])
        openssl_encrypt(bundle, encrypted, password)
        openssl_decrypt(encrypted, verify_bundle, password)
        run(["git", "bundle", "verify", str(verify_bundle)])
        run(["git", "clone", "-q", "-b", BACKUP_BRANCH, str(verify_bundle), str(restore_smoke)])

        artifact = VAULT / f"workspace-{ts}.bundle.enc"
        manifest = VAULT / f"workspace-{ts}.manifest.json"
        shutil.copy2(encrypted, artifact)
        artifact.chmod(0o600)
        if os.environ.get("USEFUL_AGENT_SKIP_IMMUTABLE") != "1":
            run(["chflags", "uchg", str(artifact)], check=False)
        shutil.copy2(artifact, VAULT / "workspace-latest.bundle.enc")

        manifest_data = {
            "schema": "useful-agent-backup/v1",
            "created_at": created_at,
            "workspace": str(WORKSPACE),
            "source_head": head,
            "encrypted_bundle": str(artifact),
            "branch": BACKUP_BRANCH,
            "verification": {"decrypt": True, "bundle": True, "restore_clone": True},
            "mirror": {"enabled": bool(config.get("backup", {}).get("mirror_enabled")), "path": config.get("backup", {}).get("mirror_path", "")},
        }
        write(manifest, json.dumps(manifest_data, indent=2) + "\n", 0o600)
        shutil.copy2(manifest, VAULT / "workspace-latest.manifest.json")
        mirror_result = copy_backup_to_mirror(artifact, manifest, config)
        manifest_data["mirror"] = mirror_result
        write(manifest, json.dumps(manifest_data, indent=2) + "\n", 0o600)
        shutil.copy2(manifest, VAULT / "workspace-latest.manifest.json")
        if mirror_result.get("copied"):
            mirror_path = Path(str(mirror_result.get("path") or "")).expanduser()
            if mirror_path.exists():
                shutil.copy2(manifest, mirror_path / manifest.name)
                shutil.copy2(manifest, mirror_path / "workspace-latest.manifest.json")

        report.write_text(
            f"Encrypted backup verified: {artifact}\n"
            f"Manifest: {manifest}\n"
            f"Mirror: {json.dumps(mirror_result, ensure_ascii=False)}\n",
            encoding="utf-8",
        )
        print(f"Encrypted backup verified: {artifact}")
        if mirror_result.get("copied"):
            print(f"Mirror copied: {mirror_result.get('path')}")
        elif mirror_result.get("enabled"):
            print(f"Mirror warning: {mirror_result.get('error')}")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def backup_search_locations() -> list[Path]:
    config = load_config()
    locations: list[Path] = []
    backup_config = config.get("backup", {})
    if backup_config.get("mirror_enabled") and backup_config.get("mirror_path"):
        locations.append(Path(str(backup_config["mirror_path"])).expanduser())
    locations.append(VAULT)
    return locations


def discover_backups(limit: int = 5) -> list[dict[str, object]]:
    seen: set[str] = set()
    items: list[dict[str, object]] = []
    for location in backup_search_locations():
        if not location.exists():
            continue
        for manifest in sorted(location.glob("workspace-*.manifest.json")):
            if manifest.name == "workspace-latest.manifest.json":
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            declared_artifact = Path(str(data.get("encrypted_bundle") or ""))
            sibling_artifact = manifest.with_name(manifest.name.replace(".manifest.json", ".bundle.enc"))
            artifact = sibling_artifact if sibling_artifact.exists() else declared_artifact
            key = artifact.name if artifact.exists() else manifest.name
            if key in seen:
                continue
            seen.add(key)
            items.append({
                "created_at": data.get("created_at") or "",
                "artifact": str(artifact),
                "manifest": str(manifest),
                "location": str(location),
                "legacy": False,
                "workspace": data.get("workspace") or "",
            })
        for artifact in sorted(location.glob("workspace-*.bundle.enc")):
            if artifact.name == "workspace-latest.bundle.enc":
                continue
            key = artifact.name
            if key in seen:
                continue
            seen.add(key)
            items.append({
                "created_at": datetime.fromtimestamp(artifact.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                "artifact": str(artifact),
                "manifest": "",
                "location": str(location),
                "legacy": True,
                "workspace": "",
            })
    items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return items[:limit]


def backup_list(args: argparse.Namespace) -> None:
    items = discover_backups(limit=args.limit)
    if args.json:
        print(json.dumps(items, indent=2))
        return
    if not items:
        print("No backups found.")
        return
    for idx, item in enumerate(items, start=1):
        legacy = " legacy/root-only" if item.get("legacy") else ""
        print(f"{idx}. {item.get('created_at')} {item.get('artifact')}{legacy}")


def restore_backup(args: argparse.Namespace) -> None:
    ensure_dirs()
    if args.file:
        artifact = Path(args.file).expanduser()
        item = {"artifact": str(artifact), "legacy": True}
    else:
        items = discover_backups(limit=max(args.latest, 5))
        if args.latest < 1 or args.latest > len(items):
            raise SystemExit(f"Backup index {args.latest} not found.")
        item = items[args.latest - 1]
        artifact = Path(str(item["artifact"]))
    if not artifact.exists():
        raise SystemExit(f"Backup artifact not found: {artifact}")

    password = backup_password()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    restore_dir = Path(args.output).expanduser() if args.output else RESTORES / f"restore-{ts}"
    if restore_dir.exists() and any(restore_dir.iterdir()):
        raise SystemExit(f"Restore target is not empty: {restore_dir}")
    restore_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="useful-agent-restore."))
    try:
        bundle = temp_root / "workspace.bundle"
        openssl_decrypt(artifact, bundle, password)
        run(["git", "bundle", "verify", str(bundle)])
        result = run(["git", "clone", "-q", "-b", BACKUP_BRANCH, str(bundle), str(restore_dir)], check=False, capture=True)
        if result.returncode != 0:
            run(["git", "clone", "-q", str(bundle), str(restore_dir)])
        print(f"Restored backup to: {restore_dir}")
        print("Safety: active workspace was not overwritten. Inspect the restore folder before replacing anything.")
        run(["open", str(restore_dir)], check=False, capture=True)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def backup_mirror(args: argparse.Namespace) -> None:
    ensure_dirs()
    config = ensure_config()
    config.setdefault("backup", {})
    if args.mirror_cmd == "enable":
        path = Path(args.path).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        config["backup"].update({"mirror_enabled": True, "mirror_path": str(path)})
        save_config(config)
        print(f"Backup mirror enabled: {path}")
    elif args.mirror_cmd == "disable":
        config["backup"]["mirror_enabled"] = False
        save_config(config)
        print("Backup mirror disabled.")
    else:
        backup_config = config.get("backup", {})
        print(json.dumps({
            "enabled": bool(backup_config.get("mirror_enabled")),
            "path": backup_config.get("mirror_path", ""),
            "writable": Path(str(backup_config.get("mirror_path") or "")).expanduser().is_dir() if backup_config.get("mirror_path") else False,
        }, indent=2))


def backup_open_folder(_: argparse.Namespace) -> None:
    config = load_config()
    backup_config = config.get("backup", {})
    target = Path(str(backup_config.get("mirror_path") or "")).expanduser() if backup_config.get("mirror_enabled") and backup_config.get("mirror_path") else VAULT
    target.mkdir(parents=True, exist_ok=True)
    run(["open", str(target)], check=False, capture=True)
    print(f"Opened backup folder: {target}")


def backup_entry(args: argparse.Namespace) -> None:
    if getattr(args, "backup_cmd", None) in {None, "create"}:
        create_backup(args)
    elif args.backup_cmd == "list":
        backup_list(args)
    elif args.backup_cmd == "restore":
        restore_backup(args)
    elif args.backup_cmd == "mirror":
        backup_mirror(args)
    elif args.backup_cmd == "open-folder":
        backup_open_folder(args)


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
    backup_parser = sub.add_parser("backup")
    backup_sub = backup_parser.add_subparsers(dest="backup_cmd")
    backup_parser.set_defaults(func=backup_entry, backup_cmd=None)
    backup_sub.add_parser("create").set_defaults(func=backup_entry)
    p = backup_sub.add_parser("list")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=backup_entry)
    p = backup_sub.add_parser("restore")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--latest", type=int)
    source.add_argument("--file")
    p.add_argument("--output")
    p.set_defaults(func=backup_entry)
    mirror = backup_sub.add_parser("mirror")
    mirror_sub = mirror.add_subparsers(dest="mirror_cmd", required=True)
    p = mirror_sub.add_parser("enable")
    p.add_argument("--path", required=True)
    p.set_defaults(func=backup_entry, backup_cmd="mirror")
    mirror_sub.add_parser("disable").set_defaults(func=backup_entry, backup_cmd="mirror")
    mirror_sub.add_parser("status").set_defaults(func=backup_entry, backup_cmd="mirror")
    backup_sub.add_parser("open-folder").set_defaults(func=backup_entry)
    sub.add_parser("open-console").set_defaults(func=open_console)
    sub.add_parser("open-telegram-setup").set_defaults(func=open_telegram)
    sub.add_parser("update").set_defaults(func=lambda _: run([find_uv() or "uv", "tool", "upgrade", "useful-agent"], check=False))
    sub.add_parser("uninstall").set_defaults(func=lambda _: print("Run docs/uninstall.md checklist; workspace/backups are never auto-deleted."))

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
