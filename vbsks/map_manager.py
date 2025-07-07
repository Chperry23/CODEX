from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import Dict

from cryptography.fernet import Fernet
import hashlib
import base64

from .database import _ensure_dir


def _derive_key(password: str) -> bytes:
    digest = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(digest)


@dataclass
class MapManager:
    """Manage encrypted mapping of key ids to vector indices."""

    folder: str
    master_password: str

    def __post_init__(self) -> None:
        _ensure_dir(self.folder)
        self.map_path = os.path.join(self.folder, "map.enc")
        self.fernet = Fernet(_derive_key(self.master_password))
        if not os.path.exists(self.map_path):
            self.save_map({})

    def load_map(self) -> Dict[str, int]:
        with open(self.map_path, "rb") as f:
            data = f.read()
        if not data:
            return {}
        decrypted = self.fernet.decrypt(data)
        return json.loads(decrypted.decode())

    def save_map(self, mapping: Dict[str, int]) -> None:
        data = json.dumps(mapping).encode()
        encrypted = self.fernet.encrypt(data)
        with open(self.map_path, "wb") as f:
            f.write(encrypted)
