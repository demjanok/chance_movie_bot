import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TELEGRAM_TOKEN="7785276339:AAGQNWvOrzNwxsR_W3yYIVS3ChVbQdFwQBY"


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm alive!😎")


def get_movie():
    API_KEY = "e655b7c1"
    title = "Inception"

    url = f"http://www.omdbapi.com/?t={title}&apikey={API_KEY}"

    response = requests.get(url)
    data = response.json()

    if data.get("imdbRating") and float(data["imdbRating"]) > 3.0:
        print(f"{data['Title']} ({data['Year']}) — IMDb: {data['imdbRating']}")
    else:
        print("Rating too low or movie not found.")



if __name__ == '__main__':
    get_movie()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("The bot has been launched...")
    app.run_polling()
