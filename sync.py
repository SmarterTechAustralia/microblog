import sqlite3
import requests
import asyncio
from telegram import Bot, InputFile
from telegram.error import TelegramError
from io import BytesIO
import yaml

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


async def verify_bot_token():
    try:
        bot_info = await bot.get_me()
        print("Bot Info:", bot_info)
    except TelegramError as e:
        print("Failed to verify bot token:", e)


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
    print("Database initialized successfully.")


# Fetch Messages from Telegram Channel
async def fetch_channel_messages():
    try:
        updates = await bot.get_updates()
        if not updates:  # No new messages
            print("No new messages to process.")
            return

        for update in updates:
            print("Raw Update:", update)  # Print raw data received from Telegram

            if update.message and update.message.chat.id == TELEGRAM_CHANNEL_ID:
                process_message(update.message)
            elif (
                update.channel_post
                and update.channel_post.chat.id == TELEGRAM_CHANNEL_ID
            ):
                process_message(update.channel_post)
            elif (
                update.edited_message
                and update.edited_message.chat.id == TELEGRAM_CHANNEL_ID
            ):
                process_edited_message(update.edited_message)
            elif (
                update.edited_channel_post
                and update.edited_channel_post.chat.id == TELEGRAM_CHANNEL_ID
            ):
                process_edited_message(update.edited_channel_post)
            else:
                print("No new messages to process.")
    except TelegramError as e:
        print("Failed to fetch messages:", e)


# Process Telegram Message
def process_message(message):
    text = message.text or ""
    image_url = None

    if message.photo:
        file_id = message.photo[-1].file_id
        image_url = download_telegram_image(file_id)

    store_message(message.message_id, text, image_url)


# Process Edited Telegram Message
def process_edited_message(message):
    text = message.text or ""
    image_url = None

    if message.photo:
        file_id = message.photo[-1].file_id
        image_url = download_telegram_image(file_id)

    update_message(message.message_id, text, image_url)


# Store Message in SQLite
def store_message(message_id, text, image_url):
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO posts (message_id, text, image_url) VALUES (?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET text=?, image_url=?
    """,
        (message_id, text, image_url, text, image_url),
    )
    conn.commit()
    cursor.execute("SELECT wp_post_id FROM posts WHERE message_id=?", (message_id,))
    wp_post_id = cursor.fetchone()
    conn.close()
    if wp_post_id:
        update_wordpress_post(wp_post_id[0], text, text, image_url)
    else:
        publish_to_wordpress(message_id, text, text, image_url)


# Update Message in SQLite and WordPress
def update_message(message_id, text, image_url):
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE posts SET text=?, image_url=? WHERE message_id=?
    """,
        (text, image_url, message_id),
    )
    conn.commit()
    cursor.execute("SELECT wp_post_id FROM posts WHERE message_id=?", (message_id,))
    wp_post_id = cursor.fetchone()[0]
    conn.close()
    update_wordpress_post(wp_post_id, text, text, image_url)


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

    print("Publishing to WordPress:", post_data)  # Debugging information
    response = requests.post(WORDPRESS_URL, json=post_data, auth=auth)
    print(
        "WordPress Response:", response.status_code, response.text
    )  # Debugging information
    if response.status_code == 201:
        wp_post_id = response.json()["id"]
        update_wp_post_id(message_id, wp_post_id)


# Update WordPress Post
def update_wordpress_post(wp_post_id, title, content, image_url):
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

    print("Updating WordPress Post:", wp_post_id, post_data)  # Debugging information
    response = requests.post(f"{WORDPRESS_URL}/{wp_post_id}", json=post_data, auth=auth)
    print(
        "WordPress Update Response:", response.status_code, response.text
    )  # Debugging information
    if response.status_code == 200:
        print(f"WordPress post {wp_post_id} updated successfully.")


# Upload Image to WordPress
def upload_image_to_wordpress(image_path):
    auth = (WP_USERNAME, WP_PASSWORD)
    with open(image_path, "rb") as img_file:
        files = {"file": img_file}
        response = requests.post(f"{WORDPRESS_URL}/media", files=files, auth=auth)
        print(
            "Uploading Image to WordPress:", response.status_code, response.text
        )  # Debugging information
        if response.status_code == 201:
            return response.json()["id"]


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


# Check for Deleted Messages
async def check_deleted_messages():
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    cursor.execute("SELECT message_id FROM posts")
    stored_message_ids = {row[0] for row in cursor.fetchall()}

    updates = await bot.get_updates()
    current_message_ids = set()

    for update in updates:
        if update.channel_post and update.channel_post.chat.id == TELEGRAM_CHANNEL_ID:
            current_message_ids.add(update.channel_post.message_id)

    deleted_message_ids = stored_message_ids - current_message_ids

    for message_id in deleted_message_ids:
        print(f"Message {message_id} has been deleted.")
        cursor.execute("DELETE FROM posts WHERE message_id=?", (message_id,))
        conn.commit()

    conn.close()


# Sync Process
async def sync():
    print("Starting sync process...")
    await fetch_channel_messages()
    await check_deleted_messages()
    print("Sync process completed.")


async def run_main():
    # Call the verification function
    await verify_bot_token()
    # Run the sync process
    await sync()


def main():
    # Initialize Database
    init_db()

    # Run the main async function
    asyncio.run(run_main())


if __name__ == "__main__":
    main()
