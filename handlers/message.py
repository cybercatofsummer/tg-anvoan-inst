from telegram import Update
from telegram.ext import CallbackContext
from services.utils import INSTAGRAM_NICK, IN_REVIEW, APPROVE, REJECT, IMAGES, is_my_chat_id
from services.instagram import handle_instagram_name
from handlers.submission import handle_approve, handle_reject
from config import MY_TG_CHAT_ID, MEDIA_GROUP_TIMEOUT

def handle_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    data = context.user_data if is_my_chat_id(update.message.chat_id) else context.bot_data[user_id]
    state = data["state"]

    if state == INSTAGRAM_NICK:
        return handle_instagram_name(update, context)
    elif state == IN_REVIEW:
        update.message.reply_text("Your submission is being rewieved. Please wait.")
    elif state == APPROVE:
        return handle_approve(update, context)
    elif state == REJECT:
        return handle_reject(update, context)
    else: update.message.reply_text("My appologies, something went wrong. Are you sure the data you sent is valid?")

def handle_image(update: Update, context):
    user = update.message.from_user
    user_id = user.id

    if user.id not in context.bot_data and not is_my_chat_id(update.message.chat_id):
        context.bot_data[user.id] = {
            "images": [],
            "username": user.username,
            "chat_id": update.message.chat_id,
            "state": IMAGES
        }

    data = context.bot_data[user_id]
    state = data["state"]

    if state == IN_REVIEW:
        update.message.reply_text("Your submission is being rewieved. Please wait.")
        return
    elif state != IMAGES:
        update.message.reply_text("Looks like it is not image!")
        return
    
    image = update.message.photo[-1]
    context.bot_data[user_id]["images"].append(image.file_id)

    # Start or restart the timer
    try:
        # If a job exists, remove it
        context.job_queue.get_jobs_by_name(str(user_id))[0].schedule_removal()
    except IndexError:
        pass  # No job exists yet, so we continue
        
    # Schedule the new job
    context.job_queue.run_once(
        __check_media_group_completion,
        MEDIA_GROUP_TIMEOUT,
        context=user_id,
        name=str(user_id)
    )

def __check_media_group_completion(context: CallbackContext):
    user_id = context.job.context
    context.bot_data[user_id]["state"] = INSTAGRAM_NICK
    context.bot.send_message(chat_id=user_id, text="Thanks for the images! Please send your Instagram name now.")