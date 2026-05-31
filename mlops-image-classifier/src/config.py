"""Application configuration.

All settings are read from environment variables so the same image can be
configured differently per environment (local, staging, prod) without code
changes. This is a core 12-factor / deployment principle.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _class_names() -> list[str]:
    raw = os.getenv("CLASS_NAMES", "cat,dog")
    return [name.strip() for name in raw.split(",") if name.strip()]


@dataclass
class Settings:
    model_path: str = field(default_factory=lambda: os.getenv("MODEL_PATH", "artifacts/model.pt"))
    class_names: list[str] = field(default_factory=_class_names)
    device: str = field(default_factory=lambda: os.getenv("DEVICE", "cpu"))
    image_size: int = field(default_factory=lambda: int(os.getenv("IMAGE_SIZE", "224")))
    max_upload_mb: int = field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_MB", "10")))

    @property
    def num_classes(self) -> int:
        return len(self.class_names)


settings = Settings()
