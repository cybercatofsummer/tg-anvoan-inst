import json
from services.post import make_post
from services.utils import delete_messages
from config import ADMIN_TG_CHAT_ID
from core.data_manager import DataManager
from services.constants import IMAGES

def handle_reject(manager: DataManager):
    __handle_action(
        manager,
        f"Submission from {manager.username} rejected for reason: {manager.message.text}",
        f"Your submission was rejected for the following reason: {manager.message.text}\n Please, try again! Send images:"
    )

def handle_approve(manager: DataManager):
    description = __make_description(manager.message.text)
    
    post_result = make_post(manager, description)
    if (not post_result):
        manager.state = IMAGES
        return
    
    __handle_action(
        manager,
        f"Posted with the following description: {description}",
        f"Your submission was approved and will be posted on Instagram with the following description: {description}\n\nSend new images:"
    )

def __handle_action(manager, admin_message, user_message): 
    delete_messages(manager)
    __send_notifications(manager, admin_message, user_message)
    manager.state = IMAGES

def __send_notifications(manager: DataManager, admin_message, user_message):
    # Notify yourself
    manager.bot.send_message(chat_id=ADMIN_TG_CHAT_ID, text=admin_message)
    # Notify the user
    manager.bot.send_message(chat_id=manager.chat_id, text=user_message)

def __make_description(instagram_user_name):
    hashtags = [
        "#AnimeArt", "#AnimeDrawing", "#AnimeIllustration", "#MangaArt", "#OtakuArt",
        "#AnimeSketch", "#AnimeInk", "#KawaiiDrawings", "#ChibiArt", "#AnimeFanArt",
        "#AnimeStyle", "#DigitalAnime", "#TraditionalAnime", "#AnimeCreators", "#AnimeArtist",
        "#AnimeDaily", "#MangaSketch", "#AnimeGallery", "#AnimeCommunity", "#AnimeLove",
        "#Anime", "#AnimeArt", "#Draw", "#Drawings", "#Paintings", "#Anvoan",
    ]
    return f"Thanks @{instagram_user_name} for such adorable work!\n{' '.join(hashtags)}"