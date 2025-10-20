"""Poster workflow orchestration across selection, download, caching and upload."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Iterable, Optional

import httpx

from core.models import MediaItem, PosterTask
from core.poster_repository import PosterRepository
from services.orchestrator_service import PosterOrchestratorService
from services.overlay_service import OverlayService
from services.plex_service import PlexService
from utils.db import PosterJobStore
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowResult:
    task: PosterTask
    success: bool
    message: str = ""


class PosterWorkflow:
    """Coordinates poster selection, download, caching and upload."""

    def __init__(
        self,
        config: dict,
        orchestrator: PosterOrchestratorService,
        plex: PlexService,
        repository: PosterRepository,
        job_store: PosterJobStore,
        overlay: Optional[OverlayService] = None,
        apply_overlay: bool = False,
    ) -> None:
        self.config = config
        self.orchestrator = orchestrator
        self.plex = plex
        self.repository = repository
        self.job_store = job_store
        self.overlay = overlay
        overlay_cfg = config.get("overlays", {})
        self.overlay_filename = overlay_cfg.get("posterFilename", "overlay.png")
        self.apply_overlay = apply_overlay and overlay is not None
        preferences = config.get("poster_preferences") or ["textless"]
        self.desired_type = preferences[0]
        self.cache_dir = Path(config.get("outputDirectory", "output/posters"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def process_item(self, item: MediaItem) -> WorkflowResult:
        logger.info(f"Processing item: {item.title} ({item.tmdb_id})")
        task = self.orchestrator.create_task(item)
        media_key = self._media_key(item)
        self.job_store.upsert(
            media_id=media_key,
            tmdb_id=item.tmdb_id,
            source_used=self._source_from_type(task.source_type),
            poster_type=task.source_type,
            status=task.status,
            quality_selection=self.desired_type,
        )

        if task.status != "selected" or not task.chosen_url:
            message = "No poster available"
            logger.warning(f"{message} for {item.title}")
            self.job_store.update_status(media_key, status="not_found", error=message)
            return WorkflowResult(task=task, success=False, message=message)

        filename = self._build_filename(item, task)
        try:
            task.downloaded_file = self._download(task.chosen_url, filename)
            task.status = "downloaded"
            self.job_store.update_status(media_key, status="downloaded")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Download failed for {item.title}: {exc}")
            task.status = "failed"
            self.job_store.update_status(media_key, status="failed", error=str(exc))
            return WorkflowResult(task=task, success=False, message=str(exc))

        if self.apply_overlay and self.overlay:
            overlay_file = self.overlay.apply_overlay(task.downloaded_file, self.overlay_filename)
            if overlay_file:
                task.output_file = overlay_file
            else:
                logger.warning("Overlay application failed; continuing with downloaded file")
                task.output_file = task.downloaded_file
        else:
            task.output_file = task.downloaded_file

        uploaded = self.plex.upload_poster_for_task(task)
        if not uploaded:
            message = "Upload to Plex failed"
            logger.error(message)
            task.status = "failed"
            self.job_store.update_status(
                media_key, status="failed", error=message, retry_in=timedelta(hours=6)
            )
            return WorkflowResult(task=task, success=False, message=message)

        task.status = "uploaded"
        self.job_store.mark_uploaded(media_key)

        if item.tmdb_id:
            self.repository.save_result(
                tmdb_id=item.tmdb_id,
                media_type=item.media_type,
                wanted_type=self.desired_type,
                actual_type=task.source_type or "unknown",
                poster_url=task.chosen_url,
            )

        logger.info(f"Completed workflow for {item.title}")
        return WorkflowResult(task=task, success=True)

    def process_items(self, items: Iterable[MediaItem]) -> list[WorkflowResult]:
        results: list[WorkflowResult] = []
        for item in items:
            try:
                results.append(self.process_item(item))
            except Exception as exc:  # noqa: BLE001
                logger.exception(f"Unhandled error processing {item.title}: {exc}")
                task = PosterTask(item=item, status="failed")
                results.append(WorkflowResult(task=task, success=False, message=str(exc)))
        return results

    def _download(self, url: str, filename: str) -> str:
        target = self.cache_dir / filename
        logger.debug(f"Downloading poster → {url} -> {target}")
        try:
            with httpx.stream("GET", url, timeout=30.0) as response:
                response.raise_for_status()
                with open(target, "wb") as fh:
                    for chunk in response.iter_bytes():
                        fh.write(chunk)
        except Exception:
            if target.exists():
                target.unlink()
            raise
        return str(target)

    def _build_filename(self, item: MediaItem, task: PosterTask) -> str:
        base = f"{item.tmdb_id or item.plex_id or item.title}".replace("/", "_")
        suffix = task.source_type or "poster"
        return f"{base}_{suffix}.jpg"

    def _media_key(self, item: MediaItem) -> str:
        if item.plex_id is not None:
            return str(item.plex_id)
        if item.tmdb_id is not None:
            return f"tmdb-{item.tmdb_id}"
        return item.title

    @staticmethod
    def _source_from_type(source_type: Optional[str]) -> Optional[str]:
        if not source_type:
            return None
        if source_type.startswith("fanart"):
            return "fanart"
        return "tmdb"
