#!/usr/bin/env python3
"""Patch Nanobot image generation tool to support Codex CLI subscription images."""

from __future__ import annotations

import os
from pathlib import Path


TARGET = Path(os.environ.get(
    "NANOBOT_IMAGE_GEN_PATCH_TARGET",
    "/usr/local/lib/python3.11/site-packages/nanobot/agent/tools/image_generation.py",
))


CODEX_CLIENT = r'''

class _CodexCLIImageGenerationClient:
    """Generate images through Codex CLI's built-in imagegen tool.

    This uses the user's Codex subscription/OAuth session, not OpenAI API billing.
    The CLI writes PNGs under CODEX_HOME/generated_images; we detect the new file,
    convert it to a data URL, and let Nanobot persist/send it via its normal media
    pipeline.
    """

    def __init__(self) -> None:
        self.command = os.environ.get("NANOBOT_CODEX_CLI", "codex")
        self.timeout = float(os.environ.get("NANOBOT_CODEX_IMAGEGEN_TIMEOUT", "900"))
        self.codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()

    async def generate(
        self,
        *,
        prompt: str,
        model: str,
        reference_images: list[str] | None = None,
        aspect_ratio: str | None = None,
        image_size: str | None = None,
    ):
        before = self._known_pngs()
        generated_prompt = self._build_prompt(
            prompt=prompt,
            model=model,
            reference_images=reference_images or [],
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )
        cmd = [
            self.command,
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-rules",
            "--cd",
            os.environ.get("NANOBOT_CODEX_IMAGEGEN_WORKDIR", "/workspace/Money"),
            "--sandbox",
            "read-only",
            "-c",
            'approval_policy="never"',
        ]
        for image_path in reference_images or []:
            cmd.extend(["--image", image_path])
        cmd.append(generated_prompt)

        try:
            proc = subprocess.run(
                cmd,
                cwd=os.environ.get("NANOBOT_CODEX_IMAGEGEN_WORKDIR", "/workspace/Money"),
                env=os.environ.copy(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ImageGenerationError(f"Codex CLI not found: {self.command}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ImageGenerationError(f"Codex CLI image generation timed out after {int(self.timeout)}s") from exc

        if proc.returncode != 0:
            detail = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip()[:1200]
            raise ImageGenerationError(f"Codex CLI image generation failed: {detail or 'no output'}")

        new_pngs = [p for p in self._known_pngs() if p not in before]
        if not new_pngs:
            detail = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()[:1200]
            raise ImageGenerationError(f"Codex CLI returned no generated PNG. Output: {detail or 'empty'}")
        newest = max(new_pngs, key=lambda p: p.stat().st_mtime)
        raw = newest.read_bytes()
        encoded = base64.b64encode(raw).decode("ascii")
        return _CodexCLIImageGenerationResponse(
            images=[f"data:image/png;base64,{encoded}"],
            content=str(newest),
            raw={"path": str(newest), "stdout": proc.stdout[-2000:] if proc.stdout else ""},
        )

    def _known_pngs(self) -> set[Path]:
        root = self.codex_home / "generated_images"
        if not root.exists():
            return set()
        return {p.resolve() for p in root.rglob("*.png") if p.is_file()}

    @staticmethod
    def _build_prompt(
        *,
        prompt: str,
        model: str,
        reference_images: list[str],
        aspect_ratio: str | None,
        image_size: str | None,
    ) -> str:
        constraints = []
        if aspect_ratio:
            constraints.append(f"Aspect ratio: {aspect_ratio}.")
        if image_size:
            constraints.append(f"Size/detail hint: {image_size}.")
        if model:
            constraints.append(f"Use the default Codex image generation model unless unavailable; requested Nanobot model label: {model}.")
        if reference_images:
            constraints.append("Use the attached reference image(s) only as visual references if relevant.")
        constraint_text = "\n".join(constraints)
        return (
            "$imagegen\n"
            "Generate exactly one image from this prompt. Do not ask follow-up questions. "
            "After generation, reply with only a short confirmation.\n\n"
            f"{constraint_text}\n\n"
            f"Prompt:\n{prompt}"
        )


class _CodexCLIImageGenerationResponse:
    def __init__(self, *, images: list[str], content: str, raw: dict[str, Any]) -> None:
        self.images = images
        self.content = content
        self.raw = raw
'''


def patch() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if "_CodexCLIImageGenerationClient" in text:
        return

    text = text.replace(
        "from pathlib import Path\n",
        "import base64\nimport os\nimport subprocess\nfrom pathlib import Path\n",
        1,
    )
    text = text.replace(
        'if TYPE_CHECKING:\n    from nanobot.config.schema import ProviderConfig\n',
        'if TYPE_CHECKING:\n    from nanobot.config.schema import ProviderConfig\n' + CODEX_CLIENT,
        1,
    )
    text = text.replace(
        "    def _provider_client(self) -> OpenRouterImageGenerationClient | AIHubMixImageGenerationClient | None:\n",
        "    def _provider_client(self) -> OpenRouterImageGenerationClient | AIHubMixImageGenerationClient | _CodexCLIImageGenerationClient | None:\n",
        1,
    )
    text = text.replace(
        '        if self.config.provider == "aihubmix":\n            return AIHubMixImageGenerationClient(**kwargs)\n        return None\n',
        '        if self.config.provider == "aihubmix":\n            return AIHubMixImageGenerationClient(**kwargs)\n        if self.config.provider == "codex_cli":\n            return _CodexCLIImageGenerationClient()\n        return None\n',
        1,
    )
    text = text.replace(
        "        provider = self._provider_config()\n        if not provider or not provider.api_key:\n            return self._missing_api_key_error()\n",
        "        provider = self._provider_config()\n        if self.config.provider != \"codex_cli\" and (not provider or not provider.api_key):\n            return self._missing_api_key_error()\n",
        1,
    )
    TARGET.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch()
