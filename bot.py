from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackQueryHandler, CallbackContext
from telegram.error import TelegramError
import traceback
import logging
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MEDIA_GROUP_TIMEOUT = 1
IMGUR_ENDPOINT = "https://api.imgur.com/3/upload"
IMGUR_DELETE_ENDPOINT = "https://api.imgur.com/3/image/{deletehash}"
IMGUR_CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')
MY_TG_CHAT_ID = os.getenv('MY_TG_CHAT_ID')
BOT_TOKEN = os.getenv('BOT_TOKEN')
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
INSTAGRAM_USER_ID = os.getenv('INSTAGRAM_USER_ID') 
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID') 
FACEBOOK_SECRET = os.getenv('FACEBOOK_SECRET') 

IMAGES, INSTAGRAM_NICK, IN_REVIEW, APPROVE, REJECT = range(5)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

logger = logging.getLogger(__name__)

def start(update: Update, context):
    user = update.message.from_user
    if user.id not in context.bot_data and not is_my_chat_id(update.message.chat_id):
        context.bot_data[user.id] = {
            "images": [],
            "username": user.username,
            "chat_id": update.message.chat_id,
            "state": IMAGES
        }

    start_message = "Wait for users\' submissions" if is_my_chat_id(update.message.chat_id) else (bot_description() + "\n\n Send me your images:")
    update.message.reply_text(start_message)

def help(update: Update, context):
    update.message.reply_text(bot_description())

def bot_description():
    return (
        "🎨 Welcome to the Anvoan Drawings Bot! 🎨\n\n"
        "Here's how to use this bot:\n"
        "1️⃣ Send one or more images that you'd like to submit. If you send multiple images, they'll be grouped into a carousel post but no more than 10 images per 1 post\n"
        "2️⃣ After sending your images, provide your Instagram username so we can credit you when the artwork is posted.\n"
        "3️⃣ Wait for a confirmation message. Your submission will be reviewed, and if approved, it will be posted on our Instagram page with your credit.\n\n"
        "📌 Note: Always ensure you have the rights to the images you're submitting. We respect and uphold copyright laws.\n"
        "📌 If something went wrong then restart bot by /start command.\n\n"
        "For any other questions or issues, please reach out to our support team. Happy submitting!"
    )

def handle_message(update: Update, context):
    
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


def is_my_chat_id(chat_id):
    return str(chat_id) == MY_TG_CHAT_ID

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

    if state != IMAGES:
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
        check_media_group_completion,
        MEDIA_GROUP_TIMEOUT,
        context=user_id,
        name=str(user_id)
    )

def check_media_group_completion(context: CallbackContext):
    user_id = context.job.context
    context.bot_data[user_id]["state"] = INSTAGRAM_NICK
    context.bot.send_message(chat_id=user_id, text="Thanks for the images! Please send your Instagram name now.")

def handle_instagram_name(update: Update, context: CallbackContext):
    instagram_name = update.message.text
    user = update.message.from_user

    context.bot_data[user.id]["instagram_name"] = instagram_name
    context.bot_data[user.id]["state"] = IN_REVIEW
    update.message.reply_text("Thank you! Please wait until your submission is processed.")
    process_images(context, user.id)


def process_images(context, user_id):
    images = context.bot_data[user_id]["images"]
    instagram_name = context.bot_data[user_id]["instagram_name"]
    username = context.bot_data[user_id]["username"]

    approve_data = json.dumps({"action": APPROVE, "user_id": user_id})
    reject_data = json.dumps({"action": REJECT, "user_id": user_id})


    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Approve", callback_data=approve_data),
         InlineKeyboardButton("Reject", callback_data=reject_data)]
    ])

    media = [InputMediaPhoto(file_id) for file_id in images]
    sent_images_to_admin = context.bot.send_media_group(chat_id=MY_TG_CHAT_ID, media=media)
    sent_instagram_name = context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"Submission from: {username};\nInstagram name: {instagram_name}", reply_markup=keyboard)

    message_ids_to_delete = [message.message_id for message in sent_images_to_admin]
    message_ids_to_delete.append(sent_instagram_name.message_id)

    context.bot_data[user_id]["message_ids_to_delete"] = message_ids_to_delete

def handle_callback(update: Update, context):
    logger.debug("handle_callback triggered!")
    query = update.callback_query
    query.answer() # This ends the loading state on the button

    data = json.loads(query.data)
    action = data['action']
    context.user_data['proceeded_user_id'] = data['user_id']

    handle_action(action, query, context)

def handle_action(action, query, context):
    message = "instagram name for post (without @)" if action == APPROVE else "rejection reason"
    query.message.reply_text(f"Please enter the {message}:")
    context.user_data['state'] = APPROVE if action == APPROVE else REJECT

def handle_reject(update: Update, context):
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

def make_description_test(instagram_user_name):
    return f"Thanks @{instagram_user_name} for such adorable work!\n#anime #animeart #draw #drawings #paintings #anvoan"

def handle_approve(update: Update, context):
    description = make_description_test(update.message.text)
    user_id = context.user_data['proceeded_user_id']
    user_chat_id = context.bot_data[user_id]['chat_id']
    
    post_result = make_post(context, description)
    if (not post_result):
        context.user_data['state'] = None
        return
    
    delete_messages(context)
    # Notify the user that their submission was rejected
    context.bot.send_message(chat_id=user_chat_id, text=f"Your submission was approved and will be posted on Instagram with the following description: {description}")

    context.user_data['state'] = None

def make_post(context, description):
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
        logger.error(f"Error during the posting process: {str(e)}")
        return False

def make_instagram_post(img_links, description):
    try:
        # Step 1: Create individual item containers for each image
        item_ids = []
        for img_url in img_links:
            payload = {
                "image_url": img_url,
                "is_carousel_item": True,
                "access_token": INSTAGRAM_ACCESS_TOKEN
            }
            response = requests.post(f"https://graph.facebook.com/v17.0/{INSTAGRAM_USER_ID}/media", data=payload)
            response_data = response.json()
            if "id" in response_data:
                item_ids.append(response_data["id"])
            else:
                return handle_error(f"Error creating item container for {img_url}: {response_data.get('error', {})}")

        # Step 2: Create a carousel container
        payload = {
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
            "caption": description,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        response = requests.post(f"https://graph.facebook.com/v17.0/{INSTAGRAM_USER_ID}/media", data=payload)
        response_data = response.json()
        if "id" not in response_data:
            return handle_error(f"Error creating carousel container: {response_data.get('error', {})}")
        
        # Step 3: Publish the carousel
        payload = {
            "creation_id": response_data["id"],
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        response = requests.post(f"https://graph.facebook.com/v17.0/{INSTAGRAM_USER_ID}/media_publish", data=payload)
        response_data = response.json()
        if "id" not in response_data:
            return handle_error(f"Error publishing carousel: {response_data.get('error', {})}")

        return None
    except Exception as e:
        return handle_error(f"Error during Instagram post creation: {str(e)}")

    
def handle_error(message):
    logger.error(message)
    return message

def delete_messages(context):
    user_id = context.user_data['proceeded_user_id']
    for message_id in context.bot_data[user_id]['message_ids_to_delete']:
        try:
            context.bot.delete_message(chat_id=MY_TG_CHAT_ID, message_id=message_id)
        except TelegramError as e:
            logger.error(f"Error deleting message with ID {message_id}: {e}")

    context.bot_data[user_id]['message_ids_to_delete'] = []
    context.bot_data[user_id]['images'] = []
    context.bot_data[user_id]['state'] = IMAGES

def error_callback(update: Update, context: CallbackContext):
    error_message = str(context.error)
    traceback_message = traceback.format_exc()
    context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"An error occurred: {error_message}\n{traceback_message}")
    logger.error("Global error handler: %s\n%s", error_message, traceback_message)

def save_telegram_images(context):
    user_id = context.user_data['proceeded_user_id']
    saved_image_paths = []
    
    current_directory = os.getcwd()
    image_folder_path = os.path.join(current_directory, 'temp_images')
    
    if not os.path.exists(image_folder_path):
        os.makedirs(image_folder_path)

    for image_id in context.bot_data[user_id]['images']:
        file = context.bot.get_file(image_id)
        local_path = os.path.join(image_folder_path, f"{image_id}.jpg")
        file.download(local_path)
        saved_image_paths.append(local_path)
    
    return saved_image_paths

def cleanup_telegram_images(saved_image_paths):
    for image_path in saved_image_paths:
        os.remove(image_path)

def upload_to_imgur(image_paths):
    res = {
        "imgur_links": [],
        "deletehash": [],
        "success": False,
        "message": ""
    }

    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}"
    }

    for image_path in image_paths:
        with open(image_path, 'rb') as image_file:
            files = {
                'image': image_file
            }
            response = requests.post(IMGUR_ENDPOINT, headers=headers, files=files)
            response_data = response.json()
            
            if response.status_code == 200:
                res["imgur_links"].append(response_data['data']['link'])
                res["deletehash"].append(response_data['data']['deletehash'])
                res["success"] = True
            else:
                res["success"] = False
                res["message"] = response_data.get('data', {}).get('error', '')
                delete_from_imgur(res["deletehash"])
                break

    cleanup_telegram_images(image_paths)
                
    return res

def delete_from_imgur(deletehashes):
    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}"
    }
    
    for deletehash in deletehashes:
        response = requests.delete(IMGUR_DELETE_ENDPOINT.format(deletehash=deletehash), headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Error deleting image with deletehash {deletehash} from Imgur: {response.text}")

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.photo, handle_image))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    dp.add_error_handler(error_callback)
    
    updater.start_polling()
    updater.idle()

def get_long_lived_token():
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": FACEBOOK_APP_ID,
        "client_secret": FACEBOOK_SECRET,
        "fb_exchange_token": INSTAGRAM_ACCESS_TOKEN
    }

    response = requests.get("https://graph.facebook.com/v17.0/oauth/access_token", params=params)
    data = response.json()

    if "access_token" in data:
        return data["access_token"]
    else:
        logger.error(f"Error getting long-lived token: {data.get('error', {})}")
        return None

if __name__ == '__main__':
    # print('long_live_token => ', get_long_lived_token())
    main()