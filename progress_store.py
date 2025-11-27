import json
import os
from typing import Dict, Set

PROGRESS_FILE = "progress.json"

class ProgressStore:
    def __init__(self, path: str = PROGRESS_FILE):
        self.path = path
        self.data = {
            "turns": 0,
            "corrections": 0,
            "vocabulary": {},  # word -> count
        }
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def increment_turn(self):
        self.data["turns"] += 1
        self.save()

    def add_corrections(self, count: int):
        self.data["corrections"] += count
        self.save()

    def add_vocabulary(self, words: Set[str]):
        for w in words:
            if not w:
                continue
            self.data["vocabulary"][w] = self.data["vocabulary"].get(w, 0) + 1
        self.save()

    def top_vocabulary(self, n: int = 10):
        return sorted(self.data["vocabulary"].items(), key=lambda x: x[1], reverse=True)[:n]

progress_store = ProgressStore()
