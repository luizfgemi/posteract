from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fanart.tv import FanartTv
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PosterResult:
    url: str
    type: str  # "fanart_poster", "fanart_hdlogo", etc.


class FanartService:
    """
    Service for interacting with Fanart.tv API.
    """

    def __init__(self, api_key: str, enabled: bool = True):
        self.enabled = enabled
        if not enabled or not api_key:
            logger.warning("Fanart.tv disabled or API key missing.")
            self.client = None
        else:
            self.client = FanartTv(api_key=api_key)
            logger.info("Fanart.tv service initialized.")

    @classmethod
    def from_config(cls, cfg: dict) -> "FanartService":
        fanart_cfg = cfg.get("fanart", {})
        return cls(
            api_key=fanart_cfg.get("api_key", ""),
            enabled=fanart_cfg.get("enabled", True)
        )

    def get_movie_textless(self, tmdb_id: int) -> Optional[PosterResult]:
        """
        Fetch textless poster for a movie from Fanart.tv.
        Returns PosterResult if found, else None.
        """
        if not self.client or not self.enabled:
            return None

        try:
            data = self.client.get_movie_artwork(tmdb_id)
            # Fanart.tv returns:
            # {
            #   'movieposter': [{'url': '...', 'lang': 'en', 'likes': 10, ...}, ...],
            #   'hdmovielogo': [{'url': '...', ...}], ← *logos*
            # }

            posters = data.get("movieposter", [])
            if not posters:
                logger.debug(f"Fanart: no movieposter for TMDB ID {tmdb_id}")
                return None

            # Pick the one with the most "likes" (higher quality/popularity)
            posters_sorted = sorted(posters, key=lambda p: int(p.get("likes", 0)), reverse=True)
            best = posters_sorted[0]

            url = best.get("url")
            if url:
                logger.info(f"Fanart: found poster for TMDB {tmdb_id}: {url}")
                return PosterResult(url=url, type="fanart_poster")

        except Exception as e:
            logger.error(f"Fanart.tv error for tmdb_id={tmdb_id}: {e}")

        return None
