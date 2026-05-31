"""Inference logic: turn raw image bytes into class predictions."""
from __future__ import annotations

import io
from functools import lru_cache

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from src.config import settings
from src.model import load_model


def _build_transform(image_size: int) -> transforms.Compose:
    # Same normalisation ResNet was pretrained with on ImageNet.
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )


@lru_cache(maxsize=1)
def _get_model():
    """Load the model once and cache it (cold start happens on first request)."""
    return load_model(
        model_path=settings.model_path,
        num_classes=settings.num_classes,
        device=settings.device,
    )


def predict(image_bytes: bytes) -> dict:
    """Run inference on a single image.

    Returns a dict with the top label, its confidence, and the full
    probability distribution over classes.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    transform = _build_transform(settings.image_size)
    tensor = transform(image).unsqueeze(0).to(settings.device)

    model = _get_model()
    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=1).squeeze(0)

    top_idx = int(torch.argmax(probs).item())
    return {
        "label": settings.class_names[top_idx],
        "confidence": round(float(probs[top_idx]), 4),
        "probabilities": {
            name: round(float(probs[i]), 4)
            for i, name in enumerate(settings.class_names)
        },
    }
