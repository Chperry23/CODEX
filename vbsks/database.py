from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import Dict

import numpy as np


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


@dataclass
class VectorDatabase:
    """Simple vector database storing noise and key vectors."""

    folder: str
    dimensions: int = 100
    db_size: int = 10000

    def __post_init__(self) -> None:
        _ensure_dir(self.folder)
        self.vectors_path = os.path.join(self.folder, "vectors.npy")
        self.meta_path = os.path.join(self.folder, "meta.json")
        if not os.path.exists(self.vectors_path):
            self._init_db()
        self._load_meta()

    def _init_db(self) -> None:
        noise = np.random.normal(size=(self.db_size, self.dimensions))
        np.save(self.vectors_path, noise)
        with open(self.meta_path, "w") as f:
            json.dump({}, f)

    def _load_meta(self) -> None:
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r") as f:
                self.meta: Dict[str, int] = json.load(f)
        else:
            self.meta = {}

    def save_meta(self) -> None:
        with open(self.meta_path, "w") as f:
            json.dump(self.meta, f)

    def load_vectors(self) -> np.ndarray:
        return np.load(self.vectors_path)

    def save_vectors(self, arr: np.ndarray) -> None:
        np.save(self.vectors_path, arr)
