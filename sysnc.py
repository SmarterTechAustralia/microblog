import sqlite3
import requests
import schedule
import time
from telegram import Bot, InputFile
from telegram.error import TelegramError
from io import BytesIO
import yaml  # https://python.land/data-processing/python-yaml

with open("keys.yaml", "r") as file:
    keys = yaml.safe_load(file)

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = keys["telegram"]["bot_token"]
TELEGRAM_CHANNEL_ID = keys["telegram"]["channel_id"]

# WordPress Credentials
WORDPRESS_URL = keys["wordpress"]["url"]
WP_USERNAME = keys["wordpress"]["username"]
WP_PASSWORD = keys["wordpress"]["password"]

# Initialize Telegram Bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)


# Initialize Database
def init_db():
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            message_id INTEGER PRIMARY KEY,
            text TEXT,
            image_url TEXT,
            wp_post_id INTEGER
        )
    """
    )
    conn.commit()
    conn.close()


# Fetch Messages from Telegram
def fetch_telegram_messages():
    updates = bot.get_updates()
    for update in updates:
        if update.message:
            process_message(update.message)


# Process Telegram Message
def process_message(message):
    text = message.text or ""
    image_url = None

    if message.photo:
        file_id = message.photo[-1].file_id
        image_url = download_telegram_image(file_id)

    store_message(message.message_id, text, image_url)


# Download Telegram Image
def download_telegram_image(file_id):
    try:
        file = bot.get_file(file_id)
        response = requests.get(file.file_path)
        image_data = BytesIO(response.content)
        filename = f"images/{file_id}.jpg"
        with open(filename, "wb") as img_file:
            img_file.write(image_data.getbuffer())
        return filename
    except TelegramError:
        return None


# Store Message in SQLite
def store_message(message_id, text, image_url):
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO posts (message_id, text, image_url)
        VALUES (?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET text=?, image_url=?
    """,
        (message_id, text, image_url, text, image_url),
    )
    conn.commit()
    conn.close()
    publish_to_wordpress(message_id, text, image_url)


# Publish Post to WordPress
def publish_to_wordpress(message_id, title, content, image_url):
    auth = (WP_USERNAME, WP_PASSWORD)
    media_id = None

    if image_url:
        media_id = upload_image_to_wordpress(image_url)

    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "featured_media": media_id if media_id else None,
    }

    response = requests.post(WORDPRESS_URL, json=post_data, auth=auth)
    if response.status_code == 201:
        wp_post_id = response.json()["id"]
        update_wp_post_id(message_id, wp_post_id)


# Upload Image to WordPress
def upload_image_to_wordpress(image_path):
    auth = (WP_USERNAME, WP_PASSWORD)
    with open(image_path, "rb") as img_file:
        files = {"file": img_file}
        response = requests.post(f"{WORDPRESS_URL}/media", files=files, auth=auth)
        if response.status_code == 201:
            return response.json()["id"]
    return None


# Update WordPress Post ID in SQLite
def update_wp_post_id(message_id, wp_post_id):
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE posts SET wp_post_id=? WHERE message_id=?
    """,
        (wp_post_id, message_id),
    )
    conn.commit()
    conn.close()


# Sync Process
def sync():
    fetch_telegram_messages()
    # Add function to check for WordPress updates


# Schedule the Sync Every X Minutes
schedule.every(5).minutes.do(sync)

# Initialize Database
init_db()

# Start the Scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
