import html
import logging
from collections import deque
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

import config
from locales import (
    DEFAULT_LANGUAGE,
    get_user_language,
    get_message,
)
from services.tmdb_service import tmdb_service, ANY_GENRE
from keyboards import get_movie_actions_keyboard, get_genres_keyboard

logger = logging.getLogger(__name__)


def format_movie_caption(movie: dict, lang: str = DEFAULT_LANGUAGE) -> str:
    """Formats the movie details card, ensuring it stays within Telegram's 1024-character caption limit."""
    untitled_fallback = get_message("caption_untitled", lang=lang)
    title = html.escape(movie.get("title") or untitled_fallback)
    orig_title = html.escape(movie.get("original_title") or "")
    release_date = movie.get("release_date") or ""
    unknown_year_fallback = get_message("caption_unknown_year", lang=lang)
    year = release_date[:4] if len(release_date) >= 4 else unknown_year_fallback

    rating = movie.get("vote_average", 0.0)
    vote_count = movie.get("vote_count", 0)

    # Genres
    genres_list = [g.get("name", "") for g in movie.get("genres", []) if g.get("name")]
    not_specified_fallback = get_message("caption_not_specified", lang=lang)
    genres_str = html.escape(", ".join(genres_list)) if genres_list else not_specified_fallback

    # Runtime
    runtime = movie.get("runtime")
    runtime_str = f"{get_message('caption_runtime', lang=lang, runtime=runtime)}\n" if runtime else ""

    header = f"🎬 <b>{title}</b> ({year})\n"
    if orig_title and orig_title.lower() != title.lower():
        header += f"<i>{orig_title}</i>\n"

    rating_str = get_message("caption_rating", lang=lang, rating=rating, vote_count=vote_count)
    genre_str = get_message("caption_genre", lang=lang, genres=genres_str)
    overview_title = get_message("caption_overview_title", lang=lang)

    info = (
        f"\n{rating_str}\n"
        f"{genre_str}\n"
        f"{runtime_str}"
        f"{overview_title}\n"
    )

    no_overview_fallback = get_message("caption_no_overview", lang=lang)
    overview = movie.get("overview") or no_overview_fallback
    overview = html.escape(overview.strip())

    # Telegram caption limit is 1024 characters; truncate if needed
    max_overview_len = 1000 - len(header) - len(info)
    if len(overview) > max_overview_len:
        overview = overview[:max_overview_len - 3] + "..."

    return f"{header}{info}{overview}"


async def movie_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles genre selection and 'Another movie' button clicks with multi-language support."""
    query = update.callback_query
    user_lang_code = query.from_user.language_code if query.from_user else None
    lang = get_user_language(context.user_data, user_lang_code)

    await query.answer(text=get_message("picking_movie", lang=lang))

    data = query.data or ""
    # Expected format: "genre:<id>" or "next:<id>"
    if ":" in data:
        _, genre_id = data.split(":", 1)
    else:
        genre_id = ANY_GENRE

    chat_id = query.message.chat_id

    # Display photo upload action in chat while fetching
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

    # Retrieve recently seen movie IDs for this user session to avoid duplicates.
    # Uses deque with maxlen for O(1) append/evict instead of list.pop(0).
    seen_movies: deque = context.user_data.setdefault(
        "seen_movies", deque(maxlen=config.SEEN_MOVIES_BUFFER_SIZE)
    )
    exclude_ids = set(seen_movies)

    movie = await tmdb_service.get_random_movie(
        genre_id=genre_id,
        exclude_ids=exclude_ids,
        lang=lang,
    )

    if not movie:
        if not tmdb_service.api_key:
            error_msg = get_message("error_no_key", lang=lang)
        else:
            error_msg = get_message("error_not_found", lang=lang)

        await query.message.reply_text(
            text=error_msg,
            reply_markup=get_genres_keyboard(lang=lang),
            parse_mode="HTML",
        )
        return

    # Record the shown movie ID in the user's recent buffer (deque auto-evicts oldest)
    movie_id = movie.get("id")
    if movie_id:
        seen_movies.append(movie_id)

    caption = format_movie_caption(movie, lang=lang)
    keyboard = get_movie_actions_keyboard(
        genre_id=genre_id,
        trailer_url=movie.get("trailer_url"),
        lang=lang,
    )

    poster_url = movie.get("poster_url")
    if poster_url:
        try:
            await query.message.reply_photo(
                photo=poster_url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return
        except Exception as e:
            logger.warning(f"Failed to send poster photo {poster_url}: {e}")

    # Fallback: if poster is missing or failed to upload
    await query.message.reply_text(
        text=caption,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def menu_genres_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Returns to the genre selection menu in the user's language."""
    query = update.callback_query
    user_lang_code = query.from_user.language_code if query.from_user else None
    lang = get_user_language(context.user_data, user_lang_code)

    await query.answer()
    await query.message.reply_text(
        text=get_message("choose_new_genre", lang=lang),
        reply_markup=get_genres_keyboard(lang=lang),
    )
