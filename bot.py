from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackQueryHandler, ConversationHandler, MessageFilter, CallbackContext
import traceback
import logging
import json
import os
import sqlite3


MY_TG_CHAT_ID = os.getenv('MY_TG_CHAT_ID')
BOT_TOKEN = os.getenv('BOT_TOKEN')

PHOTO, APPROVE, REJECTION_REASON = range(3)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

logger = logging.getLogger(__name__)

class MyChatIdFilter(MessageFilter):
    def __init__(self, my_chat_id):
        self.my_chat_id = my_chat_id
        self.name = 'MyChatIdFilter'  # Optional name for the filter

    def filter(self, message):
        return str(message.chat_id) == self.my_chat_id

filterByMyChatId = MyChatIdFilter(MY_TG_CHAT_ID)

def start(update: Update, context):
    update.message.reply_text("Send me your image!")

media_groups = {}

def handle_image(update: Update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    media_group_id = update.message.media_group_id
    image = update.message.photo[-1]

    if media_group_id:
        if media_group_id not in media_groups:
            media_groups[media_group_id] = {
                "images": [],
                "user": user,
                "chat_id": chat_id
            }
        media_groups[media_group_id]["images"].append(image.file_id)

        # Assuming the last image has been received when the group size matches the number of images
        if len(media_groups[media_group_id]["images"]) == 2:
            process_images(context, media_groups[media_group_id])
            del media_groups[media_group_id]
            return PHOTO
    else: 
        process_single_image(context, image.file_id, user, chat_id)
        return PHOTO
    
def insertToDB(chat_id, message_ids_str, file_ids_str):
    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO submissions (user_chat_id, admin_message_ids, image_file_ids) VALUES (?, ?, ?)',
        (chat_id, message_ids_str, file_ids_str)
    )
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id

def process_images(context, media_group):
    images = media_group["images"]
    user = media_group["user"]
    chat_id = media_group["chat_id"]

    media = [InputMediaPhoto(file_id) for file_id in images]
    sent_messages = context.bot.send_media_group(chat_id=MY_TG_CHAT_ID, media=media)

    message_ids = [str(message.message_id) for message in sent_messages]

    # Concatenating file_ids into a single string
    file_ids_str = ','.join(images)
    message_ids_str = ','.join(message_ids)

    record_id = insertToDB(chat_id, message_ids_str, file_ids_str)

    approve_data = json.dumps({"action": "approve", "record_id": record_id})
    reject_data = json.dumps({"action": "reject", "record_id": record_id})

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Approve", callback_data=approve_data),
         InlineKeyboardButton("Reject", callback_data=reject_data)]
    ])

    # it's not possible to add keyboard to media group, so just send new message
    messageForMedia = context.bot.send_message(chat_id=MY_TG_CHAT_ID, text="Submission from: " + user.username, reply_markup=keyboard)


    message_ids.append(str(messageForMedia.message_id))
    updated_message_ids_str = ','.join(message_ids)

    # consider refactoring since I connect to db here twice
    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE submissions SET admin_message_ids = ? WHERE id = ?', (updated_message_ids_str, record_id))
    conn.commit()
    conn.close()

def process_single_image(context, image_file_id, user, chat_id):

    sent_message = context.bot.send_photo(chat_id=MY_TG_CHAT_ID, photo=image_file_id, caption=f"Submission from: {user.username}")
    # Extracting the message_id
    message_id = sent_message.message_id

    record_id = insertToDB(chat_id, str(message_id), image_file_id)

    approve_data = json.dumps({"action": "approve", "record_id": record_id})
    reject_data = json.dumps({"action": "reject", "record_id": record_id})

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Approve", callback_data=approve_data),
         InlineKeyboardButton("Reject", callback_data=reject_data)]
    ])

    # Edit the message to include the inline keyboard
    sent_message.edit_reply_markup(reply_markup=keyboard)
    # update.message.reply_text("Thanks! Your picture is under review, you'll be notified when it will be posted")


def handle_callback(update: Update, context):
    query = update.callback_query
    query.answer() # This ends the loading state on the button

    data = json.loads(query.data)
    action = data['action']

    record_id = data['record_id']

    submission = getRecordById(record_id)

    if action == 'approve':
        return handleApprove(query, context, submission['user_chat_id'], submission['admin_message_ids'], record_id)
    if action == 'reject':
        return handleReject(query, context, submission['user_chat_id'], submission['admin_message_ids'], record_id)


def handleApprove(query, context, chat_id, message_ids, record_id):
    query.message.reply_text("Please enter the description for post:")
    return handleRequest(APPROVE, context, chat_id, message_ids, record_id)

def handleReject(query, context, chat_id, message_ids, record_id):
    query.message.reply_text("Please enter the reason for rejection:")
    return handleRequest(REJECTION_REASON, context, chat_id, message_ids, record_id)

def handleRequest(action, context, chat_id, message_ids, record_id): 
    context.user_data['chat_id'] = chat_id
    context.user_data['message_ids_to_delete'] = message_ids
    context.user_data['record_id'] = record_id
    return APPROVE if action == APPROVE else REJECTION_REASON

def handle_rejection_reason(update: Update, context):
    rejection_reason = update.message.text
    chat_id_to_reject = context.user_data['chat_id']
    message_ids_to_delete = [int(x) for x in context.user_data['message_ids_to_delete'].split(',')]
    record_id = context.user_data['record_id']

    # Delete the original message (you'll need the message_id)
    for message_id in message_ids_to_delete:
        context.bot.delete_message(chat_id=MY_TG_CHAT_ID, message_id=message_id)

    # Notify yourself that the rejection was completed
    context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"Submission from {chat_id_to_reject} rejected for reason: {rejection_reason}")

    # Notify the user that their submission was rejected
    context.bot.send_message(chat_id=chat_id_to_reject, text=f"Your submission was rejected for the following reason: {rejection_reason}")

    deleteRecordById(record_id)
    
    return PHOTO if hasPendingSubmissions() else ConversationHandler.END

def handle_approve(update: Update, context):
    description = update.message.text
    chat_id_to_notify = context.user_data['chat_id']
    message_ids_to_delete = [int(x) for x in context.user_data['message_ids_to_delete'].split(',')]

    record_id = context.user_data['record_id']

    # Use the description to create the post (e.g., post to Instagram)

    for message_id in message_ids_to_delete:
        context.bot.delete_message(chat_id=MY_TG_CHAT_ID, message_id=message_id)

    # Notify the user that their submission was rejected
    context.bot.send_message(chat_id=chat_id_to_notify, text=f"Your submission was approved and will be posted on Instagram with the following description: {description}")

    deleteRecordById(record_id)
    
    return PHOTO if hasPendingSubmissions() else ConversationHandler.END

def handle_text(update: Update, context):
    update.message.reply_text("Please send me a photo, not text. Start over by sending a photo!")

def error_callback(update: Update, context: CallbackContext):
    error_message = str(context.error)
    traceback_message = traceback.format_exc()
    context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"An error occurred: {error_message}\n{traceback_message}")
    #logger.error("Global error handler: %s\n%s", error_message, traceback_message)

def getRecordById(record_id):
    conn = sqlite3.connect('submissions.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (record_id,))
    submission = cursor.fetchone()
    conn.close()

    return dict(submission) if submission else None


def deleteRecordById(record_id):
    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM submissions WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.photo, handle_image)], # Entry point is now the handle_image function
        states={
            PHOTO: [CallbackQueryHandler(handle_callback)],
            APPROVE: [MessageHandler(Filters.text & ~Filters.command & filterByMyChatId, handle_approve)],
            REJECTION_REASON: [MessageHandler(Filters.text & ~Filters.command & filterByMyChatId, handle_rejection_reason)],
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(Filters.text, handle_text)], # You can use the start command as a fallback
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error_callback)
    
    updater.start_polling()
    updater.idle()

def hasPendingSubmissions():
    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM submissions')
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def init_db():
    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY,
        user_chat_id INTEGER,
        admin_message_ids TEXT,
        image_file_ids TEXT
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    main()