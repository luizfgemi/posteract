import httpx
from loguru import logger
from typing import Optional, Dict, Any

def http_get(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Optional[dict]:
    """
    Perform an HTTP GET request and return the JSON response as a dictionary.
    Handles errors and logs appropriately.
    """
    try:
        with httpx.Client(timeout=15.0) as client:   # 15s timeout (adjustable)
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} from {url} - {e}")
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to {url} - {e}")
    except ValueError:
        logger.error(f"Failed to parse JSON from {url}")
    return None
