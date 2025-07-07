from __future__ import annotations

import numpy as np
from dataclasses import dataclass

from .key_manager import KeyManager


@dataclass
class ReconfigurationController:
    manager: KeyManager

    def reconfigure(self) -> None:
        """Move all key vectors to new random positions."""
        vecs = self.manager.db.load_vectors()
        mapping = self.manager.map.load_map()
        for key_id, index in mapping.items():
            new_index = np.random.randint(0, self.manager.db_size)
            vecs[new_index] = vecs[index]
            vecs[index] = np.random.normal(size=(self.manager.dimensions,))
            mapping[key_id] = new_index
        self.manager.db.save_vectors(vecs)
        self.manager.map.save_map(mapping)
