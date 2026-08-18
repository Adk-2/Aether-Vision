"""Local JSON persistence for Project Aether memory."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TextIO

from .memory_quality import (
    DEFAULT_MOVEMENT_DEBOUNCE_SECONDS,
    compact_persistent_memory,
)
from .serializer import PersistentMemory, empty_memory, from_json, to_json

DEFAULT_MEMORY_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "aether_memory.json"
)


class PersistenceStore:
    """Save, load, and clear persistent memory from a single JSON file."""

    def __init__(
        self,
        path: str | Path | None = None,
        movement_debounce_seconds: float = DEFAULT_MOVEMENT_DEBOUNCE_SECONDS,
    ) -> None:
        self.path = Path(path) if path is not None else DEFAULT_MEMORY_PATH
        self.movement_debounce_seconds = movement_debounce_seconds

    def save(self, memory: PersistentMemory) -> None:
        """Atomically write memory to disk as valid, readable JSON."""
        memory = compact_persistent_memory(memory, self.movement_debounce_seconds)
        self._ensure_parent()
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(to_json(memory), handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_path, self.path)

    def load(self) -> PersistentMemory:
        """Load memory, returning empty memory if the file is missing or invalid."""
        try:
            self._ensure_file()
            with self.path.open("r", encoding="utf-8") as handle:
                return _load_json(handle)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Warning: could not load persistent memory: {exc}")
            return empty_memory()

    def clear(self) -> None:
        """Clear persisted memory while keeping the JSON file present."""
        self.save(empty_memory())

    def _ensure_parent(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_file(self) -> None:
        self._ensure_parent()
        if not self.path.exists():
            self.save(empty_memory())


def save(memory: PersistentMemory, path: str | Path | None = None) -> None:
    """Save persistent memory using the default store."""
    PersistenceStore(path).save(memory)


def load(path: str | Path | None = None) -> PersistentMemory:
    """Load persistent memory using the default store."""
    return PersistenceStore(path).load()


def clear(path: str | Path | None = None) -> None:
    """Clear persistent memory using the default store."""
    PersistenceStore(path).clear()


def _load_json(handle: TextIO) -> PersistentMemory:
    raw = handle.read().strip()
    if not raw:
        return empty_memory()
    data = json.loads(raw)
    return from_json(data)
