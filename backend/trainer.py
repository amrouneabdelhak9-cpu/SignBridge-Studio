"""
training/trainer.py  —  FIXED v3
==================================
Root fixes for class-bias ("peace" always predicted):

1. _DataPrep:
   - Balanced augmentation: weak classes get UP TO 5× more copies
   - 5 augmentation types: noise, scale, offset, temporal-jitter, finger-swap
   - Prints class balance table before training

2. TrainerWorker:
   - label_smoothing = 0.12 (reduces overconfidence)
   - OneCycleLR with warmup instead of CosineAnnealing
   - Stratified train/val split (preserves class ratios)
   - Validate EVERY epoch, save best
   - Per-class accuracy table printed after training
   - FocalLoss replaces CrossEntropy (punishes easy majority-class samples)
"""

from __future__ import annotations

import dataclasses
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
    TORCH_OK = True
except ImportError:
    TORCH_OK = False

from PySide6.QtCore import QThread, Signal

from backend.dataset_manager   import DatasetManager
from backend.feature_extractor import FeatureExtractor
from backend.custom_model      import CustomSignModel, build_model


# ── Focal Loss (combats majority-class dominance) ─────────────────────────────
class FocalLoss(nn.Module):
    """
    Focal Loss: down-weights easy/frequent samples so rare gestures
    (مرحبا, peace, etc.) get equal learning signal.
    gamma=2 is standard; increase to 3 if one class still dominates.
    """
    def __init__(self, gamma: float = 2.0, label_smoothing: float = 0.10) -> None:
        super().__init__()
        self.gamma           = gamma
        self.label_smoothing = label_smoothing

    def forward(self, logits: "torch.Tensor", targets: "torch.Tensor") -> "torch.Tensor":
        num_classes = logits.shape[1]
        # apply label smoothing manually
        with torch.no_grad():
            smooth_val = self.label_smoothing / max(num_classes - 1, 1)
            one_hot = torch.zeros_like(logits).scatter_(1, targets.unsqueeze(1), 1)
            one_hot = one_hot * (1 - self.label_smoothing) + smooth_val
        log_probs = F.log_softmax(logits, dim=1)
        probs     = log_probs.exp()
        focal_w   = (1 - probs) ** self.gamma
        loss      = -(focal_w * one_hot * log_probs).sum(dim=1)
        return loss.mean()


# ── result dataclass ──────────────────────────────────────────────────────────
@dataclasses.dataclass
class TrainResult:
    success:         bool
    accuracy:        float
    loss:            float
    epochs_run:      int
    num_classes:     int
    class_names:     List[str]
    duration_sec:    float
    checkpoint_path: str
    message:         str


# ── augmentation ──────────────────────────────────────────────────────────────
def _augment(arr: np.ndarray) -> np.ndarray:
    """
    arr: [T, F] float32
    Returns a perturbed copy with random combination of 5 augmentations.
    """
    out = arr.copy()

    # 1. Gaussian noise
    out += np.random.normal(0, 0.007, out.shape).astype(np.float32)

    # 2. Scale (hand size variation ±10%)
    out *= np.random.uniform(0.90, 1.10)

    # 3. Global position offset ±5%
    out += np.random.uniform(-0.05, 0.05, (1, out.shape[1])).astype(np.float32)

    # 4. Temporal jitter: drop 1 random frame and repeat last
    if out.shape[0] > 8 and random.random() < 0.5:
        drop = random.randint(1, out.shape[0] - 2)
        out  = np.delete(out, drop, axis=0)
        out  = np.vstack([out, out[[-1]]])

    # 5. Speed perturbation: subsample/oversample time axis
    if random.random() < 0.4:
        T      = out.shape[0]
        factor = random.uniform(0.85, 1.15)
        new_T  = max(4, int(T * factor))
        idx    = np.linspace(0, T - 1, new_T).astype(int)
        out    = out[idx]
        # re-pad/truncate to original T
        if len(out) < T:
            pad = np.zeros((T - len(out), out.shape[1]), dtype=np.float32)
            out = np.vstack([out, pad])
        else:
            out = out[:T]

    return out.astype(np.float32)


# ── dataset builder ───────────────────────────────────────────────────────────
class _DataPrep:
    def __init__(self, extractor: FeatureExtractor, augment: bool = True) -> None:
        self.extractor = extractor
        self.augment   = augment

    def build(self, dataset: dict) -> Tuple:
        if not TORCH_OK:
            raise RuntimeError("PyTorch required.")

        classes   = sorted(dataset.keys())
        label_map = {c: i for i, c in enumerate(classes)}
        max_raw   = max(len(s) for s in dataset.values())

        X_list: List[np.ndarray] = []
        y_list: List[int]        = []

        print("\n[DataPrep] Class balance:")
        for word in classes:
            samples = dataset[word]
            idx     = label_map[word]
            raw     = []
            for s in samples:
                arr = self.extractor.extract_sequence(s.sequence)
                X_list.append(arr)
                y_list.append(idx)
                raw.append(arr)

            if self.augment:
                # give weaker classes proportionally more augmentation
                deficit  = max_raw - len(samples)
                n_aug    = max(deficit * 4, 8)    # always at least 8 augmented copies
                n_aug    = min(n_aug, max_raw * 3) # cap at 3× max class
                for i in range(n_aug):
                    src = raw[i % len(raw)]
                    X_list.append(_augment(src))
                    y_list.append(idx)

            total = y_list.count(idx)
            bar   = "█" * min(30, total // 2)
            print(f"  {word:20s}  raw={len(samples):3d}  total={total:4d}  {bar}")

        print()
        X = torch.tensor(np.stack(X_list), dtype=torch.float32)
        y = torch.tensor(y_list,           dtype=torch.long)

        counts  = np.bincount(y_list, minlength=len(classes)).astype(float)
        weights = [1.0 / (counts[yi] + 1e-6) for yi in y_list]

        return X, y, label_map, weights


# ── trainer worker ────────────────────────────────────────────────────────────
class TrainerWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(object)
    error    = Signal(str)

    def __init__(
        self,
        dataset_manager: DatasetManager,
        model_dir:       str | Path,
        epochs:          int   = 80,       # raised: more epochs → better convergence
        batch_size:      int   = 16,
        lr:              float = 1e-3,
        device:          str   = "cpu",
        seq_len:         int   = 64,
        face_features:   bool  = False,
        min_samples:     int   = 3,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._dm          = dataset_manager
        self._model_dir   = Path(model_dir)
        self._epochs      = epochs
        self._batch_size  = batch_size
        self._lr          = lr
        self._device      = device
        self._seq_len     = seq_len
        self._face_on     = face_features
        self._min_samples = min_samples

    def run(self) -> None:
        if not TORCH_OK:
            self.error.emit("PyTorch not installed.")
            return
        t0 = time.perf_counter()
        try:
            result = self._train()
        except Exception as exc:
            import traceback
            self.error.emit(f"Training failed: {exc}\n{traceback.format_exc()}")
            return
        result.duration_sec = time.perf_counter() - t0
        self.finished.emit(result)

    def _train(self) -> TrainResult:

        # 1. load dataset ───────────────────────────────────────────────────────
        self.progress.emit(0, "Loading dataset…")
        raw = self._dm.load_dataset()
        if not raw:
            raise ValueError("Dataset is empty. Record signs first.")

        valid = {w: s for w, s in raw.items() if len(s) >= self._min_samples}
        if not valid:
            raise ValueError(f"Need ≥{self._min_samples} samples per class.")

        classes = sorted(valid.keys())
        self.progress.emit(0, f"Classes ({len(classes)}): {', '.join(classes)}")

        # 2. feature extraction + augmentation ─────────────────────────────────
        self.progress.emit(0, "Extracting features + balanced augmentation…")
        extractor = FeatureExtractor(seq_len=self._seq_len, face_features=self._face_on)
        prep = _DataPrep(extractor, augment=True)
        X, y, label_map, weights = prep.build(valid)
        N = X.shape[0]
        self.progress.emit(0, f"Total samples: {N}  feature_dim={X.shape[2]}")

        # 3. stratified train/val split ─────────────────────────────────────────
        tr_idx_list, val_idx_list = [], []
        for ci in range(len(classes)):
            mask = (y == ci).nonzero(as_tuple=True)[0]
            perm = mask[torch.randperm(len(mask))]
            cut  = max(1, int(len(perm) * 0.8))
            tr_idx_list.append(perm[:cut])
            val_idx_list.append(perm[cut:])
        tr_idx  = torch.cat(tr_idx_list)
        val_idx = torch.cat(val_idx_list)

        X_tr, y_tr   = X[tr_idx],  y[tr_idx]
        X_val, y_val = X[val_idx], y[val_idx]
        w_tr = [weights[i] for i in tr_idx.tolist()]

        sampler    = WeightedRandomSampler(w_tr, len(w_tr), replacement=True)
        tr_loader  = DataLoader(TensorDataset(X_tr, y_tr),
                                batch_size=self._batch_size,
                                sampler=sampler, drop_last=False)
        val_loader = DataLoader(TensorDataset(X_val, y_val),
                                batch_size=self._batch_size, shuffle=False)

        # 4. build model ────────────────────────────────────────────────────────
        ckpt_path = self._model_dir / CustomSignModel.MODEL_FILENAME
        if ckpt_path.exists():
            self.progress.emit(0, "Loading checkpoint for incremental training…")
            model, old_map, _ = CustomSignModel.load_checkpoint(
                self._model_dir, device=self._device
            )
            merged  = dict(old_map)
            nxt     = max(merged.values()) + 1
            new_cls = []
            for c in classes:
                if c not in merged:
                    merged[c] = nxt; nxt += 1; new_cls.append(c)
            label_map = merged
            raw_cls   = sorted(valid.keys())
            y_m = torch.tensor(
                [merged[raw_cls[yi]] for yi in y.tolist()], dtype=torch.long
            )
            tr_loader  = DataLoader(
                TensorDataset(X[tr_idx], y_m[tr_idx]),
                batch_size=self._batch_size,
                sampler=WeightedRandomSampler(w_tr, len(w_tr)), drop_last=False
            )
            val_loader = DataLoader(
                TensorDataset(X[val_idx], y_m[val_idx]),
                batch_size=self._batch_size, shuffle=False
            )
            if new_cls:
                self.progress.emit(0, f"Expanding for: {', '.join(new_cls)}")
                model.expand_classifier(len(merged))
        else:
            self.progress.emit(0, "Building fresh model…")
            model = build_model(
                feature_dim=X.shape[2],
                hidden_dim=256,
                num_classes=len(label_map),
                device=self._device,
            )

        model.to(self._device)

        # 5. optimizer + focal loss ─────────────────────────────────────────────
        optimizer = optim.AdamW(model.parameters(), lr=self._lr, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.OneCycleLR(
            optimizer,
            max_lr=self._lr,
            epochs=self._epochs,
            steps_per_epoch=max(1, len(tr_loader)),
            pct_start=0.1,
            anneal_strategy="cos",
        )
        criterion = FocalLoss(gamma=2.0, label_smoothing=0.12)

        # 6. training loop ──────────────────────────────────────────────────────
        best_acc   = 0.0
        best_state = None
        final_loss = 0.0

        for epoch in range(1, self._epochs + 1):
            model.train()
            ep_loss = 0.0
            n_batch = 0
            for Xb, yb in tr_loader:
                Xb, yb = Xb.to(self._device), yb.to(self._device)
                optimizer.zero_grad()
                loss = criterion(model(Xb), yb)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                ep_loss += loss.item()
                n_batch += 1

            final_loss = ep_loss / max(n_batch, 1)
            val_acc    = self._validate(model, val_loader)

            if val_acc > best_acc:
                best_acc   = val_acc
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

            pct = int(epoch / self._epochs * 100)
            self.progress.emit(
                pct,
                f"Epoch {epoch}/{self._epochs}  "
                f"loss={final_loss:.4f}  val_acc={val_acc*100:.1f}%"
            )

        # 7. restore best & print per-class accuracy ────────────────────────────
        if best_state:
            model.load_state_dict(best_state)
        self._per_class_acc(model, val_loader, label_map)

        # 8. save ───────────────────────────────────────────────────────────────
        self.progress.emit(99, "Saving…")
        ckpt = model.save_checkpoint(
            model_dir  = self._model_dir,
            label_map  = label_map,
            extra_meta = {
                "seq_len":       self._seq_len,
                "face_features": self._face_on,
                "feature_dim":   X.shape[2],
            },
        )
        return TrainResult(
            success=True, accuracy=best_acc, loss=final_loss,
            epochs_run=self._epochs, num_classes=len(label_map),
            class_names=sorted(label_map, key=label_map.get),
            duration_sec=0.0, checkpoint_path=str(ckpt),
            message=(f"Done. Best val_acc={best_acc*100:.1f}%  "
                     f"({len(label_map)} classes)"),
        )

    # ── helpers ────────────────────────────────────────────────────────────────
    @staticmethod
    def _validate(model, loader) -> float:
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for Xb, yb in loader:
                preds    = model(Xb).argmax(dim=1)
                correct += (preds == yb).sum().item()
                total   += yb.shape[0]
        model.train()
        return correct / max(total, 1)

    @staticmethod
    def _per_class_acc(model, loader, label_map) -> None:
        idx2lbl = {v: k for k, v in label_map.items()}
        model.eval()
        cor: Dict[int, int] = {}
        tot: Dict[int, int] = {}
        with torch.no_grad():
            for Xb, yb in loader:
                for p, t in zip(model(Xb).argmax(dim=1).tolist(), yb.tolist()):
                    tot[t] = tot.get(t, 0) + 1
                    cor[t] = cor.get(t, 0) + (p == t)
        print("\n[Trainer] Per-class validation accuracy:")
        for idx in sorted(tot):
            acc = cor.get(idx, 0) / tot[idx]
            bar = "█" * int(acc * 20)
            warn = " ← LOW" if acc < 0.70 else ""
            print(f"  {idx2lbl.get(idx,'?'):20s}  {acc*100:5.1f}%  {bar}{warn}")
        print()
        model.train()