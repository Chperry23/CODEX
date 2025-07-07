from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .key_manager import KeyManager
from .reconfiguration import ReconfigurationController


@dataclass
class VBSKSEasy:
    db_folder: str
    master_password: str

    def __post_init__(self) -> None:
        self.manager = KeyManager(self.db_folder, self.master_password)
        self.reconfig = ReconfigurationController(self.manager)

    def store_key(self, key_id: str, data: str) -> None:
        self.manager.store_key(key_id, data)

    def retrieve_key(self, key_id: str) -> Optional[str]:
        return self.manager.retrieve_key(key_id)

    def list_keys(self) -> list[str]:
        return self.manager.list_keys()

    def reconfigure(self) -> None:
        self.reconfig.reconfigure()

    def delete_key(self, key_id: str) -> bool:
        return self.manager.delete_key(key_id)
