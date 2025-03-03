from telegram import Update
from telegram.ext import CallbackContext
from services.constants import IMAGES
from core.data_manager import DataManager

def start(update: Update, context: CallbackContext):
    manager = DataManager(context, update)
    manager.message.reply_text(__start_message(manager))

def help(update: Update, context):
    manager.message.reply_text(__bot_description())

def __start_message(manager: DataManager):
    return "Wait for users\' submissions" if manager.is_admin_chat_id else (__bot_description() + "\n\n Send me your images:")

def __bot_description():
    # TODO: add language selection
    return (
        "🎨 Welcome to the Anvoan Drawings Bot! 🎨\n\n"
        "Here's how to use this bot:\n"
        "1️⃣ Send one or more images that you'd like to submit. If you send multiple images, they'll be grouped into a carousel post but no more than 10 images per 1 post.\n"
        "2️⃣ After sending your images, provide your Instagram username so we can credit you when the artwork is posted.\n"
        "3️⃣ Wait for a confirmation message. Your submission will be reviewed, and if approved, it will be posted on our Instagram page with your credit.\n\n"
        "📌 Note: Always ensure you have the rights to the images you're submitting. We respect and uphold copyright laws.\n"
        "📌 This bot is not for chatting. If you try to chat with it, you might break its functionality. If something goes wrong, use the /start command to restart the bot.\n\n"
        "For any other questions or issues, please reach out to our instagram. Happy submitting!\n\n"
    )