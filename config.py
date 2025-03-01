import os
from dotenv import load_dotenv

# for local testing
load_dotenv(dotenv_path=".env")

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_TG_CHAT_ID = os.getenv("MY_TG_CHAT_ID")

# Imgur API Configuration
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")
IMGUR_ENDPOINT = "https://api.imgur.com/3/upload"
IMGUR_DELETE_ENDPOINT = "https://api.imgur.com/3/image/{deletehash}"

# Instagram API Configuration
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_SECRET = os.getenv("FACEBOOK_SECRET")

# Other Configurations
MEDIA_GROUP_TIMEOUT = 1  # Time (in seconds) to wait before grouping media submissions
