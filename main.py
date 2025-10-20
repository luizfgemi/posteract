"""Posteract CLI entry point."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Optional

from core.config import load_config
from core.models import MediaItem
from core.poster_repository import PosterRepository
from services.fanart_service import FanartService
from services.orchestrator_service import PosterOrchestratorService
from services.overlay_service import OverlayService
from services.plex_client import PlexClient
from services.plex_service import PlexService
from services.poster_workflow import PosterWorkflow, WorkflowResult
from services.tmdb_service import TmdbService
from utils.db import PosterJobStore
from utils.logger import get_logger, setup_logger

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Posteract poster workflow")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--item", type=str, help="Process a single Plex item by rating key or title")
    group.add_argument("--all", action="store_true", help="Process all configured libraries")
    group.add_argument("--test", action="store_true", help="Run the workflow against sample data")
    group.add_argument(
        "--reset",
        nargs="*",
        metavar="LIBRARY",
        help="Reset cached posters and Plex library posters (optionally limit to libraries)",
    )
    return parser.parse_args()


def build_workflow(config: dict) -> tuple[PosterWorkflow, PlexService, PosterJobStore]:
    tmdb_service = TmdbService.from_config(config)
    fanart_service = FanartService.from_config(config)
    orchestrator = PosterOrchestratorService(config, tmdb_service, fanart_service)
    plex_service = PlexService.from_config(config)

    overlays_cfg = config.get("overlays", {})
    overlay_service: Optional[OverlayService] = None
    if overlays_cfg.get("enable") and overlays_cfg.get("path"):
        overlay_service = OverlayService(
            overlay_base_path=overlays_cfg["path"],
            output_dir=config.get("outputDirectory", "output/posters"),
        )

    repository = PosterRepository()
    job_store = PosterJobStore()
    workflow = PosterWorkflow(
        config=config,
        orchestrator=orchestrator,
        plex=plex_service,
        repository=repository,
        job_store=job_store,
        overlay=overlay_service,
        apply_overlay=bool(overlay_service),
    )
    return workflow, plex_service, job_store


def run_for_item(workflow: PosterWorkflow, plex: PlexService, identifier: str) -> WorkflowResult:
    identifier = identifier.strip()
    media_item: Optional[MediaItem] = None

    if identifier.isdigit():
        rating_key = int(identifier)
        media_item = plex.build_media_item(rating_key)
        if not media_item:
            raise RuntimeError(f"Plex item with rating key {rating_key} not found")
    else:
        media_item = plex.find_media_item_by_title(identifier)
        if not media_item:
            raise RuntimeError(f"Plex item titled '{identifier}' not found")

    return workflow.process_item(media_item)


def run_for_all(workflow: PosterWorkflow, plex: PlexService, config: dict) -> List[WorkflowResult]:
    libraries = config.get("libraries")
    items = plex.iter_library_items(libraries)
    return workflow.process_items(items)


def run_test(workflow: PosterWorkflow) -> List[WorkflowResult]:
    sample_items = [
        MediaItem(plex_id=None, title="Demo Movie", year=1999, tmdb_id=603, media_type="movie"),
        MediaItem(plex_id=None, title="Demo Show", year=2010, tmdb_id=1399, media_type="show"),
    ]
    return workflow.process_items(sample_items)


def handle_reset(config: dict, job_store: PosterJobStore, libraries: Optional[Iterable[str]]) -> None:
    plex_client = PlexClient.from_config(config)
    cache_dir = Path(config.get("outputDirectory", "output/posters"))
    PlexClient.clear_cache(cache_dir)
    job_store.clear()
    touched = plex_client.reset_library_posters(libraries)
    logger.info(f"Reset completed for {touched} Plex items")


def log_results(results: Iterable[WorkflowResult]) -> None:
    for result in results:
        status = "success" if result.success else "failed"
        logger.info(
            f"{result.task.item.title} → {status} ({result.task.status})"
            + (f" :: {result.message}" if result.message else "")
        )


def main() -> None:
    setup_logger()
    args = parse_args()
    config = load_config(args.config)
    workflow, plex_service, job_store = build_workflow(config)

    if args.reset is not None:
        libraries = args.reset if args.reset else None
        handle_reset(config, job_store, libraries)
        return

    if args.test:
        results = run_test(workflow)
        log_results(results)
        return

    if args.item is not None:
        result = run_for_item(workflow, plex_service, args.item)
        log_results([result])
        return

    if args.all:
        results = run_for_all(workflow, plex_service, config)
        log_results(results)
        return


if __name__ == "__main__":
    main()
