from typing import Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from locales import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    get_message,
    get_popular_genres,
)
from services.tmdb_service import ANY_GENRE


def get_genres_keyboard(lang: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Generates an inline keyboard grid with genre selection buttons."""
    keyboard = []
    row = []

    genres = get_popular_genres(lang)
    for genre_id, title in genres.items():
        row.append(InlineKeyboardButton(text=title, callback_data=f"genre:{genre_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Full-width button for random/any genre
    any_text = get_message("btn_any_genre", lang)
    keyboard.append([InlineKeyboardButton(text=any_text, callback_data=f"genre:{ANY_GENRE}")])

    # Language selection button
    lang_btn_text = get_message("btn_change_lang", lang)
    keyboard.append([InlineKeyboardButton(text=lang_btn_text, callback_data="select_language")])

    return InlineKeyboardMarkup(keyboard)


def get_movie_actions_keyboard(
    genre_id: str,
    trailer_url: Optional[str] = None,
    lang: str = DEFAULT_LANGUAGE,
) -> InlineKeyboardMarkup:
    """Generates action buttons displayed below a movie recommendation card."""
    action_row = [
        InlineKeyboardButton(text=get_message("btn_next_movie", lang), callback_data=f"next:{genre_id}")
    ]
    if trailer_url:
        action_row.append(InlineKeyboardButton(text=get_message("btn_trailer", lang), url=trailer_url))

    keyboard = [
        action_row,
        [InlineKeyboardButton(text=get_message("btn_change_genre", lang), callback_data="menu_genres")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_language_keyboard(lang: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Generates an inline keyboard for selecting the user interface language."""
    buttons = [
        InlineKeyboardButton(text=label, callback_data=f"set_lang:{code}")
        for code, label in SUPPORTED_LANGUAGES.items()
    ]
    # Two language buttons in a row
    keyboard = [
        buttons,
        [InlineKeyboardButton(text=get_message("btn_back", lang), callback_data="menu_genres")],
    ]
    return InlineKeyboardMarkup(keyboard)
