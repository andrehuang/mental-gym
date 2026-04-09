"""Configuration loading and validation."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class LLMConfig:
    backend: str = "claude-cli"  # "anthropic-api" | "claude-cli" | "codex-cli"
    model: str = "claude-sonnet-4-6"  # model hint for API backend

    VALID_BACKENDS = ("anthropic-api", "claude-cli", "codex-cli")

    def validate(self):
        if self.backend not in self.VALID_BACKENDS:
            raise ValueError(
                f"Invalid LLM backend '{self.backend}'. "
                f"Must be one of: {', '.join(self.VALID_BACKENDS)}"
            )
        if self.backend == "anthropic-api" and not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable required for anthropic-api backend"
            )


@dataclass
class MentalGymConfig:
    domain: str = ""
    knowledge_base: Optional[str] = None  # path to KB directory
    llm: LLMConfig = field(default_factory=LLMConfig)
    session_duration: int = 25  # minutes
    db_path: str = "data/mental_gym.db"

    # Resolved paths (set after loading)
    config_dir: str = ""  # directory containing the config file

    def resolve_paths(self):
        """Resolve relative paths against config directory."""
        if self.knowledge_base:
            kb = Path(self.config_dir) / self.knowledge_base
            self.knowledge_base = str(kb.resolve())
        db = Path(self.config_dir) / self.db_path
        self.db_path = str(db.resolve())


def load_config(config_path: str = "mental_gym.yaml") -> MentalGymConfig:
    """Load config from YAML file."""
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            "Run 'mental-gym init' to create one."
        )

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    llm_raw = raw.get("llm", {})
    llm = LLMConfig(
        backend=llm_raw.get("backend", LLMConfig.backend),
        model=llm_raw.get("model", LLMConfig.model),
    )

    config = MentalGymConfig(
        domain=raw.get("domain", ""),
        knowledge_base=raw.get("knowledge_base"),
        llm=llm,
        session_duration=raw.get("session_duration", 25),
        db_path=raw.get("db_path", "data/mental_gym.db"),
        config_dir=str(path.parent),
    )
    config.resolve_paths()
    return config


def write_config(config: MentalGymConfig, config_path: str = "mental_gym.yaml"):
    """Write config to YAML file."""
    data = {
        "domain": config.domain,
        "llm": {
            "backend": config.llm.backend,
            "model": config.llm.model,
        },
        "session_duration": config.session_duration,
        "db_path": "data/mental_gym.db",
    }
    if config.knowledge_base:
        # Store as relative path from config dir
        try:
            rel = os.path.relpath(config.knowledge_base, config.config_dir)
            data["knowledge_base"] = rel
        except ValueError:
            data["knowledge_base"] = config.knowledge_base

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
