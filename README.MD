## Posteract Roadmap — Full Replacement for Posterizarr and Kometa (Poster and Artwork Features)

### 1. Core (Implemented)
* Load configuration from `config.yaml`
* Connect to Plex (PlexAPI)
* Retrieve libraries from Plex
* Fetch posters from TMDB (textless, language-specific, fallback)
* Fetch artwork from Fanart.tv (textless posters)
* Poster source selection via `poster_preferences`
* Upload posters to Plex
* Logging using Loguru

---

### 2. Phase 1 — Basic Poster Workflow ✅
Posteract now automates the full basic poster workflow from discovery through upload.

**Poster lifecycle**
* Poster selection is orchestrated with TMDB and Fanart.tv sources according to configuration.
* Downloads are cached locally under `output/posters/` and reused automatically on subsequent runs.
* Poster status is persisted in SQLite via `poster_jobs`, including media identifiers, source metadata, timestamps, retry tracking, and chosen quality.
* Poster results are logged in `poster_cache` for quick lookups of previously used artwork.

**Command line interface**
```
posteract --config /path/to/config.yaml --item "Movie Title"
posteract --config /path/to/config.yaml --all
posteract --config /path/to/config.yaml --test
posteract --config /path/to/config.yaml --reset           # reset every library
posteract --config /path/to/config.yaml --reset Movies TV  # reset specific libraries
```

* `--item` accepts either a Plex rating key or an exact title.
* `--all` processes every item in the configured libraries.
* `--test` runs against built-in demo data without Plex access.
* `--reset` clears the local cache, wipes the job database, and invokes the same Plex poster reset flow as Posterizarr's `Reset-PlexLibraryPictures` task.

---

### 3. Phase 2 — Advanced Overlay System (Posterizarr-Level)
- Build OverlayService using Pillow or ImageMagick
- Support multiple overlay layers:
  - Streaming logos (Netflix, Prime Video, Disney+)
  - Resolution tags (4K, HDR, Dolby Vision)
  - IMDb/TMDb ratings, Rotten Tomatoes score
  - Award badges (Oscars, Golden Globes)
- Custom text rendering on posters:
  - Movie title placement, custom font, color, drop shadows
- Poster style templates (minimalistic, neon, cinema style, etc.)
- Automatic title placement for textless posters
- Color analysis for dynamic contrast between text and background

---

### 4. Phase 3 — Plex Collections (Kometa-Style)
- Auto-create Plex collections based on:
  - TMDb collections (e.g., Marvel, James Bond, etc.)
  - Genres, studios, directors, actors
  - IMDb lists, TMDb lists, Trakt lists
- YAML-based collection configuration (similar to Kometa):
```
collections:
Christopher Nolan:
imdb_list: "https://www.imdb.com/list/lsXXXXXXXXX/"
sort_title: "Nolan"
overlay: "director"
```

- Assign posters and backgrounds to collections
- Automatically refresh collections when new matching items are added to Plex

---

### 5. Phase 4 — Automation and Scheduling
- Add APScheduler for scheduled jobs (daily, weekly, or manual)
- Automatically recheck items if:
- A better or newly-available textless poster appears
- Fanart.tv or TMDb updates artwork
- Retry logic with exponential backoff
- Optional REST API using FastAPI to trigger actions or refresh posters remotely

---

### 6. Phase 5 — External Integration (Radarr / Sonarr / Trakt)
- When Sonarr/Radarr adds a new media file:
- Posteract fetches and uploads the poster automatically
- Sync Plex collections with Trakt watchlists, IMDb Top 250, or TMDb Trending
- Auto-update collection posters if artwork changes or improves

---

### 7. Final Goal
Once complete, Posteract will:
- Fully replace Posterizarr and Kometa for poster and artwork workflows
- Provide automated, configurable poster generation and Plex uploading
- Support overlays, collections, metadata updates, schedules, and fallbacks
- Run on Linux, Windows, Docker, Unraid, and TrueNAS
- Support CLI usage, scheduled tasks, and an optional REST API
