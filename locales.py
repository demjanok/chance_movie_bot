"""
Localization module providing multi-language support (Ukrainian and English).
"""

from typing import Dict, Any, Optional

import config

SUPPORTED_LANGUAGES = {
    "uk": "🇺🇦 Українська",
    "en": "🇬🇧 English",
}

DEFAULT_LANGUAGE = getattr(config, "DEFAULT_LANGUAGE", "uk") or "uk"
if DEFAULT_LANGUAGE not in SUPPORTED_LANGUAGES:
    DEFAULT_LANGUAGE = "uk"

# Mapping from internal language code to TMDB API language parameter
TMDB_LANGUAGE_CODES = {
    "uk": "uk-UA",
    "en": "en-US",
}

# Popular genres for each supported language
POPULAR_GENRES: Dict[str, Dict[str, str]] = {
    "uk": {
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
    },
    "en": {
        "35": "🎭 Comedy",
        "28": "🍿 Action",
        "878": "🚀 Sci-Fi",
        "53": "🔪 Thriller",
        "18": "🎭 Drama",
        "27": "😱 Horror",
        "16": "🎨 Animation",
        "9648": "🔍 Mystery",
        "10749": "💖 Romance",
        "14": "🧙 Fantasy",
        "80": "🚓 Crime",
    },
}

MESSAGES: Dict[str, Dict[str, str]] = {
    "uk": {
        "welcome": (
            "👋 <b>Привіт! Я твій гід по кіно на вечір.</b>\n\n"
            "Я підбираю тільки перевірені фільми з високим рейтингом (⭐ від {min_rating}).\n\n"
            "Обери жанр, який тобі до душі, або довірся рандому:"
        ),
        "help": (
            "🎬 <b>Як користуватися ботом:</b>\n\n"
            "1. Натисни /start або обери жанр зі списку.\n"
            "2. Бот обере для тебе фільм з високим рейтингом.\n"
            "3. Натискай «🔄 Інший фільм», доки не знайдеш ідеальний варіант.\n"
            "4. За потреби тисни «▶️ Трейлер», щоб глянути ролик на YouTube.\n\n"
            "🌐 <b>Зміна мови:</b> команда /language або кнопка «🌐 Мова / Language» в меню.\n\n"
            "<i>Дані надані сервісом The Movie Database (TMDB).</i>"
        ),
        "choose_language": "🌐 <b>Оберіть мову / Choose language:</b>",
        "language_changed": "🇺🇦 Мову змінено на українську!",
        "picking_movie": "🔍 Підбираю фільм...",
        "error_unhandled": "⚠️ Щось пішло не так. Спробуйте ще раз.",
        "error_no_key": (
            "⚠️ <b>TMDB_API_KEY не налаштовано!</b>\n\n"
            "Будь ласка, вкажіть ваш API ключ у файлі <code>.env</code>."
        ),
        "error_not_found": (
            "😔 На жаль, не вдалося знайти фільм за обраними критеріями. "
            "Спробуйте інший жанр!"
        ),
        "choose_new_genre": "Обери новий жанр для пошуку фільму:",
        "btn_any_genre": "🎲 Будь-який жанр",
        "btn_next_movie": "🔄 Інший фільм",
        "btn_trailer": "▶️ Трейлер",
        "btn_change_genre": "🔙 Обрати інший жанр",
        "btn_change_lang": "🌐 Мова / Language",
        "btn_back": "🔙 Назад",
        "caption_untitled": "Без назви",
        "caption_unknown_year": "Рік невідомий",
        "caption_not_specified": "Не вказано",
        "caption_rating": "⭐ <b>Рейтинг:</b> {rating:.1f}/10 ({vote_count} голосів)",
        "caption_genre": "🎭 <b>Жанр:</b> {genres}",
        "caption_runtime": "⏱ <b>Тривалість:</b> {runtime} хв.",
        "caption_overview_title": "📖 <b>Опис:</b>",
        "caption_no_overview": "Опис відсутній.",
    },
    "en": {
        "welcome": (
            "👋 <b>Hello! I am your movie guide for tonight.</b>\n\n"
            "I only pick top-rated movies (⭐ {min_rating}+ rating).\n\n"
            "Choose a genre you like, or trust random selection:"
        ),
        "help": (
            "🎬 <b>How to use the bot:</b>\n\n"
            "1. Press /start or pick a genre from the list.\n"
            "2. The bot will pick a high-rated movie for you.\n"
            "3. Tap '🔄 Another movie' until you find your match.\n"
            "4. If available, tap '▶️ Trailer' to watch it on YouTube.\n\n"
            "🌐 <b>Change language:</b> /language command or the '🌐 Language / Мова' button.\n\n"
            "<i>Data provided by The Movie Database (TMDB).</i>"
        ),
        "choose_language": "🌐 <b>Choose your language / Оберіть мову:</b>",
        "language_changed": "🇬🇧 Language switched to English!",
        "picking_movie": "🔍 Picking a movie...",
        "error_unhandled": "⚠️ Something went wrong. Please try again.",
        "error_no_key": (
            "⚠️ <b>TMDB_API_KEY is not configured!</b>\n\n"
            "Please specify your API key in the <code>.env</code> file."
        ),
        "error_not_found": (
            "😔 Unfortunately, no movie was found matching the selected criteria. "
            "Please try another genre!"
        ),
        "choose_new_genre": "Choose a new genre to find a movie:",
        "btn_any_genre": "🎲 Any genre",
        "btn_next_movie": "🔄 Another movie",
        "btn_trailer": "▶️ Trailer",
        "btn_change_genre": "🔙 Choose another genre",
        "btn_change_lang": "🌐 Language / Мова",
        "btn_back": "🔙 Back",
        "caption_untitled": "Untitled",
        "caption_unknown_year": "Year unknown",
        "caption_not_specified": "Not specified",
        "caption_rating": "⭐ <b>Rating:</b> {rating:.1f}/10 ({vote_count} votes)",
        "caption_genre": "🎭 <b>Genre:</b> {genres}",
        "caption_runtime": "⏱ <b>Runtime:</b> {runtime} min.",
        "caption_overview_title": "📖 <b>Overview:</b>",
        "caption_no_overview": "No overview available.",
    },
}


def get_user_language(user_data: Optional[Dict[str, Any]] = None, user_language_code: Optional[str] = None) -> str:
    """
    Resolves the effective language for a user.
    Checks user_data session first, falls back to the user's Telegram client language,
    and defaults to DEFAULT_LANGUAGE ('uk').
    """
    if user_data is not None:
        lang = user_data.get("language")
        if lang in SUPPORTED_LANGUAGES:
            return lang

    if user_language_code:
        code = user_language_code.lower().split("-")[0].split("_")[0]
        if code in SUPPORTED_LANGUAGES:
            if user_data is not None:
                user_data["language"] = code
            return code

    if user_data is not None:
        user_data["language"] = DEFAULT_LANGUAGE
    return DEFAULT_LANGUAGE


def get_message(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Retrieves a formatted localized string by key."""
    lang_dict = MESSAGES.get(lang, MESSAGES[DEFAULT_LANGUAGE])
    template = lang_dict.get(key, MESSAGES[DEFAULT_LANGUAGE].get(key, ""))
    if kwargs:
        return template.format(**kwargs)
    return template


def get_popular_genres(lang: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    """Returns the popular genres dictionary for the specified language."""
    return POPULAR_GENRES.get(lang, POPULAR_GENRES[DEFAULT_LANGUAGE])
