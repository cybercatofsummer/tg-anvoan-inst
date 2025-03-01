import json
from services.post import make_post
from services.utils import delete_messages
from telegram import Update
from telegram.ext import CallbackContext
from config import MY_TG_CHAT_ID


def handle_reject(update: Update, context: CallbackContext):
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
    description = __make_description(update.message.text)
    user_id = context.user_data['proceeded_user_id']
    user_chat_id = context.bot_data[user_id]['chat_id']
    
    post_result = make_post(context, description)
    if (not post_result):
        context.user_data['state'] = None
        return
    
    delete_messages(context)
    # Notify the user that their submission was rejected
    context.bot.send_message(chat_id=user_chat_id, text=f"Your submission was approved and will be posted on Instagram with the following description: {description}\n\nSend new images:")
    context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"Posted with the following description: {description}")

    context.user_data['state'] = None

def __make_description(instagram_user_name):
    hashtags = [
        "#AnimeArt", "#AnimeDrawing", "#AnimeIllustration", "#MangaArt", "#OtakuArt",
        "#AnimeSketch", "#AnimeInk", "#KawaiiDrawings", "#ChibiArt", "#AnimeFanArt",
        "#AnimeStyle", "#DigitalAnime", "#TraditionalAnime", "#AnimeCreators", "#AnimeArtist",
        "#AnimeDaily", "#MangaSketch", "#AnimeGallery", "#AnimeCommunity", "#AnimeLove",
        "#Anime", "#AnimeArt", "#Draw", "#Drawings", "#Paintings", "#Anvoan",
    ]
    return f"Thanks @{instagram_user_name} for such adorable work!\n{' '.join(hashtags)}"