"""Train the image classifier.

Expects data laid out for torchvision.datasets.ImageFolder:

    data/
      train/
        cat/ *.jpg
        dog/ *.jpg
      val/
        cat/ *.jpg
        dog/ *.jpg

Usage:
    python -m src.train --data-dir data --epochs 5 --out artifacts/model.pt
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from src.model import build_model


def build_loaders(data_dir: str, image_size: int, batch_size: int):
    train_tf = transforms.Compose(
        [
            transforms.RandomResizedCrop(image_size),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    val_tf = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    train_ds = datasets.ImageFolder(Path(data_dir) / "train", transform=train_tf)
    val_ds = datasets.ImageFolder(Path(data_dir) / "val", transform=val_tf)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    return train_loader, val_loader, train_ds.classes


@torch.no_grad()
def evaluate(model, loader, device) -> float:
    model.eval()
    correct = total = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        preds = model(images).argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
    return correct / total if total else 0.0


def train(args: argparse.Namespace) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    train_loader, val_loader, classes = build_loaders(
        args.data_dir, args.image_size, args.batch_size
    )
    print(f"Classes: {classes}")

    model = build_model(num_classes=len(classes)).to(device)
    criterion = nn.CrossEntropyLoss()
    # Only the new head has requires_grad=True, so only it gets optimised.
    optimizer = torch.optim.Adam(
        (p for p in model.parameters() if p.requires_grad), lr=args.lr
    )

    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            running += loss.item()
        acc = evaluate(model, val_loader, device)
        print(f"Epoch {epoch}/{args.epochs}  loss={running:.3f}  val_acc={acc:.3f}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), args.out)
    print(f"Saved model to {args.out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the image classifier.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--out", default="artifacts/model.pt")
    train(parser.parse_args())


if __name__ == "__main__":
    main()
