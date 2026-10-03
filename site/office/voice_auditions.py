"""Local-only Gemini audition catalog, immutable samples, and saved evaluations."""

import hashlib
import json
import os
import threading
from pathlib import Path

import requests
from django.conf import settings

from office.api.views.tts import GeminiTTSProvider
from office.voice_style import GEMINI_PRAYER_STYLE

# Contemporary Collect for Grace, with an opening Amen for pronunciation auditions.
SAMPLE_TEXT = (
    "Amen. O Lord, our heavenly Father, almighty and everlasting God, you have brought us safely to the beginning of this day: "
    "Defend us by your mighty power, that we may not fall into sin nor run into any danger; and that, guided by your "
    "Spirit, we may do what is righteous in your sight; through Jesus Christ our Lord. Amen."
)
STYLE = GEMINI_PRAYER_STYLE


class AuditionProvider(GeminiTTSProvider):
    @property
    def effective_instructions(self):
        return STYLE


class AuditionStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.synthesis_lock = threading.Lock()
        self.provider = AuditionProvider()
        self.voices = {}
        self.total = 0
        self.load_catalog()
        self.results = self._read("results.json", {})
        self.batch = {"status": "idle", "total": 0, "completed": 0, "failed": [], "current": None}
        self.batch_stop = threading.Event()
        self.batch_thread = None

    def _read(self, name, default):
        path = self.directory / name
        return json.loads(path.read_text()) if path.exists() else default

    def _write(self, name, data):
        path = self.directory / name
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2))
        os.replace(temporary, path)

    def load_catalog(self, refresh=False):
        with self.lock:
            catalog = None if refresh else self._read("catalog.json", None)
            if catalog is None:
                if not settings.GEMINI_API_KEY:
                    raise ValueError("Set GEMINI_API_KEY in site/website/.env first.")
                catalog, seen, token = [], set(), ""
                while True:
                    response = requests.get(
                        "https://generativelanguage.googleapis.com/v1beta/voices",
                        headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                        params={"page_size": 1000, **({"page_token": token} if token else {})},
                        timeout=30,
                    )
                    if not response.ok:
                        raise ValueError(f"Google voice catalog failed (HTTP {response.status_code}).")
                    page = response.json()
                    if not isinstance(page.get("voices"), list):
                        raise ValueError("Google returned an invalid voice catalog.")
                    catalog.extend(page["voices"])
                    token = page.get("next_page_token", "")
                    if not token:
                        break
                    if token in seen:
                        raise ValueError("Google repeated a voice catalog page token.")
                    seen.add(token)
                self._write("catalog.json", catalog)
            self.total = len(catalog)
            # Regional US accents are American English too. Exclude ambiguous metadata.
            self.voices = {
                v["id"]: v
                for v in catalog
                if v.get("id")
                and v.get("language_code", "").lower() == "en-us"
                and v.get("region_code", "US").upper() == "US"
            }

    def sample_key(self, voice):
        return hashlib.sha256(json.dumps([voice, SAMPLE_TEXT, self.provider.cache_signature()]).encode()).hexdigest()

    def snapshot(self):
        with self.lock:
            return {
                "voices": sorted(self.voices.values(), key=lambda v: (v.get("display_name") or v["id"]).casefold()),
                "results": self.results.copy(),
                "total": self.total,
                "sample": SAMPLE_TEXT,
                "sample_title": "A Collect for Grace",
                "sample_source": "Daily Office · Morning Prayer · Contemporary language",
                "style": STYLE,
                "model": self.provider.model,
                "cached": [v for v in self.voices if self.is_cached(v)],
                "batch": {**self.batch, "failed": list(self.batch["failed"])},
                "popularity_available": False,
            }

    def is_cached(self, voice):
        path = self.audio_path(self.sample_key(voice))
        return path.exists() and path.stat().st_size > 0

    def start_batch(self):
        """Resume missing samples; one paid request at a time, shared with playback."""
        with self.lock:
            if self.batch["status"] in {"running", "stopping"}:
                return self.snapshot()
            pending = [v for v in self.voices if not self.is_cached(v)]
            self.batch_stop.clear()
            self.batch = {"status": "running", "total": len(pending), "completed": 0, "failed": [], "current": None}
            self.batch_thread = threading.Thread(target=self._run_batch, args=(pending,), daemon=True)
            self.batch_thread.start()
            return self.snapshot()

    def stop_batch(self):
        with self.lock:
            if self.batch["status"] == "running":
                self.batch["status"] = "stopping"
                self.batch_stop.set()
            return self.snapshot()

    def _run_batch(self, pending):
        try:
            for voice in pending:
                with self.lock:
                    if self.batch_stop.is_set():
                        break
                    self.batch["current"] = voice
                try:
                    self.synthesize(voice)
                except Exception:
                    # Keep credentials and upstream response bodies out of browser status.
                    with self.lock:
                        self.batch["failed"].append(voice)
                finally:
                    with self.lock:
                        self.batch["completed"] += 1
        finally:
            with self.lock:
                self.batch["current"] = None
                self.batch["status"] = "paused" if self.batch_stop.is_set() else "complete"

    def audio_path(self, key):
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("Invalid sample identifier.")
        return self.directory / f"{key}.mp3"

    def synthesize(self, voice):
        if voice not in self.voices:
            raise ValueError("Select an American English voice from the catalog.")
        key = self.sample_key(voice)
        path = self.audio_path(key)
        # Serialize paid requests and double-check the cache under the lock.
        with self.synthesis_lock:
            if not path.exists() or not path.stat().st_size:
                self.provider.synthesize(voice, SAMPLE_TEXT, str(path))
        return {"url": f"/audio/{key}.mp3"}

    def save_result(self, data):
        voice = data.get("voice")
        if voice not in self.voices:
            raise ValueError("Unknown voice.")
        status, rating, notes = data.get("status"), data.get("rating"), data.get("notes", "")
        if status not in {"unreviewed", "shortlist", "reject", "maybe"}:
            raise ValueError("Invalid decision.")
        if type(rating) is not int or not 0 <= rating <= 5 or not isinstance(notes, str) or len(notes) > 2000:
            raise ValueError("Use a rating from 0 to 5 and notes under 2,000 characters.")
        with self.lock:
            self.results[voice] = {"status": status, "rating": rating, "notes": notes}
            self._write("results.json", self.results)
        return {"saved": True}
