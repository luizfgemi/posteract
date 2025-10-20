from __future__ import annotations

from typing import Optional, List
from utils.logger import get_logger

from services.tmdb_service import TmdbService, PosterResult
from services.fanart_service import FanartService
from core.models import PosterTask, MediaItem

logger = get_logger()


class PosterOrchestratorService:
    """
    Decides the best poster source based on user 'poster_preferences' in config.yaml.
    Does NOT download the image — only chooses the best URL & source type.
    """

    def __init__(self, config: dict, tmdb_service: TmdbService, fanart_service: FanartService):
        self.tmdb = tmdb_service
        self.fanart = fanart_service
        self.preferences: List[str] = config.get("poster_preferences", ["textless", "tmdb_en", "tmdb_any"])

        logger.info(f"PosterOrchestrator initialized with preferences: {self.preferences}")

    def get_best_poster(self, item: MediaItem) -> Optional[PosterResult]:
        """
        Try each poster source in the order specified in config.
        Returns PosterResult(url, type) or None if nothing was found.
        """
        tmdb_id = item.tmdb_id
        if not tmdb_id:
            logger.warning(f"Item {item.title} has no TMDB ID, cannot fetch posters.")
            return None

        for pref in self.preferences:
            if pref == "fanart":
                result = self.fanart.get_movie_textless(tmdb_id)
                if result:
                    logger.info(f"Using Fanart poster for {item.title} ({tmdb_id})")
                    return PosterResult(result.url, "fanart")

            elif pref in ["textless", "tmdb_en", "tmdb_pt", "tmdb_any"]:
                result = self.tmdb.get_poster(tmdb_id, mode=pref)
                if result:
                    logger.info(f"Using TMDB ({pref}) poster for {item.title} ({tmdb_id})")
                    return result

        logger.warning(f"No poster found for {item.title} ({tmdb_id}) after checking all preferences.")
        return None

    def create_task(self, item: MediaItem) -> PosterTask:
        """
        Build a PosterTask with chosen poster URL & type.
        """
        task = PosterTask(item=item)
        poster = self.get_best_poster(item)
        if poster:
            task.chosen_url = poster.url
            task.source_type = poster.type
            task.status = "selected"
        else:
            task.status = "not_found"

        return task
