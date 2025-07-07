from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from cryptography.fernet import Fernet
import numpy as np
import hashlib
import base64
import json

from .database import VectorDatabase
from .map_manager import MapManager


def _random_vector(dim: int) -> np.ndarray:
    return np.random.normal(size=(dim,))


def _derive_data_key(password: str) -> bytes:
    digest = hashlib.sha256(("data" + password).encode()).digest()
    return base64.urlsafe_b64encode(digest)


@dataclass
class KeyManager:
    folder: str
    master_password: str
    dimensions: int = 100
    db_size: int = 10000

    def __post_init__(self) -> None:
        self.db = VectorDatabase(self.folder, self.dimensions, self.db_size)
        self.map = MapManager(self.folder, self.master_password)
        self.data_path = os.path.join(self.folder, "data.enc")
        self.data_fernet = Fernet(_derive_data_key(self.master_password))
        if not os.path.exists(self.data_path):
            with open(self.data_path, "wb") as f:
                f.write(self.data_fernet.encrypt(b"{}"))

    def _load_data(self) -> dict:
        with open(self.data_path, "rb") as f:
            decrypted = self.data_fernet.decrypt(f.read())
        return json.loads(decrypted.decode())

    def _save_data(self, data: dict) -> None:
        encrypted = self.data_fernet.encrypt(json.dumps(data).encode())
        with open(self.data_path, "wb") as f:
            f.write(encrypted)

    def store_key(self, key_id: str, secret: str) -> None:
        vecs = self.db.load_vectors()
        mapping = self.map.load_map()
        if key_id in mapping:
            index = mapping[key_id]
        else:
            index = np.random.randint(0, self.db_size)
            mapping[key_id] = index
            self.map.save_map(mapping)
        vecs[index] = _random_vector(self.dimensions)
        self.db.save_vectors(vecs)
        data = self._load_data()
        data[key_id] = self.data_fernet.encrypt(secret.encode()).decode()
        self._save_data(data)

    def retrieve_key(self, key_id: str) -> Optional[str]:
        mapping = self.map.load_map()
        if key_id not in mapping:
            return None
        data = self._load_data()
        if key_id not in data:
            return None
        enc = data[key_id].encode()
        return self.data_fernet.decrypt(enc).decode()

    def list_keys(self) -> list[str]:
        mapping = self.map.load_map()
        return list(mapping.keys())
