import sys
import asyncio
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

import config
from handlers.start import start_handler, help_handler
from handlers.movies import movie_callback_handler, menu_genres_callback

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    # In Python 3.14+, asyncio.get_event_loop() no longer implicitly creates a new loop in the main thread
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

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

    logger.info("🎬 Bot launched and ready for requests...")
    app.run_polling()


if __name__ == "__main__":
    main()
