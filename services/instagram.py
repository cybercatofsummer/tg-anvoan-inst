import json
from telegram import Update, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from services.constants import IN_REVIEW, APPROVE, REJECT
from config import ADMIN_TG_CHAT_ID
from core.data_manager import DataManager

def handle_instagram_name(manager: DataManager):
    manager.instagram_name = manager.message.text
    manager.state = IN_REVIEW
    manager.message.reply_text("Thank you! Please wait until your submission is processed.")
    __process_images(manager)


def __process_images(manager: DataManager):
    keyboard = __create_buttons(manager)

    media = [InputMediaPhoto(file_id) for file_id in manager.images]
    sent_images_to_admin = manager.bot.send_media_group(chat_id=ADMIN_TG_CHAT_ID, media=media)
    sent_instagram_name = manager.bot.send_message(chat_id=ADMIN_TG_CHAT_ID, text=f"Submission from: {manager.username};\nInstagram name: {manager.instagram_name}", reply_markup=keyboard)

    manager.message_ids_to_delete = __message_ids_to_delete(sent_images_to_admin, sent_instagram_name)
    
def __message_ids_to_delete(sent_images_to_admin, sent_instagram_name):
    message_ids_to_delete = [message.message_id for message in sent_images_to_admin]
    message_ids_to_delete.append(sent_instagram_name.message_id)
    return message_ids_to_delete


def __create_buttons(manager: DataManager):
    approve_data = json.dumps({"action": APPROVE, "user_id": manager.user_id})
    reject_data = json.dumps({"action": REJECT, "user_id": manager.user_id})

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Approve", callback_data=approve_data),
         InlineKeyboardButton("Reject", callback_data=reject_data)]
    ])
