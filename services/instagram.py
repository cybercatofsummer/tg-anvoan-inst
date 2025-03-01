import json
from telegram import Update, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from services.utils import IN_REVIEW, APPROVE, REJECT
from config import MY_TG_CHAT_ID

def handle_instagram_name(update: Update, context: CallbackContext):
    instagram_name = update.message.text
    user = update.message.from_user

    context.bot_data[user.id]["instagram_name"] = instagram_name
    context.bot_data[user.id]["state"] = IN_REVIEW
    update.message.reply_text("Thank you! Please wait until your submission is processed.")
    __process_images(context, user.id)


def __process_images(context, user_id):
    images = context.bot_data[user_id]["images"]
    instagram_name = context.bot_data[user_id]["instagram_name"]
    username = context.bot_data[user_id]["username"]

    approve_data = json.dumps({"action": APPROVE, "user_id": user_id})
    reject_data = json.dumps({"action": REJECT, "user_id": user_id})


    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Approve", callback_data=approve_data),
         InlineKeyboardButton("Reject", callback_data=reject_data)]
    ])

    media = [InputMediaPhoto(file_id) for file_id in images]
    sent_images_to_admin = context.bot.send_media_group(chat_id=MY_TG_CHAT_ID, media=media)
    sent_instagram_name = context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"Submission from: {username};\nInstagram name: {instagram_name}", reply_markup=keyboard)

    message_ids_to_delete = [message.message_id for message in sent_images_to_admin]
    message_ids_to_delete.append(sent_instagram_name.message_id)

    context.bot_data[user_id]["message_ids_to_delete"] = message_ids_to_delete
