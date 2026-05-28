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
from typing import Any


APP_SUPPORT = Path(os.environ.get("USEFUL_AGENT_APP_SUPPORT", Path.home() / "Library/Application Support/UsefulAIAgent"))
CONFIG_FILE = APP_SUPPORT / "config.json"
LAUNCH_AGENTS = Path.home() / "Library/LaunchAgents"
REPO_DIR = APP_SUPPORT / "source/useful-ai-agent"
SERVICE = "UsefulAIAgentBackup"
ACCOUNT = "bundle-password"
TELEGRAM_SERVICE = "UsefulAIAgentTelegram"
WEBSOCKET_SERVICE = "UsefulAIAgentWebSocket"
BACKUP_BRANCH = "backup-snapshot"

PROJECT_ROOT = Path(os.environ.get("USEFUL_AGENT_PROJECT_ROOT", Path.cwd())).expanduser()
INSTALL_ROOT = Path(os.environ.get("USEFUL_AGENT_INSTALL_ROOT", PROJECT_ROOT / "Useful Agent")).expanduser()
WORKSPACE = Path(os.environ.get("USEFUL_AGENT_WORKSPACE", INSTALL_ROOT / "workspace")).expanduser()
STATE_DIR = INSTALL_ROOT / "state"
RUNTIME = INSTALL_ROOT / "runtime"
VAULT = APP_SUPPORT / "backups" / "default"
RESTORES = APP_SUPPORT / "restores" / "default"
LOG_DIR = Path(os.environ.get("USEFUL_AGENT_LOG_DIR", Path.home() / "Library/Logs/UsefulAIAgent/default"))


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
    for path in [APP_SUPPORT, LOG_DIR, INSTALL_ROOT, WORKSPACE, STATE_DIR, VAULT, RUNTIME, RESTORES, LAUNCH_AGENTS, APP_SUPPORT / "bin"]:
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


def slug_path(path: Path) -> str:
    slug = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in str(path.expanduser()))
    slug = "-".join(part for part in slug.split("-") if part)
    return slug[-80:] or "default"


def default_install_root(project_root: Path) -> Path:
    if (project_root / "Harness").exists():
        return project_root / "Harness/useful-agent-runtime"
    return project_root / "Useful Agent"


def default_workspace_for(install_root: Path) -> Path:
    return install_root / "workspace"


def default_config() -> dict:
    mirror = default_mirror_path()
    project_root_raw = os.environ.get("USEFUL_AGENT_PROJECT_ROOT", "")
    project_root = Path(project_root_raw).expanduser() if project_root_raw else None
    install_root_raw = os.environ.get("USEFUL_AGENT_INSTALL_ROOT", "")
    install_root = Path(install_root_raw).expanduser() if install_root_raw else (default_install_root(project_root) if project_root else None)
    return {
        "project": {
            "root": str(project_root) if project_root else "",
            "install_root": str(install_root) if install_root else "",
            "workspace": str(default_workspace_for(install_root)) if install_root else "",
        },
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
                config["project"] = {**default_config()["project"], **loaded.get("project", {})}
                config["backup"] = {**default_config()["backup"], **loaded.get("backup", {})}
        except json.JSONDecodeError:
            pass
    return config


def save_config(config: dict) -> None:
    write(CONFIG_FILE, json.dumps(config, indent=2) + "\n", 0o600)


def apply_config_paths(config: dict) -> None:
    global PROJECT_ROOT, INSTALL_ROOT, WORKSPACE, STATE_DIR, RUNTIME, VAULT, RESTORES, LOG_DIR

    project = config.get("project", {})
    root_raw = project.get("root") or os.environ.get("USEFUL_AGENT_PROJECT_ROOT") or str(Path.cwd())
    PROJECT_ROOT = Path(str(root_raw)).expanduser().resolve()
    install_raw = project.get("install_root") or os.environ.get("USEFUL_AGENT_INSTALL_ROOT") or str(default_install_root(PROJECT_ROOT))
    INSTALL_ROOT = Path(str(install_raw)).expanduser()
    workspace_raw = project.get("workspace") or os.environ.get("USEFUL_AGENT_WORKSPACE") or str(default_workspace_for(INSTALL_ROOT))
    WORKSPACE = Path(str(workspace_raw)).expanduser()
    STATE_DIR = INSTALL_ROOT / "state"
    RUNTIME = INSTALL_ROOT / "runtime"

    profile = slug_path(PROJECT_ROOT)
    VAULT = APP_SUPPORT / "backups" / profile
    RESTORES = APP_SUPPORT / "restores" / profile
    LOG_DIR = Path(os.environ.get("USEFUL_AGENT_LOG_DIR", Path.home() / f"Library/Logs/UsefulAIAgent/{profile}"))


def ensure_config() -> dict:
    APP_SUPPORT.mkdir(parents=True, exist_ok=True)
    config = load_config()
    if not CONFIG_FILE.exists():
        save_config(config)
    apply_config_paths(config)
    return config


def configure_project(args: argparse.Namespace) -> dict:
    APP_SUPPORT.mkdir(parents=True, exist_ok=True)
    config = load_config()
    project_root = Path(args.project_root).expanduser() if getattr(args, "project_root", None) else None
    if project_root is None and getattr(args, "guided", False):
        default_root = Path.cwd()
        entered = input(f"Project root folder [{default_root}]: ").strip()
        project_root = Path(entered).expanduser() if entered else default_root
    if project_root is None:
        project_root = Path(config.get("project", {}).get("root") or Path.cwd()).expanduser()
    project_root = project_root.resolve()

    install_root = Path(args.install_root).expanduser() if getattr(args, "install_root", None) else None
    if install_root is None:
        existing = config.get("project", {}).get("install_root")
        default_install = Path(existing).expanduser() if existing else default_install_root(project_root)
        if getattr(args, "guided", False):
            entered = input(f"Useful Agent runtime folder [{default_install}]: ").strip()
            install_root = Path(entered).expanduser() if entered else default_install
        else:
            install_root = default_install

    workspace = default_workspace_for(install_root)
    config["project"] = {
        "root": str(project_root),
        "install_root": str(install_root),
        "workspace": str(workspace),
    }
    save_config(config)
    apply_config_paths(config)
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
    configure_project(args)
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
    install_project_adapters(PROJECT_ROOT)
    install_backup_policy()

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
    print("Creating project-local runtime workspace")
    replacements = {"WORKSPACE": str(WORKSPACE)}
    copy_template("modules/router/templates/AGENTS.md", WORKSPACE / "AGENTS.md", replacements)
    copy_template("modules/router/templates/CLAUDE.md", WORKSPACE / "CLAUDE.md", replacements)
    copy_template("modules/router/templates/cursor-router.mdc", WORKSPACE / ".cursor/rules/useful-agent-router.mdc", replacements)
    for folder in ["Canon", "Projects", "Clients", "Personal", "Inbox", "Archive", "Harness"]:
        (WORKSPACE / folder).mkdir(parents=True, exist_ok=True)
    copy_template("modules/router/templates/scoped-harness-AGENTS.md", WORKSPACE / "Harness/AGENTS.md", replacements)
    install_source_save_policy()


def install_source_save_policy() -> None:
    write(WORKSPACE / "Harness/source-save-policy.md", f"""# Source Save Policy

Project root: `{PROJECT_ROOT}`

When the user asks to persist information, the agent must update source of
truth files, not only local memory.

## Save Flow

1. Identify whether the request is a persistence request. Trigger words include:
   save, remember, record, write down, log, зафиксируй, запиши, сохрани, добавь в контекст.
2. Choose the destination using the nearest `AGENTS.md` routing table.
3. Append to an existing `.md` file whenever possible.
4. If no destination is obvious, append to `Inbox/` and mention the unresolved routing.
5. Also write the compact durable fact to local memory for retrieval.
6. Never silently save only to local memory when the user asked for persistence.

## Append Format

Use a timestamped append block:

```md
### YYYY-MM-DD HH:MM - Short title

Source: Telegram / local agent / meeting / manual note.

- Durable fact:
- Context:
- Follow-up:
```

Keep the original file history intact unless the user explicitly asks for a rewrite.
""")


def copy_template_if_absent(name: str, target: Path, replacements: dict[str, str] | None = None, mode: int | None = None) -> bool:
    if target.exists():
        return False
    copy_template(name, target, replacements, mode)
    return True


def install_project_adapters(target: Path) -> None:
    replacements = {"WORKSPACE": str(target)}
    copy_template_if_absent("modules/router/templates/AGENTS.md", target / "AGENTS.md", replacements)
    copy_template_if_absent("modules/router/templates/CLAUDE.md", target / "CLAUDE.md", replacements)
    copy_template_if_absent("modules/router/templates/cursor-router.mdc", target / ".cursor/rules/useful-agent-router.mdc", replacements)


def backup_config_dir() -> Path:
    return INSTALL_ROOT / "config/backups"


def backup_excludes_file() -> Path:
    return backup_config_dir() / "backup-excludes.txt"


def backup_nested_policy_file() -> Path:
    return backup_config_dir() / "backup-nested-repos.txt"


def install_backup_policy() -> None:
    excludes = backup_excludes_file()
    nested = backup_nested_policy_file()
    if not excludes.exists():
        write(excludes, """# Useful Agent backup-only excludes.
# This is not .gitignore. It only prevents local runtime/build/model junk from
# making encrypted backups too large.
Useful Agent/runtime/
Useful Agent/state/cache/
Harness/useful-agent-runtime/runtime/
Harness/useful-agent-runtime/state/cache/
.git/
.DS_Store
node_modules/
.venv/
venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
target/
dist/
build/
*.gguf
*.safetensors
*.onnx
*.dylib
*.so
*.a
*.o
*.tmp
*.log
""")
    if not nested.exists():
        write(nested, """# action|relative/path|reason
# action: snapshot or skip. Empty file means auto-snapshot discovered nested repos.
""")


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
        "agents": {
            "defaults": {
                "workspace": str(WORKSPACE),
                "projectRoot": str(PROJECT_ROOT),
                "reasoningEffort": "medium",
            }
        },
        "workspace": {
            "projectRoot": str(PROJECT_ROOT),
            "installRoot": str(INSTALL_ROOT),
            "scratch": str(WORKSPACE),
            "mode": "project-local-no-source-duplication",
        },
        "sourceOfTruth": {
            "enabled": True,
            "projectRoot": str(PROJECT_ROOT),
            "policyFile": str(WORKSPACE / "Harness/source-save-policy.md"),
            "writeMode": "append-only-routed-markdown",
            "memoryIsNotEnoughForPersistenceRequests": True,
        },
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
                    "args": ["--palace", str(STATE_DIR / "mempalace/palace")],
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
    apply_config_paths(load_config())
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
        {"name": "project root", "ok": PROJECT_ROOT.exists(), "path": str(PROJECT_ROOT)},
        {"name": "project-local install root", "ok": str(INSTALL_ROOT).startswith(str(PROJECT_ROOT)), "path": str(INSTALL_ROOT)},
        {"name": "source save policy", "ok": (WORKSPACE / "Harness/source-save-policy.md").exists()},
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
    ensure_config()
    ensure_dirs()
    token, allowed_users = collect_telegram(args)
    config_path = APP_SUPPORT / "nanobot/config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else build_nanobot_config(None, [], get_or_create_secret(WEBSOCKET_SERVICE, "token-issue-secret", "websocket-token-issue-secret"))
    config["channels"]["telegram"] = build_nanobot_config(token, allowed_users, config["channels"]["websocket"].get("tokenIssueSecret") or get_or_create_secret(WEBSOCKET_SERVICE, "token-issue-secret", "websocket-token-issue-secret"))["channels"]["telegram"]
    write(config_path, json.dumps(config, indent=2) + "\n", 0o600)
    print("Telegram config updated. Run useful-agent restart.")


def configure_websocket(_: argparse.Namespace) -> None:
    ensure_config()
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
    ensure_config()
    target = Path(args.target).expanduser().resolve() if args.target else PROJECT_ROOT
    target.mkdir(parents=True, exist_ok=True)
    replacements = {"WORKSPACE": str(target)}
    copy_template("modules/router/templates/AGENTS.md", target / "AGENTS.md", replacements)
    copy_template("modules/router/templates/CLAUDE.md", target / "CLAUDE.md", replacements)
    copy_template("modules/router/templates/cursor-router.mdc", target / ".cursor/rules/useful-agent-router.mdc", replacements)
    print(f"Installed Codex/Claude/Cursor workspace adapters in {target}")


def configure_project_cmd(args: argparse.Namespace) -> None:
    config = configure_project(args)
    ensure_dirs()
    install_backup_policy()
    print(json.dumps(config["project"], indent=2))


def start(_: argparse.Namespace) -> None:
    ensure_config()
    run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(LAUNCH_AGENTS / "com.usefulaiagent.nanobot.plist")], check=False)
    run(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/com.usefulaiagent.nanobot"], check=False)


def stop(_: argparse.Namespace) -> None:
    ensure_config()
    run(["launchctl", "bootout", f"gui/{os.getuid()}/com.usefulaiagent.nanobot"], check=False)


def logs(_: argparse.Namespace) -> None:
    ensure_config()
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


def copy_backup_to_mirror(artifact: Path, manifest: Path, config: dict, latest_manifest_name: str = "project-latest.manifest.json") -> dict:
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
        shutil.copy2(manifest, mirror_path / latest_manifest_name)
        result["copied"] = True
    except Exception as exc:
        result["error"] = str(exc)
    return result


def git_snapshot_bundle(source_dir: Path, snapshot_git: Path, bundle_path: Path, label: str, excludes: list[str] | None = None) -> str:
    run(["git", f"--git-dir={snapshot_git}", "init", "-q"])
    run(["git", f"--git-dir={snapshot_git}", "config", "user.name", "Useful AI Agent Backup"])
    run(["git", f"--git-dir={snapshot_git}", "config", "user.email", "useful-agent-backup@local"])
    run(["git", f"--git-dir={snapshot_git}", "config", "core.autocrlf", "false"])
    run(["git", f"--git-dir={snapshot_git}", "config", "advice.detachedHead", "false"])
    if excludes:
        info = snapshot_git / "info"
        info.mkdir(parents=True, exist_ok=True)
        (info / "exclude").write_text("\n".join(excludes) + "\n", encoding="utf-8")
    run(["git", f"--git-dir={snapshot_git}", f"--work-tree={source_dir}", "add", "-A", "--", "."])
    tree = run(["git", f"--git-dir={snapshot_git}", "write-tree"], capture=True).stdout.strip()
    commit = run(["git", f"--git-dir={snapshot_git}", "commit-tree", tree], input_text=f"{label} working-tree snapshot\n", capture=True).stdout.strip()
    run(["git", f"--git-dir={snapshot_git}", "update-ref", "refs/heads/snapshot", commit])
    run(["git", f"--git-dir={snapshot_git}", "fsck", "--no-progress"])
    run(["git", f"--git-dir={snapshot_git}", "bundle", "create", str(bundle_path), "refs/heads/snapshot"])
    run(["git", "bundle", "verify", str(bundle_path)])
    return run(["git", f"--git-dir={snapshot_git}", "rev-parse", "--short", commit], capture=True).stdout.strip()


def read_backup_excludes(source_dir: Path) -> list[str]:
    install_backup_policy()
    excludes: list[str] = []
    if backup_excludes_file().exists():
        for line in backup_excludes_file().read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                excludes.append(stripped)
    return excludes


def discover_nested_repos(source_dir: Path) -> list[Path]:
    nested: list[Path] = []
    for git_dir in source_dir.rglob(".git"):
        if git_dir == source_dir / ".git":
            continue
        if any(part in {".Trash", "node_modules", "runtime", ".venv", "venv"} for part in git_dir.parts):
            continue
        if git_dir.is_dir():
            nested.append(git_dir.parent)
    return sorted(nested)


def read_nested_policy(source_dir: Path) -> dict[str, tuple[str, str]]:
    install_backup_policy()
    policy: dict[str, tuple[str, str]] = {}
    path = backup_nested_policy_file()
    if not path.exists():
        return policy
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split("|", 2)
        if len(parts) < 2:
            continue
        action = parts[0].strip()
        rel = parts[1].strip().rstrip("/")
        reason = parts[2].strip() if len(parts) > 2 else ""
        if action in {"snapshot", "skip"} and rel:
            policy[rel] = (action, reason)
    return policy


def artifact_from_manifest(data: dict[str, Any], manifest_path: Path | None = None) -> Path | None:
    if manifest_path:
        candidate = manifest_path.with_name(manifest_path.name.replace(".manifest.json", ".root.bundle.enc"))
        if candidate.exists():
            return candidate
        candidate = manifest_path.with_name(manifest_path.name.replace(".manifest.json", ".bundle.enc"))
        if candidate.exists():
            return candidate
    root = data.get("root") if isinstance(data.get("root"), dict) else None
    raw = root.get("encrypted_bundle") if root else data.get("encrypted_bundle")
    if raw:
        candidate = Path(str(raw)).expanduser()
        if candidate.exists():
            return candidate
    return None


def create_backup(_: argparse.Namespace) -> None:
    config = ensure_config()
    ensure_dirs()
    password = backup_password()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    report = VAULT / f"backup-{ts}.report.txt"
    temp_root = Path(tempfile.mkdtemp(prefix="useful-agent-backup."))
    try:
        source_dir = PROJECT_ROOT
        bundle = temp_root / f"project-{ts}.root.bundle"
        encrypted = temp_root / f"project-{ts}.root.bundle.enc"
        verify_bundle = temp_root / f"project-{ts}.root.verify.bundle"
        restore_smoke = temp_root / "root-restore-smoke"

        if not source_dir.exists():
            raise SystemExit(f"Project root does not exist: {source_dir}")

        root_excludes = read_backup_excludes(source_dir)
        nested_repos = discover_nested_repos(source_dir)
        for nested_repo in nested_repos:
            root_excludes.append(str(nested_repo.relative_to(source_dir)).rstrip("/") + "/")

        snapshot_head = git_snapshot_bundle(source_dir, temp_root / "root-snapshot.git", bundle, str(source_dir), root_excludes)
        openssl_encrypt(bundle, encrypted, password)
        openssl_decrypt(encrypted, verify_bundle, password)
        run(["git", "bundle", "verify", str(verify_bundle)])
        run(["git", "clone", "-q", "-b", "snapshot", str(verify_bundle), str(restore_smoke)])

        nested_policy = read_nested_policy(source_dir)
        nested_records: list[dict[str, Any]] = []
        for nested_repo in nested_repos:
            rel = str(nested_repo.relative_to(source_dir))
            action, reason = nested_policy.get(rel, ("snapshot", "auto-discovered nested git repository"))
            branch = run(["git", "-C", str(nested_repo), "branch", "--show-current"], check=False, capture=True).stdout.strip()
            changed_raw = run(["git", "-C", str(nested_repo), "status", "--porcelain"], check=False, capture=True).stdout
            changed_files = len([line for line in changed_raw.splitlines() if line.strip()])
            record: dict[str, Any] = {
                "action": action,
                "path": rel,
                "branch": branch or None,
                "changed_files": changed_files,
                "reason": reason,
            }
            if action == "snapshot":
                slug = slug_path(Path(rel))
                nested_bundle = temp_root / f"project-{ts}.nested-{slug}.bundle"
                nested_enc = temp_root / f"project-{ts}.nested-{slug}.bundle.enc"
                nested_verify = temp_root / f"project-{ts}.nested-{slug}.verify.bundle"
                nested_head = git_snapshot_bundle(nested_repo, temp_root / f"nested-{slug}.git", nested_bundle, rel, read_backup_excludes(nested_repo))
                openssl_encrypt(nested_bundle, nested_enc, password)
                openssl_decrypt(nested_enc, nested_verify, password)
                run(["git", "bundle", "verify", str(nested_verify)])
                nested_final = VAULT / f"project-{ts}.nested-{slug}.bundle.enc"
                shutil.copy2(nested_enc, nested_final)
                nested_final.chmod(0o600)
                if os.environ.get("USEFUL_AGENT_SKIP_IMMUTABLE") != "1":
                    run(["chflags", "uchg", str(nested_final)], check=False)
                record.update({"status": "ok", "encrypted_bundle": str(nested_final), "snapshot_head": nested_head})
            else:
                record.update({"status": "skipped", "encrypted_bundle": None, "snapshot_head": None})
            nested_records.append(record)

        artifact = VAULT / f"project-{ts}.root.bundle.enc"
        manifest = VAULT / f"project-{ts}.manifest.json"
        shutil.copy2(encrypted, artifact)
        artifact.chmod(0o600)
        if os.environ.get("USEFUL_AGENT_SKIP_IMMUTABLE") != "1":
            run(["chflags", "uchg", str(artifact)], check=False)
        shutil.copy2(artifact, VAULT / "project-latest.root.bundle.enc")

        manifest_data = {
            "schema": "useful-agent-backup-set/v2",
            "created_at": created_at,
            "project_root": str(source_dir),
            "install_root": str(INSTALL_ROOT),
            "workspace": str(WORKSPACE),
            "root": {
                "encrypted_bundle": str(artifact),
                "snapshot_head": snapshot_head,
                "branch": "snapshot",
            },
            "nested_repositories": nested_records,
            "policy": {
                "excludes": str(backup_excludes_file()),
                "nested": str(backup_nested_policy_file()),
            },
            "verification": {"decrypt": True, "bundle": True, "restore_clone": True},
            "mirror": {"enabled": bool(config.get("backup", {}).get("mirror_enabled")), "path": config.get("backup", {}).get("mirror_path", "")},
        }
        write(manifest, json.dumps(manifest_data, indent=2) + "\n", 0o600)
        shutil.copy2(manifest, VAULT / "project-latest.manifest.json")
        mirror_result = copy_backup_to_mirror(artifact, manifest, config)
        manifest_data["mirror"] = mirror_result
        write(manifest, json.dumps(manifest_data, indent=2) + "\n", 0o600)
        shutil.copy2(manifest, VAULT / "project-latest.manifest.json")
        if mirror_result.get("copied"):
            mirror_path = Path(str(mirror_result.get("path") or "")).expanduser()
            if mirror_path.exists():
                shutil.copy2(manifest, mirror_path / manifest.name)
                shutil.copy2(manifest, mirror_path / "project-latest.manifest.json")

        report.write_text(
            f"Encrypted backup verified: {artifact}\n"
            f"Manifest: {manifest}\n"
            f"Project root: {source_dir}\n"
            f"Nested repositories: {len(nested_records)}\n"
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
    config = ensure_config()
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
        for manifest in sorted([*location.glob("project-*.manifest.json"), *location.glob("workspace-*.manifest.json")]):
            if manifest.name in {"workspace-latest.manifest.json", "project-latest.manifest.json"}:
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            artifact = artifact_from_manifest(data, manifest)
            if artifact is None:
                continue
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
                "schema": data.get("schema") or "",
                "project_root": data.get("project_root") or data.get("repo") or "",
                "workspace": data.get("workspace") or "",
                "nested_count": len(data.get("nested_repositories") or []),
            })
        for artifact in sorted([*location.glob("project-*.root.bundle.enc"), *location.glob("workspace-*.bundle.enc")]):
            if artifact.name in {"workspace-latest.bundle.enc", "project-latest.root.bundle.enc"}:
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
                "schema": "legacy/root-only",
                "project_root": "",
                "workspace": "",
                "nested_count": 0,
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
    ensure_config()
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
        result = run(["git", "clone", "-q", "-b", "snapshot", str(bundle), str(restore_dir)], check=False, capture=True)
        if result.returncode != 0:
            run(["git", "clone", "-q", str(bundle), str(restore_dir)])
        print(f"Restored backup to: {restore_dir}")
        print("Safety: active project was not overwritten. Inspect the restore folder before replacing anything.")
        run(["open", str(restore_dir)], check=False, capture=True)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def backup_mirror(args: argparse.Namespace) -> None:
    config = ensure_config()
    ensure_dirs()
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
    ensure_config()
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


def open_project(_: argparse.Namespace) -> None:
    run(["open", str(PROJECT_ROOT)], check=False)
    print(f"Opened project root: {PROJECT_ROOT}")


def open_runtime(_: argparse.Namespace) -> None:
    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    run(["open", str(INSTALL_ROOT)], check=False)
    print(f"Opened Useful Agent runtime: {INSTALL_ROOT}")


def menu_install(_: argparse.Namespace) -> None:
    ensure_config()
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
    p.add_argument("--project-root")
    p.add_argument("--install-root")
    p.add_argument("--telegram-token")
    p.add_argument("--allow-user")
    p.set_defaults(func=install_guided)

    for name in ["check", "doctor"]:
        p = sub.add_parser(name)
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=check)

    configure = sub.add_parser("configure")
    configure_sub = configure.add_subparsers(dest="configure_cmd", required=True)
    p = configure_sub.add_parser("project")
    p.add_argument("--project-root")
    p.add_argument("--install-root")
    p.add_argument("--guided", action="store_true")
    p.set_defaults(func=configure_project_cmd)
    p = configure_sub.add_parser("telegram")
    p.add_argument("--guided", action="store_true")
    p.add_argument("--telegram-token")
    p.add_argument("--allow-user")
    p.set_defaults(func=configure_telegram)
    configure_sub.add_parser("websocket").set_defaults(func=configure_websocket)
    p = configure_sub.add_parser("adapters")
    p.add_argument("--target")
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
    sub.add_parser("open-project").set_defaults(func=open_project)
    sub.add_parser("open-runtime").set_defaults(func=open_runtime)
    sub.add_parser("open-telegram-setup").set_defaults(func=open_telegram)
    sub.add_parser("update").set_defaults(func=lambda _: run([find_uv() or "uv", "tool", "upgrade", "useful-agent"], check=False))
    sub.add_parser("uninstall").set_defaults(func=lambda _: print("Run docs/uninstall.md checklist; workspace/backups are never auto-deleted."))

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
