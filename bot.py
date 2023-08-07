from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackQueryHandler, ConversationHandler, MessageFilter
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

def handle_image(update: Update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    image = update.message.photo[-1]

    sent_message = context.bot.send_photo(chat_id=MY_TG_CHAT_ID, photo=image.file_id, caption=f"Submission from: {user.username}")
    # Extracting the message_id
    message_id = sent_message.message_id

    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO submissions (user_chat_id, admin_message_id, image_file_id) VALUES (?, ?, ?)',
                   (chat_id, message_id, image.file_id))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()

    approve_data = json.dumps({"action": "approve", "record_id": record_id})
    reject_data = json.dumps({"action": "reject", "record_id": record_id})

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Approve", callback_data=approve_data),
         InlineKeyboardButton("Reject", callback_data=reject_data)]
    ])

    # Edit the message to include the inline keyboard
    sent_message.edit_reply_markup(reply_markup=keyboard)

    # update.message.reply_text("Thanks! Your picture is under review, you'll be notified when it will be posted")
    return PHOTO


def handle_callback(update: Update, context):
    query = update.callback_query
    query.answer() # This ends the loading state on the button

    data = json.loads(query.data)
    action = data['action']

    record_id = data['record_id']

    submission = getRecordById(record_id)

    if action == 'approve':
        return handleApprove(query, context, submission['user_chat_id'], submission['admin_message_id'], record_id)
    if action == 'reject':
        return handleReject(query, context, submission['user_chat_id'], submission['admin_message_id'], record_id)


def handleApprove(query, context, chat_id, message_id, record_id):
    query.message.reply_text("Please enter the description for post:")
    return handleRequest(APPROVE, context, chat_id, message_id, record_id)

def handleReject(query, context, chat_id, message_id, record_id):
    query.message.reply_text("Please enter the reason for rejection:")
    return handleRequest(REJECTION_REASON, context, chat_id, message_id, record_id)

def handleRequest(action, context, chat_id, message_id, record_id): 
    context.user_data['chat_id'] = chat_id
    context.user_data['message_id_to_delete'] = message_id
    context.user_data['record_id'] = record_id
    return APPROVE if action == APPROVE else REJECTION_REASON

def handle_rejection_reason(update: Update, context):
    rejection_reason = update.message.text
    chat_id_to_reject = context.user_data['chat_id']
    message_id_to_delete = context.user_data['message_id_to_delete']
    record_id = context.user_data['record_id']

    # Delete the original message (you'll need the message_id)
    context.bot.delete_message(chat_id=MY_TG_CHAT_ID, message_id=message_id_to_delete)

    # Notify yourself that the rejection was completed
    context.bot.send_message(chat_id=MY_TG_CHAT_ID, text=f"Submission from {chat_id_to_reject} rejected for reason: {rejection_reason}")

    # Notify the user that their submission was rejected
    context.bot.send_message(chat_id=chat_id_to_reject, text=f"Your submission was rejected for the following reason: {rejection_reason}")

    deleteRecordById(record_id)
    
    return PHOTO if hasPendingSubmissions() else ConversationHandler.END

def handle_approve(update: Update, context):
    description = update.message.text
    chat_id_to_notify = context.user_data['chat_id']
    message_id_to_delete = context.user_data['message_id_to_delete']
    record_id = context.user_data['record_id']

    # Use the description to create the post (e.g., post to Instagram)

    # Delete the original message (you'll need the message_id)
    context.bot.delete_message(chat_id=MY_TG_CHAT_ID, message_id=message_id_to_delete)

    # Notify the user that their submission was rejected
    context.bot.send_message(chat_id=chat_id_to_notify, text=f"Your submission was approved and will be posted on Instagram with the following description: {description}")

    deleteRecordById(record_id)
    
    return PHOTO if hasPendingSubmissions() else ConversationHandler.END

def handle_text(update: Update, context):
    update.message.reply_text("Please send me a photo, not text. Start over by sending a photo!")

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

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
    dp.add_error_handler(error)
    
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
        admin_message_id INTEGER,
        image_file_id TEXT
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    main()