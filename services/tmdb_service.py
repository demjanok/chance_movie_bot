import random
import logging
from typing import Optional, Dict, Any
import httpx

import config

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# List of popular genres displayed in the Telegram bot menu
POPULAR_GENRES = {
    "35": "🎭 Комедія",
    "28": "🍿 Бойовик",
    "878": "🚀 Фантастика",
    "53": "🔪 Трилер",
    "18": "🎭 Драма",
    "27": "😱 Жахи",
    "16": "🎨 Мультфільм",
    "9648": "🔍 Детектив",
    "10749": "💖 Мелодрама",
    "14": "🧙 Фентезі",
    "80": "🚓 Кримінал",
    "any": "🎲 Будь-який жанр",
}


class TMDBService:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get_auth_params_and_headers(self) -> tuple[dict, dict]:
        """
        Supports both traditional API Key (v3) and Read Access Token (v4 Bearer JWT).
        """
        headers = {}
        params = {}
        if self.api_key.startswith("eyJ") or len(self.api_key) > 40:
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            params["api_key"] = self.api_key
        return params, headers

    async def get_random_movie(
        self,
        genre_id: Optional[str] = None,
        min_rating: float = config.MIN_RATING,
        min_votes: int = config.MIN_VOTES,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches a random quality movie filtered by genre and rating.
        """
        if not self.api_key:
            logger.error("TMDB_API_KEY is not configured!")
            return None

        auth_params, headers = self._get_auth_params_and_headers()

        async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
            params = {
                **auth_params,
                "language": config.TMDB_LANGUAGE,
                "sort_by": "popularity.desc",
                "vote_average.gte": min_rating,
                "vote_count.gte": min_votes,
                "include_adult": "false",
                "page": 1,
            }

            if genre_id and genre_id != "any":
                params["with_genres"] = genre_id

            try:
                # 1. Initial request to determine total available pages
                response = await client.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
                response.raise_for_status()
                data = response.json()

                total_pages = data.get("total_pages", 0)
                if total_pages == 0 or not data.get("results"):
                    return None

                # Limit discovery to the top configured pages (default: 15 pages = 300 movies pool)
                max_page = min(total_pages, config.MAX_DISCOVERY_PAGES)
                random_page = random.randint(1, max_page)

                # 2. If the selected random page is not page 1, fetch that page
                if random_page != 1:
                    params["page"] = random_page
                    response = await client.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
                    response.raise_for_status()
                    data = response.json()

                results = data.get("results", [])
                if not results:
                    return None

                chosen_movie = random.choice(results)
                movie_id = chosen_movie["id"]

                # 3. Retrieve detailed movie metadata (runtime, videos/trailers, description)
                return await self.get_movie_details(client, movie_id)

            except httpx.HTTPError as e:
                logger.error(f"Error querying TMDB discover API: {e}")
                return None

    async def get_movie_details(self, client: httpx.AsyncClient, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information for a movie (runtime, trailer, overview).
        """
        auth_params, _ = self._get_auth_params_and_headers()
        params = {
            **auth_params,
            "language": config.TMDB_LANGUAGE,
            "append_to_response": "videos",
        }
        try:
            response = await client.get(f"{TMDB_BASE_URL}/movie/{movie_id}", params=params)
            response.raise_for_status()
            data = response.json()

            # If Ukrainian overview is empty, fall back to English overview
            if not data.get("overview"):
                eng_params = {**auth_params, "language": "en-US"}
                eng_resp = await client.get(
                    f"{TMDB_BASE_URL}/movie/{movie_id}",
                    params=eng_params,
                )
                if eng_resp.status_code == 200:
                    eng_data = eng_resp.json()
                    data["overview"] = eng_data.get("overview", "Опис наразі відсутній.")

            # Search for YouTube trailer
            trailer_url = None
            videos = data.get("videos", {}).get("results", [])
            for v in videos:
                if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser"):
                    trailer_url = f"https://www.youtube.com/watch?v={v.get('key')}"
                    break

            data["trailer_url"] = trailer_url
            if data.get("poster_path"):
                data["poster_url"] = f"{TMDB_IMAGE_BASE}{data['poster_path']}"
            else:
                data["poster_url"] = None

            return data

        except httpx.HTTPError as e:
            logger.error(f"Error fetching details for movie {movie_id}: {e}")
            return None


tmdb_service = TMDBService(api_key=config.TMDB_API_KEY)
