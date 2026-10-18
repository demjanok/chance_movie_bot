import sys
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

import config
from handlers.start import start_handler, help_handler
from handlers.movies import movie_callback_handler, menu_genres_callback
from services.tmdb_service import tmdb_service

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler — logs unhandled exceptions and notifies the user
    via an alert so they are never left with a spinner or silence.
    """
    logger.error("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.callback_query:
        try:
            await update.callback_query.answer(
                "⚠️ Щось пішло не так. Спробуйте ще раз.",
                show_alert=True,
            )
        except Exception:
            pass  # Ignore secondary errors inside the error handler


def main() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error(
            "Error: TELEGRAM_BOT_TOKEN is not set in .env!\n"
            "Create a .env file from .env.example and provide your bot token."
        )
        sys.exit(1)

    if not config.TMDB_API_KEY:
        logger.warning(
            "Warning: TMDB_API_KEY is not set in .env. Movie discovery will fail "
            "until an API key is provided."
        )

    # Initialize bot application
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))

    # Register callback query handlers
    app.add_handler(CallbackQueryHandler(menu_genres_callback, pattern="^menu_genres$"))
    app.add_handler(CallbackQueryHandler(movie_callback_handler, pattern="^(genre|next):"))

    # Register global error handler
    app.add_error_handler(error_handler)

    logger.info("🎬 Bot launched and ready for requests...")

    async def on_shutdown(application) -> None:
        """Close the shared HTTP client on bot shutdown."""
        await tmdb_service.close()

    app.post_shutdown = on_shutdown

    app.run_polling()


if __name__ == "__main__":
    main()
