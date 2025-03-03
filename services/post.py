from services.downloader import save_telegram_images
from services.imgur import upload_to_imgur, delete_from_imgur
from config import ADMIN_TG_CHAT_ID
from services.publisher import publish_single_image, publish_carousel
from services.utils import handle_error
from core.data_manager import DataManager

def make_post(manager: DataManager, description):
    try:
        res = upload_to_imgur(save_telegram_images(manager))

        if not res["success"]:
            manager.bot.send_message(chat_id=ADMIN_TG_CHAT_ID, text=f"Error uploading to Imgur: {res['message']}")
            return False

        post_success_message = make_instagram_post(res["imgur_links"], description)

        # delete imgur images after posting
        delete_from_imgur(res["deletehash"])

        if post_success_message != None:
            manager.bot.send_message(chat_id=ADMIN_TG_CHAT_ID, text=post_success_message)
            return False
        
        return True
    except Exception as e:
        return __handle_exception(manager, e)

def make_instagram_post(img_links, description):
    try:
        return publish_single_image(img_links, description) if len(img_links) == 1 else publish_carousel(img_links, description)
    except Exception as e:
        return handle_error(f"Error during Instagram post creation: {str(e)}")

def __handle_exception(manager: DataManager, e: Exception):
    manager.bot.send_message(chat_id=ADMIN_TG_CHAT_ID, text=f"An error occurred during the posting process: {str(e)}")
    handle_error(f"Error during the posting process: {str(e)}")

    if "deletehash" in res:
        delete_from_imgur(res["deletehash"])
    return False