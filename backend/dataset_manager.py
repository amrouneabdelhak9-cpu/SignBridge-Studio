"""
dataset/dataset_manager.py
===========================
Updated for MediaPipe Tasks API compatibility.

No structural change to dataset format,
only robustness + safety improvements.
"""

from __future__ import annotations

import json
import shutil
import dataclasses
from datetime import datetime
from pathlib import Path
from typing import Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class SignSample:
    sign_word: str
    description: str
    user_id: str
    recorded_at: str
    frame_count: int
    sequence: List[dict]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "SignSample":
        return SignSample(**d)


@dataclasses.dataclass
class DatasetStats:
    total_classes: int
    total_samples: int
    samples_per_class: Dict[str, int]
    class_names: List[str]
    last_updated: str


# ─────────────────────────────────────────────────────────────────────────────
# MANAGER
# ─────────────────────────────────────────────────────────────────────────────

class DatasetManager:

    DATASET_DIR = "dataset"
    INDEX_FILE = "_index.json"

    def __init__(self, root: str | Path = ".") -> None:
        self._root = Path(root) / self.DATASET_DIR
        self._root.mkdir(parents=True, exist_ok=True)
        self._ensure_index()

    # ─────────────────────────────────────────────────────────────────────────
    # SAVE SAMPLE
    # ─────────────────────────────────────────────────────────────────────────

    def add_new_sign(
        self,
        sign_word: str,
        sequence: List[dict],
        description: str = "",
        user_id: str = "default",
    ) -> Path:

        word = self._sanitize(sign_word)
        sign_dir = self._root / word
        sign_dir.mkdir(exist_ok=True)

        existing = sorted(sign_dir.glob("sample_*.json"))
        idx = len(existing) + 1

        sample_path = sign_dir / f"sample_{idx:03d}.json"

        sample = SignSample(
            sign_word=word,
            description=description,
            user_id=user_id,
            recorded_at=datetime.now().isoformat(timespec="seconds"),
            frame_count=len(sequence),
            sequence=sequence,
        )

        # ✔️ Safe JSON write (prevents corruption)
        with sample_path.open("w", encoding="utf-8") as f:
            json.dump(sample.to_dict(), f, ensure_ascii=False, indent=2)

        self._update_index(word)

        return sample_path

    # ─────────────────────────────────────────────────────────────────────────
    # LOAD DATASET
    # ─────────────────────────────────────────────────────────────────────────

    def load_dataset(self) -> Dict[str, List[SignSample]]:

        dataset: Dict[str, List[SignSample]] = {}

        for sign_dir in sorted(self._root.iterdir()):

            if not sign_dir.is_dir():
                continue

            if sign_dir.name.startswith("_"):
                continue

            samples: List[SignSample] = []

            for file in sorted(sign_dir.glob("sample_*.json")):

                try:
                    with file.open(encoding="utf-8") as f:
                        data = json.load(f)

                    # ✔️ validation safety (important for corrupted data)
                    if "sequence" not in data:
                        continue

                    samples.append(SignSample.from_dict(data))

                except Exception as e:
                    print(f"⚠️ corrupted sample skipped: {file} ({e})")

            if samples:
                dataset[sign_dir.name] = samples

        return dataset

    # ─────────────────────────────────────────────────────────────────────────
    # LOAD SINGLE SIGN
    # ─────────────────────────────────────────────────────────────────────────

    def load_sign(self, sign_word: str) -> List[SignSample]:

        word = self._sanitize(sign_word)
        sign_dir = self._root / word

        if not sign_dir.exists():
            return []

        return [
            SignSample.from_dict(json.load(f.open(encoding="utf-8")))
            for f in sorted(sign_dir.glob("sample_*.json"))
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # DELETE
    # ─────────────────────────────────────────────────────────────────────────

    def delete_sign(self, sign_word: str) -> bool:

        word = self._sanitize(sign_word)
        sign_dir = self._root / word

        if sign_dir.exists():
            shutil.rmtree(sign_dir)
            self._rebuild_index()
            return True

        return False

    def delete_sample(self, sign_word: str, index: int) -> bool:

        word = self._sanitize(sign_word)
        sign_dir = self._root / word

        target = sign_dir / f"sample_{index:03d}.json"

        if not target.exists():
            return False

        target.unlink()

        # renumber
        files = sorted(sign_dir.glob("sample_*.json"))

        for i, f in enumerate(files, 1):
            new_name = sign_dir / f"sample_{i:03d}.json"
            if f != new_name:
                f.rename(new_name)

        self._update_index(word)
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # EXPORT
    # ─────────────────────────────────────────────────────────────────────────

    def export_dataset(self, path: str | Path) -> Path:

        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)

        dataset = self.load_dataset()

        export = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "classes": sorted(dataset.keys()),
            "data": {
                k: [s.to_dict() for s in v]
                for k, v in dataset.items()
            },
        }

        with out.open("w", encoding="utf-8") as f:
            json.dump(export, f, ensure_ascii=False, indent=2)

        return out

    # ─────────────────────────────────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────────────────────────────────

    def get_stats(self) -> DatasetStats:

        index = self._load_index()
        spc = index.get("samples_per_class", {})

        return DatasetStats(
            total_classes=len(spc),
            total_samples=sum(spc.values()),
            samples_per_class=spc,
            class_names=sorted(spc.keys()),
            last_updated=index.get("last_updated", "—"),
        )

    def list_classes(self) -> List[str]:
        return self.get_stats().class_names

    def sample_count(self, sign_word: str) -> int:

        word = self._sanitize(sign_word)
        sign_dir = self._root / word

        if not sign_dir.exists():
            return 0

        return len(list(sign_dir.glob("sample_*.json")))

    # ─────────────────────────────────────────────────────────────────────────
    # INTERNALS
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _sanitize(word: str) -> str:
        return (
            word.strip()
            .lower()
            .replace(" ", "_")
            .replace("/", "-")
            .replace("\\", "-")
        )

    def _index_path(self) -> Path:
        return self._root / self.INDEX_FILE

    def _load_index(self) -> dict:

        try:
            if self._index_path().exists():
                with self._index_path().open(encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

        return {
            "samples_per_class": {},
            "last_updated": "—",
        }

    def _save_index(self, index: dict) -> None:

        with self._index_path().open("w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _ensure_index(self) -> None:
        if not self._index_path().exists():
            self._rebuild_index()

    def _rebuild_index(self) -> None:

        spc = {}

        for d in self._root.iterdir():
            if d.is_dir() and not d.name.startswith("_"):
                spc[d.name] = len(list(d.glob("sample_*.json")))

        self._save_index({
            "samples_per_class": spc,
            "last_updated": datetime.now().isoformat(timespec="seconds"),
        })

    def _update_index(self, word: str) -> None:

        index = self._load_index()
        spc = index.get("samples_per_class", {})

        spc[word] = len(list((self._root / word).glob("sample_*.json")))

        self._save_index({
            "samples_per_class": spc,
            "last_updated": datetime.now().isoformat(timespec="seconds"),
        })

    # ─────────────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"<DatasetManager root={self._root} "
            f"classes={stats.total_classes} "
            f"samples={stats.total_samples}>"
        )