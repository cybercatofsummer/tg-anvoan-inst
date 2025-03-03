import json
import traceback
from telegram import Update
from telegram.ext import CallbackContext
from services.utils import  logger
from services.constants import APPROVE, REJECT
from config import ADMIN_TG_CHAT_ID
from core.data_manager import DataManager

def handle_callback(update: Update, context: CallbackContext):
    manager = DataManager(context, update, True)
    __handle_action(manager)

def error_callback(update: Update, context: CallbackContext):
    error_message = str(context.error)
    traceback_message = traceback.format_exc()
    context.bot.send_message(chat_id=ADMIN_TG_CHAT_ID, text=f"An error occurred: {error_message}\n{traceback_message}")
    logger.error("Global error handler: %s\n%s", error_message, traceback_message)

def __handle_action(manager: DataManager):
    message = "instagram name for post (without @)" if manager.action == APPROVE else "rejection reason"
    manager.query.message.reply_text(f"Please enter the {message}:")
    manager.user_data['state'] = APPROVE if manager.action == APPROVE else REJECT