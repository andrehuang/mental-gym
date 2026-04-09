"""LLM backend protocol and implementations."""

import json
import os
import subprocess
import time
from typing import Optional, Protocol


class LLMBackend(Protocol):
    """Protocol for LLM backends."""

    def complete(self, system_prompt: str, user_prompt: str,
                 json_mode: bool = False) -> str:
        """Send a prompt and return the response text."""
        ...


class AnthropicAPIBackend:
    """Direct Anthropic SDK calls. Requires ANTHROPIC_API_KEY."""

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package required for API backend. "
                    "Install with: pip install mental-gym[api]"
                )
            self._client = anthropic.Anthropic()
        return self._client

    def complete(self, system_prompt: str, user_prompt: str,
                 json_mode: bool = False) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    max_tokens=4096,
                )
                return response.content[0].text
            except Exception as e:
                err_str = str(e)
                # Don't retry on client errors (auth, billing, bad request)
                is_client_error = any(
                    code in err_str for code in ("400", "401", "403", "404")
                )
                if is_client_error or attempt >= max_retries - 1:
                    raise RuntimeError(f"Anthropic API error: {e}")
                wait = 2 ** (attempt + 1)
                time.sleep(wait)


class ClaudeCliBackend:
    """Route calls through the `claude` CLI (uses OAuth / Max subscription)."""

    def __init__(self, model: Optional[str] = None):
        self.model = model

    def complete(self, system_prompt: str, user_prompt: str,
                 json_mode: bool = False) -> str:
        cmd = ["claude", "-p", user_prompt, "--system-prompt", system_prompt]
        if self.model:
            cmd.extend(["--model", self.model])

        # Clear ANTHROPIC_API_KEY so claude CLI uses OAuth (Max subscription)
        # instead of falling back to API credits
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, env=env,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                raise RuntimeError(f"claude CLI error: {stderr}")
            return result.stdout.strip()
        except FileNotFoundError:
            raise RuntimeError(
                "claude CLI not found. Install Claude Code or use a different backend."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("claude CLI timed out after 300 seconds")


class CodexCliBackend:
    """Route calls through the `codex` CLI."""

    def __init__(self, model: Optional[str] = None):
        self.model = model

    def complete(self, system_prompt: str, user_prompt: str,
                 json_mode: bool = False) -> str:
        # Combine system + user prompt for codex (which may not have separate system prompt)
        combined = f"{system_prompt}\n\n---\n\n{user_prompt}"
        cmd = ["codex", "--quiet", "--full-auto", combined]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                raise RuntimeError(f"codex CLI error: {stderr}")
            return result.stdout.strip()
        except FileNotFoundError:
            raise RuntimeError(
                "codex CLI not found. Install Codex or use a different backend."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("codex CLI timed out after 120 seconds")


def create_backend(backend_name: str, model: Optional[str] = None) -> LLMBackend:
    """Factory function to create the appropriate backend."""
    if backend_name == "anthropic-api":
        return AnthropicAPIBackend(model=model or "claude-sonnet-4-6")
    elif backend_name == "claude-cli":
        return ClaudeCliBackend(model=model)
    elif backend_name == "codex-cli":
        return CodexCliBackend(model=model)
    else:
        raise ValueError(f"Unknown backend: {backend_name}")
