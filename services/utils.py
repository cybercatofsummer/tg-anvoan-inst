import logging
from telegram import Update
from config import ADMIN_TG_CHAT_ID
from telegram.error import TelegramError
from core.data_manager import DataManager
from services.constants import IMAGES

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

def delete_messages(manager: DataManager):
    for message_id in manager.message_ids_to_delete:
        try:
            manager.bot.delete_message(chat_id=ADMIN_TG_CHAT_ID, message_id=message_id)
        except TelegramError as e:
            handle_error(f"Error deleting message with ID {message_id}: {e}")

    manager.message_ids_to_delete = []
    manager.images = []
    manager.state = IMAGES
