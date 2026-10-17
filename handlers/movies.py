import html
import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

import config
from services.tmdb_service import tmdb_service
from keyboards import get_movie_actions_keyboard, get_genres_keyboard

logger = logging.getLogger(__name__)


def format_movie_caption(movie: dict) -> str:
    """Formats the movie details card, ensuring it stays within Telegram's 1024-character caption limit."""
    title = html.escape(movie.get("title") or "Без назви")
    orig_title = html.escape(movie.get("original_title") or "")
    release_date = movie.get("release_date") or ""
    year = release_date[:4] if len(release_date) >= 4 else "Рік невідомий"

    rating = movie.get("vote_average", 0.0)
    vote_count = movie.get("vote_count", 0)

    # Genres
    genres_list = [g.get("name", "") for g in movie.get("genres", []) if g.get("name")]
    genres_str = html.escape(", ".join(genres_list)) if genres_list else "Не вказано"

    # Runtime
    runtime = movie.get("runtime")
    runtime_str = f"⏱ <b>Тривалість:</b> {runtime} хв.\n" if runtime else ""

    header = f"🎬 <b>{title}</b> ({year})\n"
    if orig_title and orig_title.lower() != title.lower():
        header += f"<i>{orig_title}</i>\n"

    info = (
        f"\n⭐ <b>Рейтинг:</b> {rating:.1f}/10 ({vote_count} голосів)\n"
        f"🎭 <b>Жанр:</b> {genres_str}\n"
        f"{runtime_str}\n"
        f"📖 <b>Опис:</b>\n"
    )

    overview = movie.get("overview") or "Опис відсутній."
    overview = html.escape(overview.strip())

    # Telegram caption limit is 1024 characters; truncate if needed
    max_overview_len = 1000 - len(header) - len(info)
    if len(overview) > max_overview_len:
        overview = overview[:max_overview_len - 3] + "..."

    return f"{header}{info}{overview}"


async def movie_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles genre selection and 'Another movie' button clicks."""
    query = update.callback_query
    await query.answer(text="🔍 Підбираю фільм...")

    data = query.data
    # Expected format: "genre:<id>" or "next:<id>"
    if ":" in data:
        _, genre_id = data.split(":", 1)
    else:
        genre_id = "any"

    chat_id = query.message.chat_id

    # Display photo upload action in chat while fetching
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

    # Retrieve recently seen movie IDs for this user session to avoid duplicates
    seen_movies = context.user_data.setdefault("seen_movies", [])
    exclude_ids = set(seen_movies)

    movie = await tmdb_service.get_random_movie(genre_id=genre_id, exclude_ids=exclude_ids)

    if not movie:
        if not tmdb_service.api_key:
            error_msg = (
                "⚠️ <b>TMDB_API_KEY не налаштовано!</b>\n\n"
                "Будь ласка, вкажіть ваш API ключ у файлі <code>.env</code>."
            )
        else:
            error_msg = (
                "😔 На жаль, не вдалося знайти фільм за обраними критеріями. "
                "Спробуйте інший жанр!"
            )
        await query.message.reply_text(
            text=error_msg,
            reply_markup=get_genres_keyboard(),
            parse_mode="HTML",
        )
        return

    # Record the shown movie ID in the user's recent buffer
    movie_id = movie.get("id")
    if movie_id:
        seen_movies.append(movie_id)
        if len(seen_movies) > config.SEEN_MOVIES_BUFFER_SIZE:
            seen_movies.pop(0)

    caption = format_movie_caption(movie)
    keyboard = get_movie_actions_keyboard(
        genre_id=genre_id,
        trailer_url=movie.get("trailer_url"),
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
    """Returns to the genre selection menu."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        text="Обери новий жанр для пошуку фільму:",
        reply_markup=get_genres_keyboard(),
    )
