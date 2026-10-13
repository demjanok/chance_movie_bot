from typing import Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from services.tmdb_service import POPULAR_GENRES


def get_genres_keyboard() -> InlineKeyboardMarkup:
    """Генерує сітку кнопок з вибором жанрів."""
    keyboard = []
    row = []

    for genre_id, title in POPULAR_GENRES.items():
        if genre_id == "any":
            continue
        row.append(InlineKeyboardButton(text=title, callback_data=f"genre:{genre_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Кнопка для випадкового жанру на всю ширину
    keyboard.append([InlineKeyboardButton(text="🎲 Будь-який жанр", callback_data="genre:any")])

    return InlineKeyboardMarkup(keyboard)


def get_movie_actions_keyboard(genre_id: str, trailer_url: Optional[str] = None) -> InlineKeyboardMarkup:
    """Генерує кнопки дій під карткою фільму."""
    action_row = [
        InlineKeyboardButton(text="🔄 Інший фільм", callback_data=f"next:{genre_id}")
    ]
    if trailer_url:
        action_row.append(InlineKeyboardButton(text="▶️ Трейлер", url=trailer_url))

    keyboard = [
        action_row,
        [InlineKeyboardButton(text="🔙 Обрати інший жанр", callback_data="menu_genres")],
    ]
    return InlineKeyboardMarkup(keyboard)
