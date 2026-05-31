"""Tests for the model architecture."""
import torch

from src.model import build_model


def test_build_model_output_shape():
    model = build_model(num_classes=3, pretrained=False)
    model.eval()
    dummy = torch.randn(2, 3, 224, 224)  # batch of 2 RGB images
    with torch.no_grad():
        out = model(dummy)
    assert out.shape == (2, 3)


def test_backbone_is_frozen():
    model = build_model(num_classes=2, pretrained=False)
    trainable = [name for name, p in model.named_parameters() if p.requires_grad]
    # Only the final fully-connected head should be trainable.
    assert all(name.startswith("fc.") for name in trainable)
    assert trainable, "Expected the classification head to be trainable"
