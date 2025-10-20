from __future__ import annotations

from typing import Iterable, List, Optional

from plexapi.server import PlexServer
from plexapi.video import Movie, Show

from utils.logger import get_logger
from core.models import MediaItem, PosterTask

logger = get_logger()

class PlexService:
    def __init__(self, url: str, token: str):
        self._plex = PlexServer(url, token)
        logger.info(f"Connected to Plex: {self._plex.friendlyName}")

    @classmethod
    def from_config(cls, config: dict):
        return cls(
            url=config["plex"]["url"],
            token=config["plex"]["token"]
        )

    def list_libraries(self):
        return [section.title for section in self._plex.library.sections()]

    def get_item_by_rating_key(self, rating_key: int) -> Movie | Show | None:
        try:
            return self._plex.fetchItem(rating_key)
        except Exception as e:
            logger.error(f"Failed to fetch item ratingKey={rating_key}: {e}")
            return None

    def find_movie_by_title(self, title: str) -> Movie | None:
        for section in self._plex.library.sections():
            if section.type != "movie":
                continue
            try:
                results = section.search(title=title)
                for r in results:
                    if getattr(r, "title", "").lower() == title.lower():
                        return r
            except Exception as e:
                logger.warning(f"Error searching in section {section.title}: {e}")
        return None

    def upload_poster_by_rating_key(self, rating_key: int, image_path: str) -> bool:
        item = self.get_item_by_rating_key(rating_key)
        if not item:
            logger.error(f"Plex item not found: {rating_key}")
            return False

        try:
            item.uploadPoster(filepath=image_path)
            logger.info(f"✅ Poster uploaded to Plex item {rating_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload poster: {e}")
            return False

    def upload_poster_for_task(self, task: PosterTask) -> bool:
        if not task.item.plex_id:
            logger.error(f"No Plex ID in MediaItem: {task.item.title}")
            return False

        image_path = task.output_file or task.downloaded_file
        if not image_path:
            logger.error(f"PosterTask has no image for upload: {task.item.title}")
            return False

        try:
            item = self.get_item_by_rating_key(task.item.plex_id)
            if not item:
                logger.error(f"Plex item {task.item.plex_id} not found in server")
                return False

            item.uploadPoster(filepath=image_path)
            task.status = "uploaded"
            logger.info(f"📤 Poster uploaded to Plex for '{task.item.title}' ({task.item.plex_id})")
            return True

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

    def iter_library_items(self, library_names: Optional[Iterable[str]] = None) -> List[MediaItem]:
        media_items: List[MediaItem] = []
        for section in self._plex.library.sections():
            if library_names and section.title not in library_names:
                continue
            try:
                for entry in section.all():
                    media_item = self._to_media_item(entry)
                    if media_item:
                        media_items.append(media_item)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Failed to list section {section.title}: {exc}")
        return media_items

    def build_media_item(self, rating_key: int) -> Optional[MediaItem]:
        plex_item = self.get_item_by_rating_key(rating_key)
        if not plex_item:
            return None
        return self._to_media_item(plex_item)

    def _to_media_item(self, plex_item: Movie | Show) -> Optional[MediaItem]:
        tmdb_id = None
        imdb_id = None
        tvdb_id = None
        try:
            for guid in getattr(plex_item, "guids", []) or []:
                if guid.id.startswith("tmdb://"):
                    tmdb_id = int(guid.id.split("//", 1)[1])
                elif guid.id.startswith("imdb://"):
                    imdb_id = guid.id.split("//", 1)[1]
                elif guid.id.startswith("tvdb://"):
                    tvdb_id = int(guid.id.split("//", 1)[1])
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Unable to parse GUIDs for {plex_item}: {exc}")

        media_type = getattr(plex_item, "type", "movie")

        return MediaItem(
            plex_id=int(getattr(plex_item, "ratingKey")),
            title=getattr(plex_item, "title", "Unknown"),
            year=getattr(plex_item, "year", None),
            tmdb_id=tmdb_id,
            imdb_id=imdb_id,
            tvdb_id=tvdb_id,
            media_type=media_type,
            poster_path=getattr(plex_item, "thumb", None),
        )
