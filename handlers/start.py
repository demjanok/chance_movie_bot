import logging
import config
from telegram import Update
from telegram.ext import ContextTypes

from locales import (
    SUPPORTED_LANGUAGES,
    get_user_language,
    get_message,
)
from keyboards import get_genres_keyboard, get_language_keyboard

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcomes the user and displays the genre selection keyboard in the user's language."""
    user = update.effective_user
    user_lang_code = user.language_code if user else None
    lang = get_user_language(context.user_data, user_lang_code)

    logger.info(
        "User started interaction (/start)",
        extra={
            "user_id": user.id if user else None,
            "username": user.username if user else None,
            "lang": lang,
        },
    )

    welcome_text = get_message("welcome", lang=lang, min_rating=config.MIN_RATING)
    keyboard = get_genres_keyboard(lang=lang)

    if update.message:
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    elif update.callback_query:
        # Returning to the main menu from an inline button
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays usage instructions and data source attribution in the user's language."""
    user = update.effective_user
    user_lang_code = user.language_code if user else None
    lang = get_user_language(context.user_data, user_lang_code)

    logger.info(
        "User requested /help",
        extra={
            "user_id": user.id if user else None,
            "lang": lang,
        },
    )

    help_text = get_message("help", lang=lang)
    if update.message:
        await update.message.reply_text(text=help_text, parse_mode="HTML")


async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompts the user to choose their preferred language via /language command."""
    user = update.effective_user
    user_lang_code = user.language_code if user else None
    lang = get_user_language(context.user_data, user_lang_code)

    logger.info(
        "User opened language menu via command",
        extra={
            "user_id": user.id if user else None,
            "lang": lang,
        },
    )

    text = get_message("choose_language", lang=lang)
    keyboard = get_language_keyboard(lang=lang)

    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def select_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the inline button click to open language selection menu."""
    query = update.callback_query
    await query.answer()

    user_lang_code = query.from_user.language_code if query.from_user else None
    lang = get_user_language(context.user_data, user_lang_code)

    logger.info(
        "User opened language menu via button",
        extra={
            "user_id": query.from_user.id if query.from_user else None,
            "lang": lang,
        },
    )

    text = get_message("choose_language", lang=lang)
    keyboard = get_language_keyboard(lang=lang)
    await query.message.reply_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Saves the user's language choice and displays the updated start menu."""
    query = update.callback_query
    data = query.data or ""
    # Expected format: "set_lang:<code"
    chosen_lang = None
    if ":" in data:
        _, lang_code = data.split(":", 1)
        if lang_code in SUPPORTED_LANGUAGES:
            context.user_data["language"] = lang_code
            chosen_lang = lang_code

    user_lang_code = query.from_user.language_code if query.from_user else None
    lang = get_user_language(context.user_data, user_lang_code)

    logger.info(
        "User changed language",
        extra={
            "user_id": query.from_user.id if query.from_user else None,
            "selected_lang": chosen_lang,
            "active_lang": lang,
        },
    )

    # Toast alert confirming language switch
    await query.answer(text=get_message("language_changed", lang=lang))

    # Send updated welcome menu in the new language
    welcome_text = get_message("welcome", lang=lang, min_rating=config.MIN_RATING)
    await query.message.reply_text(
        text=welcome_text,
        reply_markup=get_genres_keyboard(lang=lang),
        parse_mode="HTML",
    )
