from telegram import Update
from telegram.ext import CallbackContext
from services.constants import INSTAGRAM_NICK, IN_REVIEW, APPROVE, REJECT, IMAGES
from services.instagram import handle_instagram_name
from handlers.submission import handle_approve, handle_reject
from config import ADMIN_TG_CHAT_ID, MEDIA_GROUP_TIMEOUT
from core.data_manager import DataManager

def handle_message(update: Update, context: CallbackContext):
    manager = DataManager(context, update)

    if manager.state == INSTAGRAM_NICK:
        return handle_instagram_name(manager)
    elif manager.state == IN_REVIEW:
        manager.message.reply_text("Your submission is being reviewed. Please wait.")
    elif manager.state == APPROVE:
        return handle_approve(manager)
    elif manager.state == REJECT:
        return handle_reject(manager)
    else:
        manager.message.reply_text("My apologies, something went wrong. Are you sure the data you sent is valid?")

def handle_image(update: Update, context):
    manager = DataManager(context, update)

    reply_message = __get_reply_message(manager.state)
    if reply_message != None:
        return manager.message.reply_text(reply_message)
    
    image = manager.message.photo[-1]
    manager.images.append(image.file_id)

    __run_job(manager)

def __run_job(manager: DataManager):
    # Start or restart the timer
    try:
        # If a job exists, remove it
        manager.context.job_queue.get_jobs_by_name(str(manager.user_id))[0].schedule_removal()
    except IndexError:
        pass  # No job exists yet, so we continue
        
    # Schedule the new job
    manager.context.job_queue.run_once(
        __check_media_group_completion,
        MEDIA_GROUP_TIMEOUT,
        context=manager.user_id,
        name=str(manager.user_id)
    )

def __get_reply_message(state):
    if state == IN_REVIEW:
        return "Your submission is being rewieved. Please wait."
    elif state != IMAGES:
        return "Looks like it is not image!"
    return None

def __check_media_group_completion(context: CallbackContext):
    user_id = context.job.context
    context.bot_data[user_id]["state"] = INSTAGRAM_NICK
    context.bot.send_message(chat_id=user_id, text="Thanks for the images! Please send your Instagram name now.")