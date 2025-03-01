from services.downloader import save_telegram_images
from services.imgur import upload_to_imgur, delete_from_imgur
from config import MY_TG_CHAT_ID
from services.publisher import publish_single_image, publish_carousel
from telegram.ext import CallbackContext
from services.utils import handle_error

def make_post(context: CallbackContext, description):
    try:
        saved_image_paths = save_telegram_images(context)
        res = upload_to_imgur(saved_image_paths)

        if not res["success"]:
            context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"Error uploading to Imgur: {res['message']}")
            return False

        post_success_message = make_instagram_post(res["imgur_links"], description)

        # delete imgur images after posting
        delete_from_imgur(res["deletehash"])

        if post_success_message != None:
            context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=post_success_message)
            return False
        
        return True
    except Exception as e:
        context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"An error occurred during the posting process: {str(e)}")
        handle_error(f"Error during the posting process: {str(e)}")
        if "deletehash" in res:
            delete_from_imgur(res["deletehash"])
        return False

def make_instagram_post(img_links, description):
    try:
        if len(img_links) == 1:
            return publish_single_image(img_links, description)
        else: 
            return publish_carousel(img_links, description)
    except Exception as e:
        return handle_error(f"Error during Instagram post creation: {str(e)}")