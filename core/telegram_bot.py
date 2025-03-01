from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from config import BOT_TOKEN
from handlers.commands import start, help
from handlers.message import handle_message, handle_image
from handlers.callback import handle_callback, error_callback


class TelegramBot:
    def __init__(self):
        updater = Updater(BOT_TOKEN)
        self.dp = updater.dispatcher

    def register_handlers(self):
        self.dp.add_handler(CommandHandler('start', start))
        self.dp.add_handler(CommandHandler('help', help))
        self.dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        self.dp.add_handler(MessageHandler(Filters.photo, handle_image))
        self.dp.add_handler(CallbackQueryHandler(handle_callback))
        self.dp.add_error_handler(error_callback)

    def run(self):
        updater.start_polling()
        updater.idle()
