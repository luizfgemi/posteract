"""Low-level Plex client helpers for poster maintenance."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, Optional

from plexapi.server import PlexServer
from utils.logger import get_logger

logger = get_logger(__name__)


class PlexClient:
    """Wrapper around :class:`plexapi.server.PlexServer` exposing reset helpers."""

    def __init__(self, base_url: str, token: str) -> None:
        self._server = PlexServer(base_url, token)

    @classmethod
    def from_config(cls, config: dict) -> "PlexClient":
        plex_cfg = config.get("plex", {})
        return cls(base_url=plex_cfg.get("url", ""), token=plex_cfg.get("token", ""))

    def reset_library_posters(self, library_names: Optional[Iterable[str]] = None) -> int:
        """Reset posters for provided libraries. Returns number of items touched."""
        libraries = list(library_names) if library_names else None
        total = 0
        for section in self._server.library.sections():
            if libraries and section.title not in libraries:
                continue
            logger.info(f"Resetting posters for library '{section.title}'")
            for item in section.all():
                try:
                    # plexapi exposes both resetPoster and deletePoster depending on media type
                    reset_method = getattr(item, "resetPoster", None)
                    if callable(reset_method):
                        reset_method()
                    else:
                        delete_method = getattr(item, "deletePoster", None)
                        if callable(delete_method):
                            delete_method()
                    total += 1
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"Failed to reset poster for {item.title}: {exc}")
        logger.info(f"Poster reset complete ({total} items)")
        return total

    @staticmethod
    def clear_cache(cache_dir: Path) -> None:
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            logger.info(f"Deleted cache directory {cache_dir}")
