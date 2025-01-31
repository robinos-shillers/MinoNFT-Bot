from bot import create_bot

if __name__ == "__main__":
    updater = create_bot()
    updater.start_polling()
    updater.idle()