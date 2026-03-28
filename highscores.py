"""High score table — top 5 entries with initials, persisted to highscores.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple


class HighScoreEntry(NamedTuple):
    initials: str
    score: int


class HighScoreTable:
    """Top 5 high scores, persisted to disk as JSON."""

    MAX_ENTRIES = 5

    def __init__(self, path: str = "highscores.json") -> None:
        self._path = path
        self._entries: list[HighScoreEntry] = []
        self._load()

    @property
    def entries(self) -> list[HighScoreEntry]:
        return list(self._entries)

    def is_high_score(self, score: int) -> bool:
        """True if this score would make the top-5 table."""
        if len(self._entries) < self.MAX_ENTRIES:
            return True
        return score > self._entries[-1].score

    def add_entry(self, initials: str, score: int) -> None:
        """Add an entry. Keeps the table sorted, max MAX_ENTRIES long."""
        self._entries.append(HighScoreEntry(initials[:3].upper(), score))
        self._entries.sort(key=lambda e: e.score, reverse=True)
        self._entries = self._entries[: self.MAX_ENTRIES]
        self._save()

    def _load(self) -> None:
        path = Path(self._path)
        if not path.exists():
            return
        with open(path) as f:
            data = json.load(f)
        self._entries = [HighScoreEntry(e["initials"], e["score"]) for e in data]

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(
                [{"initials": e.initials, "score": e.score} for e in self._entries],
                f,
                indent=2,
            )
