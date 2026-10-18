import asyncio
import random
import logging
import time
from typing import Optional, Dict, Any
import httpx

import config
from locales import (
    TMDB_LANGUAGE_CODES,
    DEFAULT_LANGUAGE,
    POPULAR_GENRES as ALL_POPULAR_GENRES,
    get_message,
)

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# Sentinel value for "any genre" selection
ANY_GENRE = "any"

# Default genres dictionary (Ukrainian fallback for backward compatibility)
POPULAR_GENRES = ALL_POPULAR_GENRES["uk"]


class TMDBService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Persistent HTTP client — reuses TCP connections across requests
        self._client: Optional[httpx.AsyncClient] = None
        # In-memory cache: { cache_key: (results_list, timestamp) }
        self._discover_cache: Dict[str, tuple[list, float]] = {}

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

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns the shared persistent AsyncClient, creating it if needed."""
        if self._client is None or self._client.is_closed:
            _, headers = self._get_auth_params_and_headers()
            self._client = httpx.AsyncClient(headers=headers, timeout=10.0)
        return self._client

    async def close(self) -> None:
        """Gracefully closes the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _get_cached_page(self, cache_key: str) -> Optional[list]:
        """Returns cached discover results if still within TTL, otherwise None."""
        entry = self._discover_cache.get(cache_key)
        if entry and (time.monotonic() - entry[1]) < config.DISCOVER_CACHE_TTL:
            return entry[0]
        return None

    def _set_cached_page(self, cache_key: str, results: list) -> None:
        """Stores discover results in the in-memory cache."""
        self._discover_cache[cache_key] = (results, time.monotonic())

    async def _fetch_discover_page(
        self,
        client: httpx.AsyncClient,
        base_params: dict,
        page: int,
        lang: str = DEFAULT_LANGUAGE,
    ) -> list:
        """
        Fetches a single discover page, using the in-memory cache when available.
        Includes language in the cache key to avoid mixing localized data.
        """
        genre_id = base_params.get("with_genres", ANY_GENRE)
        cache_key = f"{lang}:{genre_id}:{page}"

        cached = self._get_cached_page(cache_key)
        if cached is not None:
            logger.debug(
                "Cache hit for discover page",
                extra={"page": page, "genre_id": genre_id, "lang": lang},
            )
            return cached

        params = {**base_params, "page": page}
        response = await client.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        self._set_cached_page(cache_key, results)
        return results

    async def get_random_movie(
        self,
        genre_id: Optional[str] = None,
        exclude_ids: Optional[set[int]] = None,
        min_rating: float = config.MIN_RATING,
        min_votes: int = config.MIN_VOTES,
        lang: str = DEFAULT_LANGUAGE,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches a random quality movie filtered by genre, rating, and language,
        avoiding movies listed in exclude_ids when possible.
        """
        if not self.api_key:
            logger.error("TMDB_API_KEY is not configured!")
            return None

        if exclude_ids is None:
            exclude_ids = set()

        auth_params, _ = self._get_auth_params_and_headers()
        tmdb_lang = TMDB_LANGUAGE_CODES.get(lang, "uk-UA")

        base_params: dict = {
            **auth_params,
            "language": tmdb_lang,
            "sort_by": "popularity.desc",
            "vote_average.gte": min_rating,
            "vote_count.gte": min_votes,
            "include_adult": "false",
        }

        if genre_id and genre_id != ANY_GENRE:
            base_params["with_genres"] = genre_id

        client = await self._get_client()

        try:
            # 1. Fetch page 1 to determine total available pages (may come from cache)
            first_page_results = await self._fetch_discover_page(
                client, base_params, page=1, lang=lang
            )

            # Peek at total_pages via a fresh request only if page 1 metadata is not cached
            total_pages = await self._get_total_pages(client, base_params, lang=lang)

            if total_pages == 0 or not first_page_results:
                return None

            # Limit discovery pool to configured maximum
            max_page = min(total_pages, config.MAX_DISCOVERY_PAGES)
            pages_to_try = random.sample(range(1, max_page + 1), k=min(3, max_page))

            # 2. Fetch all selected pages concurrently
            page_results_list: list[list] = await asyncio.gather(
                *[self._fetch_discover_page(client, base_params, p, lang=lang) for p in pages_to_try]
            )

            chosen_movie = None
            for page_results in page_results_list:
                unseen = [m for m in page_results if m.get("id") not in exclude_ids]
                if unseen:
                    chosen_movie = random.choice(unseen)
                    break

            # Fallback: all sampled movies already seen — pick any from the first page
            if not chosen_movie:
                if not first_page_results:
                    return None
                chosen_movie = random.choice(first_page_results)

            movie_id = chosen_movie["id"]

            # 3. Retrieve detailed movie metadata (runtime, videos/trailers, description)
            return await self.get_movie_details(client, movie_id, lang=lang)

        except httpx.HTTPError as e:
            logger.error(
                "Error querying TMDB discover API",
                exc_info=True,
                extra={"genre_id": genre_id, "lang": lang, "error": str(e)},
            )
            return None

    async def _get_total_pages(
        self,
        client: httpx.AsyncClient,
        base_params: dict,
        lang: str = DEFAULT_LANGUAGE,
    ) -> int:
        """
        Returns total_pages for a discover query.
        Uses a cached response for page 1 if available, otherwise fetches it.
        """
        genre_id = base_params.get("with_genres", ANY_GENRE)
        cache_key = f"{lang}:{genre_id}:meta"
        cached = self._discover_cache.get(cache_key)
        if cached and (time.monotonic() - cached[1]) < config.DISCOVER_CACHE_TTL:
            return cached[0]  # type: ignore[return-value]

        params = {**base_params, "page": 1}
        response = await client.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
        response.raise_for_status()
        data = response.json()
        total_pages = data.get("total_pages", 0)

        # Also cache page 1 results while we're at it
        p1_key = f"{lang}:{genre_id}:1"
        if p1_key not in self._discover_cache:
            self._set_cached_page(p1_key, data.get("results", []))

        # Cache total_pages separately
        self._discover_cache[cache_key] = (total_pages, time.monotonic())
        return total_pages

    async def get_movie_details(
        self,
        client: httpx.AsyncClient,
        movie_id: int,
        lang: str = DEFAULT_LANGUAGE,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information for a movie (runtime, trailer, overview).
        For Ukrainian, fetches UK and EN metadata concurrently and falls back to EN overview
        when the Ukrainian one is absent.
        For English, fetches EN metadata directly.
        """
        auth_params, _ = self._get_auth_params_and_headers()

        try:
            if lang == "en":
                en_params = {
                    **auth_params,
                    "language": "en-US",
                    "append_to_response": "videos",
                }
                en_resp = await client.get(f"{TMDB_BASE_URL}/movie/{movie_id}", params=en_params)
                en_resp.raise_for_status()
                data = en_resp.json()

                if not data.get("overview"):
                    data["overview"] = get_message("caption_no_overview", lang=lang)

            else:
                uk_params = {
                    **auth_params,
                    "language": "uk-UA",
                    "append_to_response": "videos",
                }
                en_params = {
                    **auth_params,
                    "language": "en-US",
                    "append_to_response": "videos",
                }

                # Fetch UK and EN metadata in parallel to avoid sequential round-trips
                uk_resp, en_resp = await asyncio.gather(
                    client.get(f"{TMDB_BASE_URL}/movie/{movie_id}", params=uk_params),
                    client.get(f"{TMDB_BASE_URL}/movie/{movie_id}", params=en_params),
                )
                uk_resp.raise_for_status()
                data = uk_resp.json()

                # Use English overview only when Ukrainian one is absent
                if not data.get("overview") and en_resp.status_code == 200:
                    en_data = en_resp.json()
                    data["overview"] = en_data.get("overview", "")

                    # Prefer English videos if Ukrainian response has none
                    if not data.get("videos", {}).get("results") and en_data.get("videos", {}).get("results"):
                        data["videos"] = en_data["videos"]

                if not data.get("overview"):
                    data["overview"] = get_message("caption_no_overview", lang=lang)

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
            logger.error(
                "Error fetching details for movie",
                exc_info=True,
                extra={"movie_id": movie_id, "lang": lang, "error": str(e)},
            )
            return None


tmdb_service = TMDBService(api_key=config.TMDB_API_KEY)
