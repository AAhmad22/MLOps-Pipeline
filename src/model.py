"""Model architecture.

We use transfer learning on a ResNet-18 backbone: the convolutional layers
(pretrained on ImageNet) are frozen, and only a fresh classification head is
trained. This is fast to train, works well on small datasets, and keeps the
saved model small enough to ship inside a container image.
"""
from __future__ import annotations

import torch
import torch.nn as nn
from torchvision import models


def build_model(num_classes: int, pretrained: bool = True) -> nn.Module:
    """Build a ResNet-18 classifier with a custom head.

    Args:
        num_classes: number of output classes.
        pretrained: load ImageNet weights for the backbone.
    """
    weights = models.ResNet18_Weights.DEFAULT if pretrained else None
    model = models.resnet18(weights=weights)

    # Freeze the backbone so we only train the new head.
    for param in model.parameters():
        param.requires_grad = False

    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model


def load_model(model_path: str, num_classes: int, device: str = "cpu") -> nn.Module:
    """Load a trained model checkpoint for inference."""
    model = build_model(num_classes=num_classes, pretrained=False)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model
