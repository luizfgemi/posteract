from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class MediaItem:
    """
    Represents a Movie or TV Show from Plex/TMDB.
    Holds all identifiers we might need.
    """
    plex_id: int                 # Plex ratingKey
    title: str
    year: Optional[int]
    tmdb_id: Optional[int]       # For TMDB
    imdb_id: Optional[str] = None
    tvdb_id: Optional[int] = None
    media_type: str = "movie"    # "movie" or "show"
    poster_path: Optional[str] = None    # Existing Plex poster path (if any)
    collection_id: Optional[int] = None  # TMDB Collection (Ex: MCU, Harry Potter etc.)

@dataclass
class PosterTask:
    """
    Represents a unit of work: generate/upload a poster for a single media item.
    """
    item: MediaItem
    chosen_url: Optional[str] = None          # URL from TMDB or Fanart.tv
    source_type: Optional[str] = None         # "textless", "fanart", "tmdb_en", etc.
    downloaded_file: Optional[str] = None     # Local file path after download
    output_file: Optional[str] = None         # Final output path after overlays
    status: str = "pending"                   # pending, downloaded, rendered, uploaded
    last_update: datetime = field(default_factory=datetime.now)
