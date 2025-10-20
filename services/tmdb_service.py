from __future__ import annotations

import tmdbsimple as tmdb
from dataclasses import dataclass
from typing import Optional, List
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PosterResult:
    url: str
    type: str   # "textless", "tmdb_en", "tmdb_pt", "tmdb_any"


class TmdbService:
    """
    Service for interacting with TMDB API.
    """

    def __init__(self, api_key: str, language: str = "en-US"):
        if not api_key:
            raise ValueError("TMDB API key cannot be empty.")

        tmdb.API_KEY = api_key
        self.language = language.split("-")[0]  # ex: "en"
        self.image_base = "https://image.tmdb.org/t/p/original"

        logger.info(f"TMDB service initialized using tmdbsimple (lang={self.language})")

    @classmethod
    def from_config(cls, config: dict) -> "TmdbService":
        return cls(
            api_key=config["tmdb"]["apiKey"],
            language=config["tmdb"].get("language", "en-US")
        )

    def _get_movie_images(self, tmdb_id: int) -> List[dict]:
        """
        Fetch posters for a movie.
        Returns a list of poster metadata.
        Each entry looks like:
          {
            'file_path': '/abcd123.jpg',
            'iso_639_1': 'en' or None,
            'width': 1000,
            'height': 1500,
            ...
          }
        """
        try:
            movie = tmdb.Movies(tmdb_id)
            response = movie.images()
            posters = response.get("posters", []) or []
            return posters
        except Exception as e:
            logger.error(f"Error fetching TMDB images for ID {tmdb_id}: {e}")
            return []

    def get_poster(self, tmdb_id: int, mode: str) -> Optional[PosterResult]:
        """
        mode can be:
            textless  → iso_639_1 == None
            tmdb_en   → iso_639_1 == 'en'
            tmdb_pt   → iso_639_1 == 'pt' or 'pt-BR'
            tmdb_any  → first available poster

        Returns PosterResult(url, type) or None.
        """
        posters = self._get_movie_images(tmdb_id)
        if not posters:
            return None

        if mode == "textless":
            for p in posters:
                if p.get("iso_639_1") is None and p.get("file_path"):
                    return PosterResult(self.image_base + p["file_path"], "textless")

        if mode == "tmdb_en":
            for p in posters:
                if p.get("iso_639_1") == "en" and p.get("file_path"):
                    return PosterResult(self.image_base + p["file_path"], "tmdb_en")

        if mode == "tmdb_pt":
            for p in posters:
                if p.get("iso_639_1") in ("pt", "pt-BR") and p.get("file_path"):
                    return PosterResult(self.image_base + p["file_path"], "tmdb_pt")

        if mode == "tmdb_any":
            first = posters[0].get("file_path")
            if first:
                return PosterResult(self.image_base + first, "tmdb_any")

        return None
