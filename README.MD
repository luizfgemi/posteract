## Posteract Roadmap — Full Replacement for Posterizarr and Kometa (Poster and Artwork Features)

### 1. Core (Already Implemented)
- Load configuration from `config.yaml`
- Connect to Plex (PlexAPI)
- Retrieve libraries from Plex
- Fetch posters from TMDB (textless, language-specific, fallback)
- Fetch artwork from Fanart.tv (textless posters)
- Poster source selection via `poster_preferences`
- Upload posters to Plex
- Logging using Loguru

---

### 2. Phase 1 — Basic Poster Workflow
Goal: Automate poster download and upload for each media item.

- Implement poster download and local caching
- Add SQLite database to store:
  - media_id, tmdb_id, source_used, poster_type, status
  - timestamps, retry attempts, quality selection
- Implement PosterTask lifecycle: select → download → save → upload
- CLI support:
  - `posteract --item "Movie Title"`
  - `posteract --all`
  - `posteract --test`
- Implement poster reset (same behavior as Posterizarr’s Reset-PlexLibraryPictures)

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
