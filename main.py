"""
Main entry point for Posteract with TMDB selection + SQLite cache.
"""

from core.config_loader import load_config
from core.poster_repository import PosterRepository
from services.tmdb_service import TmdbService
from services.plex_service import PlexService
from utils.logger import get_logger

logger = get_logger("Posteract")

# You can also move this to config.yaml later
RETRY_AFTER_DAYS = 7
WANTED_TYPE = "textless"   # we want textless first (Posterizarr's 'xx')


def main():
    logger.info("🚀 Starting Posteract with smart poster selection…")
    cfg = load_config()

    # Services
    plex = PlexService.from_config(cfg)
    logger.info(f"✅ Plex connected → {plex.list_libraries()}")

    tmdb = TmdbService.from_config(cfg)
    repo = PosterRepository()

    # Example movie TMDB IDs to process (replace with your own flow)
    to_process = [603, 27205, 155]  # Matrix, Inception, The Dark Knight

    for tmdb_id in to_process:
        choice = tmdb.pick_movie_poster(tmdb_id, lang_pref="xx")  # 'xx' = textless preference
        if not choice.url:
            logger.warning(f"No poster available for TMDB {tmdb_id}")
            continue

        # Save the result to SQLite (wanted vs actual)
        repo.save_result(
            tmdb_id=tmdb_id,
            media_type="movie",
            wanted_type=WANTED_TYPE,
            actual_type=choice.actual_type or "none",
            poster_url=choice.url,
        )

        # Download the chosen poster
        filename = f"{tmdb_id}_{choice.actual_type or 'none'}.jpg"
        path = tmdb.download_poster(choice.url, filename=filename)
        logger.info(f"Poster for {tmdb_id} ({choice.actual_type}) saved at {path}")

    # Example of checking retries:
    due = repo.due_retries(retry_after_days=RETRY_AFTER_DAYS, wanted_type=WANTED_TYPE, limit=50)
    if due:
        logger.info(f"🕒 Items due for retry (wanted={WANTED_TYPE}): {[d['tmdb_id'] for d in due]}")
    else:
        logger.info("No items due for retry yet.")

    logger.info("✅ Done.")


if __name__ == "__main__":
    main()
