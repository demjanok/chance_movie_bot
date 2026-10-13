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

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    # У Python 3.14+ asyncio.get_event_loop() більше не створює цикл автоматично
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error(
            "Помилка: TELEGRAM_BOT_TOKEN не заданий у файлі .env!\n"
            "Створіть файл .env на основі .env.example та додайте ваш токен."
        )
        sys.exit(1)

    if not config.TMDB_API_KEY:
        logger.warning(
            "Увага: TMDB_API_KEY не заданий у .env. Пошук фільмів не працюватиме "
            "доти, доки ви не додасте API ключ."
        )

    # Ініціалізація бота
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Реєстрація команд
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))

    # Реєстрація callback-кнопок
    app.add_handler(CallbackQueryHandler(menu_genres_callback, pattern="^menu_genres$"))
    app.add_handler(CallbackQueryHandler(movie_callback_handler, pattern="^(genre|next):"))

    logger.info("🎬 Бот успішно запущений і готовий до роботи...")
    app.run_polling()


if __name__ == "__main__":
    main()
