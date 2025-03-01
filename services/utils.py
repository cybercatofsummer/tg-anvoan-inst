import logging
from config import MY_TG_CHAT_ID
from telegram.error import TelegramError
from telegram.ext import CallbackContext

IMAGES, INSTAGRAM_NICK, IN_REVIEW, APPROVE, REJECT = range(5)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

def handle_error(message):
    """Logs and returns an error message."""
    logger.error(message)
    return message

def delete_messages(context: CallbackContext):
    user_id = context.user_data['proceeded_user_id']
    for message_id in context.bot_data[user_id]['message_ids_to_delete']:
        try:
            context.bot.delete_message(chat_id=MY_TG_CHAT_ID, message_id=message_id)
        except TelegramError as e:
            logger.error(f"Error deleting message with ID {message_id}: {e}")

    context.bot_data[user_id]['message_ids_to_delete'] = []
    context.bot_data[user_id]['images'] = []
    context.bot_data[user_id]['state'] = IMAGES

def is_my_chat_id(chat_id):
    return str(chat_id) == MY_TG_CHAT_ID
