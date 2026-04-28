"""
Memory Module — Kullanıcı tercihlerini JSON dosyasında saklar.
"""

import json
import os
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_memory.json")


def _load_memory() -> dict:
    """Mevcut hafıza dosyasını yükler."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"searches": [], "preferences": {}}
    return {"searches": [], "preferences": {}}


def _save_memory(data: dict) -> None:
    """Hafıza dosyasına yazar."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_search(city: str, start_date: str, end_date: str, preference: str) -> None:
    """Bir arama kaydını hafızaya ekler."""
    memory = _load_memory()
    memory["searches"].append({
        "city": city,
        "start_date": start_date,
        "end_date": end_date,
        "preference": preference,
        "timestamp": datetime.now().isoformat(),
    })
    # Son 20 aramayı tut
    memory["searches"] = memory["searches"][-20:]
    _save_memory(memory)


def get_recent_searches(limit: int = 5) -> list[dict]:
    """Son aramaları döndürür."""
    memory = _load_memory()
    return memory["searches"][-limit:]


def save_preference(key: str, value: str) -> None:
    """Bir kullanıcı tercihini kaydeder."""
    memory = _load_memory()
    memory["preferences"][key] = value
    _save_memory(memory)


def get_preferences() -> dict:
    """Kaydedilmiş tercihleri döndürür."""
    memory = _load_memory()
    return memory.get("preferences", {})
