from telegram import Update
from telegram.ext import ContextTypes

from keyboards import get_genres_keyboard


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Привітання користувача та показ клавіатури з жанрами."""
    welcome_text = (
        "👋 <b>Привіт! Я твій гід по кіно на вечір.</b>\n\n"
        "Я підбираю тільки перевірені фільми з високим рейтингом (⭐ від 7.0).\n\n"
        "Обери жанр, який тобі до душі, або довірся рандому:"
    )

    if update.message:
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=get_genres_keyboard(),
            parse_mode="HTML",
        )
    elif update.callback_query:
        # Якщо повертаємось у головне меню через інлайн-кнопку
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            text=welcome_text,
            reply_markup=get_genres_keyboard(),
            parse_mode="HTML",
        )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Підказка по використанню."""
    help_text = (
        "🎬 <b>Як користуватися ботом:</b>\n\n"
        "1. Натисни /start або обери жанр зі списку.\n"
        "2. Бот обере для тебе фільм з високим рейтингом.\n"
        "3. Натискай «🔄 Інший фільм», доки не знайдеш ідеальний варіант.\n"
        "4. За потреби тисни «▶️ Трейлер», щоб глянути ролик на YouTube."
    )
    if update.message:
        await update.message.reply_text(text=help_text, parse_mode="HTML")
