"""
training/custom_model.py
=========================
Lightweight LSTM → GRU hybrid model for custom sign classification.

Architecture
------------
  Input  [batch, T, F]
    │
    ├── Projection  Linear(F → hidden_dim)  + LayerNorm  + Dropout
    │
    ├── Bidirectional GRU  (num_layers=2, dropout=0.3)
    │
    ├── Attention pool  (soft-attention over time steps)
    │
    └── Classifier  Linear(hidden_dim*2 → num_classes)

Incremental Learning Strategy
------------------------------
When a new class is added:
  1. The existing classifier weights are FROZEN temporarily.
  2. The output layer is expanded by one neuron (the new class).
  3. Fine-tuning runs for a few epochs on ALL data to prevent forgetting.

This avoids a full retrain from scratch while keeping old accuracy.

Serialisation
-------------
  save_checkpoint()  →  model_dir/custom_signs.pt
  load_checkpoint()  ←  model_dir/custom_signs.pt
  The checkpoint includes the label→index mapping and model config.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# ── Soft-attention pooling ────────────────────────────────────────────────────
class _AttentionPool(nn.Module):
    """Compute a weighted mean over the time dimension."""

    def __init__(self, dim: int) -> None:
        super().__init__()
        self.attn = nn.Linear(dim, 1, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T, D]
        weights = F.softmax(self.attn(x), dim=1)   # [B, T, 1]
        pooled  = (x * weights).sum(dim=1)          # [B, D]
        return pooled


# ── Main model ────────────────────────────────────────────────────────────────
class CustomSignModel(nn.Module):
    """
    Bidirectional GRU sequence classifier for custom sign recognition.

    Parameters
    ----------
    feature_dim  : input feature size per time step
    hidden_dim   : GRU hidden units (each direction)
    num_layers   : number of stacked GRU layers
    num_classes  : initial number of output classes
    dropout      : dropout probability
    """

    MODEL_FILENAME = "custom_signs.pt"

    def __init__(
        self,
        feature_dim: int  = 130,
        hidden_dim:  int  = 256,
        num_layers:  int  = 2,
        num_classes: int  = 1,
        dropout:     float= 0.3,
    ) -> None:
        super().__init__()

        self.feature_dim = feature_dim
        self.hidden_dim  = hidden_dim
        self.num_layers  = num_layers
        self.dropout_p   = dropout

        # Input projection
        self.proj = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # Bidirectional GRU
        self.gru = nn.GRU(
            input_size    = hidden_dim,
            hidden_size   = hidden_dim,
            num_layers    = num_layers,
            batch_first   = True,
            dropout       = dropout if num_layers > 1 else 0.0,
            bidirectional = True,
        )

        # Attention pooling over time axis
        self.pool = _AttentionPool(hidden_dim * 2)

        # Classifier head
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(hidden_dim, num_classes),
        )

    @property
    def num_classes(self) -> int:
        """Current number of output classes (reads from the last Linear layer)."""
        return self.head[-1].out_features

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Parameters
        ----------
        x : [B, T, feature_dim]

        Returns
        -------
        logits : [B, num_classes]
        """
        h = self.proj(x)                        # [B, T, D]
        h, _ = self.gru(h)                      # [B, T, D*2]
        h = self.pool(h)                        # [B, D*2]
        return self.head(h)                     # [B, C]

    # ── incremental expansion ─────────────────────────────────────────────────

    def expand_classifier(self, new_num_classes: int) -> None:
        """
        Expand the final Linear layer from current num_classes to
        new_num_classes, preserving old weights.

        Only the NEWLY ADDED neuron rows are randomly initialised;
        existing rows are copied verbatim (no forgetting).
        """
        old_c = self.num_classes
        if new_num_classes <= old_c:
            return  # nothing to do

        old_linear = self.head[-1]              # nn.Linear(D, old_c)
        new_linear = nn.Linear(
            old_linear.in_features, new_num_classes, bias=True
        )

        with torch.no_grad():
            # Copy old weights and biases
            new_linear.weight[:old_c] = old_linear.weight
            new_linear.bias[:old_c]   = old_linear.bias

            # Initialise new neurons with small random values
            nn.init.xavier_uniform_(new_linear.weight[old_c:])
            nn.init.zeros_(new_linear.bias[old_c:])

        # Replace the last module in self.head
        head_modules = list(self.head.children())
        head_modules[-1] = new_linear
        self.head = nn.Sequential(*head_modules)

    # ── serialisation ─────────────────────────────────────────────────────────

    def save_checkpoint(
        self,
        model_dir:   str | Path,
        label_map:   Dict[str, int],
        extra_meta:  Optional[dict] = None,
    ) -> Path:
        """
        Save model weights + config + label→index map to disk.

        Returns the path of the saved .pt file.
        """
        path = Path(model_dir) / self.MODEL_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "config": {
                "feature_dim": self.feature_dim,
                "hidden_dim":  self.hidden_dim,
                "num_layers":  self.num_layers,
                "num_classes": self.num_classes,
                "dropout":     self.dropout_p,
            },
            "state_dict": self.state_dict(),
            "label_map":  label_map,
            "meta":        extra_meta or {},
        }
        torch.save(payload, path)
        return path

    @classmethod
    def load_checkpoint(
        cls,
        model_dir:  str | Path,
        device:     str = "cpu",
    ) -> tuple["CustomSignModel", Dict[str, int], dict]:
        """
        Load model from checkpoint.

        Returns
        -------
        (model, label_map, meta)
        """
        path = Path(model_dir) / cls.MODEL_FILENAME
        if not path.exists():
            raise FileNotFoundError(f"No checkpoint found at {path}")

        payload = torch.load(path, map_location=device, weights_only=False)
        cfg     = payload["config"]
        model   = cls(**cfg)
        model.load_state_dict(payload["state_dict"])
        model.to(device)
        model.eval()
        return model, payload["label_map"], payload.get("meta", {})


# ── factory helper ────────────────────────────────────────────────────────────
def build_model(
    feature_dim: int = 130,
    hidden_dim:  int = 256,
    num_classes: int = 1,
    device:      str = "cpu",
) -> CustomSignModel:
    """Construct and return a fresh model on the given device."""
    model = CustomSignModel(
        feature_dim = feature_dim,
        hidden_dim  = hidden_dim,
        num_classes = num_classes,
    )
    return model.to(device)
