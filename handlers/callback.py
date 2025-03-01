import json
import traceback
from telegram import Update
from telegram.ext import CallbackContext
from services.utils import APPROVE, REJECT, logger
from config import MY_TG_CHAT_ID

def handle_callback(update: Update, context: CallbackContext):
    logger.debug("handle_callback triggered!")
    query = update.callback_query
    query.answer() # This ends the loading state on the button

    data = json.loads(query.data)
    action = data['action']
    context.user_data['proceeded_user_id'] = data['user_id']

    __handle_action(action, query, context)

def error_callback(update: Update, context: CallbackContext):
    error_message = str(context.error)
    traceback_message = traceback.format_exc()
    context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"An error occurred: {error_message}\n{traceback_message}")
    logger.error("Global error handler: %s\n%s", error_message, traceback_message)

def __handle_action(action, query, context: CallbackContext):
    message = "instagram name for post (without @)" if action == APPROVE else "rejection reason"
    query.message.reply_text(f"Please enter the {message}:")
    context.user_data['state'] = APPROVE if action == APPROVE else REJECT