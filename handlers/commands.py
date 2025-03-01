from telegram import Update
from telegram.ext import CallbackContext
from services.utils import IMAGES, is_my_chat_id

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    if user.id not in context.bot_data and not is_my_chat_id(update.message.chat_id):
        context.bot_data[user.id] = {
            "images": [],
            "username": user.username,
            "chat_id": update.message.chat_id,
            "state": IMAGES
        }

    start_message = "Wait for users\' submissions" if is_my_chat_id(update.message.chat_id) else (__bot_description() + "\n\n Send me your images:")
    update.message.reply_text(start_message)

def help(update: Update, context):
    update.message.reply_text(__bot_description())

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