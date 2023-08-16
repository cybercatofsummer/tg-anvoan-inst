from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackQueryHandler, CallbackContext
from telegram.error import TelegramError
import traceback
import logging
import os
import json
from dotenv import load_dotenv

load_dotenv()

MEDIA_GROUP_TIMEOUT = 1
MY_TG_CHAT_ID = os.getenv('MY_TG_CHAT_ID')
BOT_TOKEN = os.getenv('BOT_TOKEN')

IMAGES, INSTAGRAM_NICK, IN_REVIEW, APPROVE, REJECT = range(5)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

logger = logging.getLogger(__name__)

def start(update: Update, context):
    user = update.message.from_user
    if user.id not in context.bot_data and not is_my_chat_id(update.message.chat_id):
        context.bot_data[user.id] = {
            "images": [],
            "username": user.username,
            "chat_id": update.message.chat_id,
            "state": IMAGES
        }

    start_message = "Wait for users\' submissions" if is_my_chat_id(update.message.chat_id) else "Send me your image!"
    update.message.reply_text(start_message)

def handle_message(update: Update, context):
    
    user = update.message.from_user
    user_id = user.id
    data = context.user_data if is_my_chat_id(update.message.chat_id) else context.bot_data[user_id]
    state = data["state"]

    if state == IMAGES:
        return handle_image(update, context)
    elif state == INSTAGRAM_NICK:
        return handle_instagram_name(update, context)
    elif state == IN_REVIEW:
        update.message.reply_text("Your submission is being rewieved. Please wait.")
    elif state == APPROVE:
        return handle_approve(update, context)
    elif state == REJECT:
        return handle_reject(update, context)
    else: update.message.reply_text("My appologies, something went wrong.")


def is_my_chat_id(chat_id):
    return str(chat_id) == MY_TG_CHAT_ID

def handle_image(update: Update, context):
    user = update.message.from_user
    image = update.message.photo[-1]
    user_id = user.id

    context.bot_data[user_id]["images"].append(image.file_id)

    # Start or restart the timer
    try:
        # If a job exists, remove it
        context.job_queue.get_jobs_by_name(str(user_id))[0].schedule_removal()
    except IndexError:
        pass  # No job exists yet, so we continue
        
    # Schedule the new job
    context.job_queue.run_once(
        check_media_group_completion,
        MEDIA_GROUP_TIMEOUT,
        context=user_id,
        name=str(user_id)
    )

def check_media_group_completion(context: CallbackContext):
    user_id = context.job.context
    context.bot_data[user_id]["state"] = INSTAGRAM_NICK
    context.bot.send_message(chat_id=user_id, text="Thanks for the images! Please send your Instagram name now.")

def handle_instagram_name(update: Update, context: CallbackContext):
    instagram_name = update.message.text
    user = update.message.from_user

    context.bot_data[user.id]["instagram_name"] = instagram_name
    context.bot_data[user.id]["state"] = IN_REVIEW
    update.message.reply_text("Thank you! Please wait until your submission is processed.")
    process_images(context, user.id)


def process_images(context, user_id):
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

def handle_callback(update: Update, context):
    logger.debug("handle_callback triggered!")
    query = update.callback_query
    query.answer() # This ends the loading state on the button

    data = json.loads(query.data)
    action = data['action']
    context.user_data['proceeded_user_id'] = data['user_id']

    handle_action(action, query, context)

def handle_action(action, query, context):
    message = "post description" if action == APPROVE else "rejection reason"
    query.message.reply_text(f"Please enter the {message}:")
    context.user_data['state'] = APPROVE if action == APPROVE else REJECT

def handle_reject(update: Update, context):
    rejection_reason = update.message.text
    user_id = context.user_data['proceeded_user_id']
    user_chat_id = context.bot_data[user_id]['chat_id']
    username = context.bot_data[user_id]['username']

    delete_messages(context)

    # Notify yourself that the rejection was completed
    context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"Submission from {username} rejected for reason: {rejection_reason}")

    # Notify the user that their submission was rejected
    context.bot.send_message(chat_id=user_chat_id, text=f"Your submission was rejected for the following reason: {rejection_reason}\n Please, try again! Send images:")
    
    context.user_data['state'] = None

def handle_approve(update: Update, context):
    description = update.message.text
    user_id = context.user_data['proceeded_user_id']
    user_chat_id = context.bot_data[user_id]['chat_id']

    delete_messages(context)
    # Notify the user that their submission was rejected
    context.bot.send_message(chat_id=user_chat_id, text=f"Your submission was approved and will be posted on Instagram with the following description: {description}")

    context.user_data['state'] = None

def delete_messages(context):
    user_id = context.user_data['proceeded_user_id']
    for message_id in context.bot_data[user_id]['message_ids_to_delete']:
        try:
            context.bot.delete_message(chat_id=MY_TG_CHAT_ID, message_id=message_id)
        except TelegramError as e:
            logger.error(f"Error deleting message with ID {message_id}: {e}")

    context.bot_data[user_id]['message_ids_to_delete'] = []
    context.bot_data[user_id]['images'] = []
    context.bot_data[user_id]['state'] = IMAGES

def error_callback(update: Update, context: CallbackContext):
    error_message = str(context.error)
    traceback_message = traceback.format_exc()
    context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"An error occurred: {error_message}\n{traceback_message}")
    logger.error("Global error handler: %s\n%s", error_message, traceback_message)

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler((Filters.text & ~Filters.command) | Filters.photo, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    dp.add_error_handler(error_callback)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()