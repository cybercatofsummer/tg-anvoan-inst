# 📸 Telegram Instagram Post Bot

## 🎨 About the Project

This Telegram bot automates the process of posting user-submitted drawings to an Instagram page. It was created to engage users of an **Anime Print How to Draw Anime(Android Application)** that teaches them how to draw. By allowing users to submit their artwork through Telegram, the bot streamlines the approval and posting process, making community interaction more seamless.

## 🚀 How It Works

1️⃣ **User Submission**

- Users send a **drawing** and their **Instagram username** to the bot.

2️⃣ **Admin Review**

- Admin receives the submission in a **private Telegram chat**.
- Admin can either **approve** or **reject** the submission.

3️⃣ **Approval Process**

- If **approved**, the image is **uploaded to Imgur**.
- The bot then posts the **Imgur image link** to **Instagram**.
- The **Imgur image is deleted** after posting.

4️⃣ **Rejection Process**

- If **rejected**, the bot notifies the user with a reason.
- The user can submit a new drawing.

## 📂 Project Structure

```
TG-INST-POST-BOT/
│── core/                     # Core bot logic
│   ├── data_manager.py       # Manages user and bot data
│   ├── telegram_bot.py       # Initializes and runs the bot
│
│── handlers/                 # Handles Telegram interactions
│   ├── callback.py           # Handles button interactions
│   ├── commands.py           # /start, /help, etc.
│   ├── message.py            # Processes user messages
│   ├── submission.py         # Handles user submissions
│
│── services/                 # External service integrations
│   ├── constants.py          # Stores API keys and constants
│   ├── downloader.py         # Handles image downloads
│   ├── imgur.py              # Uploads and deletes images from Imgur
│   ├── instagram.py          # Posts images to Instagram
│   ├── post.py               # Manages Instagram post creation
│   ├── publisher.py          # Publishes images to Instagram
│   ├── utils.py              # General utilities
│
│── temp_images/              # Temporary storage for images
│
│── .env                      # Environment variables (not committed)
│── config.py                 # Configuration file
│── main.py                   # Entry point for the bot
│── requirements.txt           # Dependencies
│── token_generator.py         # Generates access tokens
```

## ⚙️ Installation

1. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables:** Create a `.env` file with the following:

   ```
   ADMIN_TG_CHAT_ID=ADMIN_TG_CHAT_ID
   BOT_TOKEN=BOT_TOKEN
   IMGUR_CLIENT_ID=IMGUR_CLIENT_ID
   IMGUR_CLIENT_SECRET=IMGUR_CLIENT_SECRET
   INSTAGRAM_ACCESS_TOKEN=INSTAGRAM_ACCESS_TOKEN
   INSTAGRAM_USER_ID=INSTAGRAM_USER_ID
   FACEBOOK_APP_ID=FACEBOOK_APP_ID
   FACEBOOK_SECRET=FACEBOOK_SECRET
   ```

3. **Run the Bot:**

   ```bash
   python main.py
   ```

## 🛠️ Features

✔ **Automates Instagram posting** from Telegram submissions. ✔ **Allows admin review** (approve/reject drawings). ✔ **Uploads images to Imgur** before posting to Instagram. ✔ **Deletes images from Imgur** after posting. ✔ **Notifies users of approval or rejection.** ✔ **Easy setup with **``** file.**

## 🚀 Future Improvements

- Add **AI-based moderation** to filter inappropriate images.
- Add **AI-based generation** to generate post descriptions.
- Support **multi-language responses**.
- Support **Unit tests**.