from curses import echo
import os
import sqlite3
import requests
import asyncio
from telegram import Bot, InputFile
from telegram.error import TelegramError
from io import BytesIO
import yaml
from datetime import datetime

with open("keys.yaml", "r") as file:
    keys = yaml.safe_load(file)

    # Telegram Bot Credentials
    TELEGRAM_BOT_TOKEN = keys["telegram"]["bot_token"]
    TELEGRAM_CHANNEL_ID = keys["telegram"]["channel_id"]

    # WordPress Credentials
    WORDPRESS_URL = keys["wordpress"]["url"]
    WP_USERNAME = keys["wordpress"]["username"]
    WP_PASSWORD = keys["wordpress"]["password"]

    # Bluesky Credentials
    bluesky_username = keys["bluesky"]["handle"]
    bluesky_password = keys["bluesky"]["password"]

# Initialize Telegram Bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def verify_bot_token():
    try:
        bot_info = await bot.get_me()
        print("Bot Info:", bot_info)
    except TelegramError as e:
        print("Failed to verify bot token:", e)


# Define the download_telegram_image function
async def download_telegram_image(file_id):
    print("Downloading image:", file_id)
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        # print("File Path:", file_path)
        # file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        # print("File URL:", file_url)

        response = requests.get(file_path)
        if response.status_code == 200:
            os.makedirs("images", exist_ok=True)
            image_path = os.path.join("images", file_path.split("/")[-1])
            with open(image_path, "wb") as f:
                f.write(response.content)
            return image_path
        else:
            print(f"Failed to download image: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None


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
            wp_post_id INTEGER,
            created_at TEXT,
            updated_at TEXT,
            deleted INTEGER DEFAULT 0
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
            # print("Raw Update:", update)  # Print raw data received from Telegram

            if update.message and update.message.chat.id == TELEGRAM_CHANNEL_ID:
                await process_message(update.message)
            elif (
                update.channel_post
                and update.channel_post.chat.id == TELEGRAM_CHANNEL_ID
            ):
                await process_message(update.channel_post)
            elif (
                update.edited_message
                and update.edited_message.chat.id == TELEGRAM_CHANNEL_ID
            ):
                await process_edited_message(update.edited_message)
            elif (
                update.edited_channel_post
                and update.edited_channel_post.chat.id == TELEGRAM_CHANNEL_ID
            ):
                await process_edited_message(update.edited_channel_post)
            else:
                print("No new messages to process.")
    except TelegramError as e:
        print("Failed to fetch messages:", e)


# Process Telegram Message
async def process_message(message):
    text = message.caption or message.text or ""
    image_url = None

    if message.photo:
        file_id = message.photo[-1].file_id
        image_url = await download_telegram_image(file_id)

    await store_message(message.message_id, text, image_url)


# Process Edited Telegram Message
async def process_edited_message(message):
    text = message.caption or message.text or ""
    image_url = None

    if message.photo:
        file_id = message.photo[-1].file_id
        image_url = await download_telegram_image(file_id)

    await update_message(message.message_id, text, image_url)


# Store Message in SQLite
async def store_message(message_id, text, image_url):
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    updated_at = created_at
    cursor.execute(
        """
        INSERT INTO posts (message_id, text, image_url, created_at, updated_at) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET text=?, image_url=?, updated_at=?
    """,
        (
            message_id,
            text,
            image_url,
            created_at,
            updated_at,
            text,
            image_url,
            updated_at,
        ),
    )
    conn.commit()
    cursor.execute("SELECT wp_post_id FROM posts WHERE message_id=?", (message_id,))
    wp_post_id = cursor.fetchone()
    conn.close()
    if wp_post_id:
        await update_wordpress_post(wp_post_id[0], text, text, image_url)
    else:
        await publish_to_wordpress(message_id, text, text, image_url)


# Update Message in SQLite and WordPress
async def update_message(message_id, text, image_url):
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    updated_at = datetime.utcnow().isoformat()
    cursor.execute(
        """
        UPDATE posts SET text=?, image_url=?, updated_at=? WHERE message_id=?
    """,
        (text, image_url, updated_at, message_id),
    )
    conn.commit()
    cursor.execute("SELECT wp_post_id FROM posts WHERE message_id=?", (message_id,))
    wp_post_id = cursor.fetchone()
    conn.close()
    if wp_post_id:
        await update_wordpress_post(wp_post_id[0], text, text, image_url)
    else:
        print(f"No WordPress post ID found for message ID {message_id}")


# Publish Post to WordPress
async def publish_to_wordpress(message_id, title, content, image_url):
    auth = (WP_USERNAME, WP_PASSWORD)
    media_id = None

    if image_url:
        media_id = await upload_image_to_wordpress(image_url)

    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "featured_media": media_id if media_id else None,
    }

    # print("Publishing to WordPress:", post_data)  # Debugging information
    response = requests.post(WORDPRESS_URL, json=post_data, auth=auth)
    # print("WordPress Response:", response.status_code, response.text)  # Debugging information
    if response.status_code == 201:
        wp_post_id = response.json()["id"]
        await update_wp_post_id(message_id, wp_post_id)


# Update WordPress Post
async def update_wordpress_post(wp_post_id, title, content, image_url):
    auth = (WP_USERNAME, WP_PASSWORD)
    media_id = None

    if image_url:
        media_id = await upload_image_to_wordpress(image_url)

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
    elif response.status_code == 404:
        print(f"WordPress post {wp_post_id} not found, creating a new post.")
        await publish_to_wordpress(wp_post_id, title, content, image_url)


# Upload Image to WordPress
async def upload_image_to_wordpress(image_path):
    print("Uploading Image to WordPress:", image_path)
    auth = (WP_USERNAME, WP_PASSWORD)
    with open(image_path, "rb") as img_file:
        files = {"file": img_file}
        response = requests.post(
            f"{WORDPRESS_URL}/wp-json/wp/v2/media", data=files, auth=auth
        )
        print(
            "Uploading Image to WordPress:", response.status_code, response.text
        )  # Debugging information
        if response.status_code == 201:
            return response.json()["id"]


# Update WordPress Post ID in SQLite
async def update_wp_post_id(message_id, wp_post_id):
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
    cursor.execute("SELECT message_id, wp_post_id FROM posts WHERE deleted=0")
    stored_messages = cursor.fetchall()

    updates = await bot.get_updates()
    current_message_ids = set()

    for update in updates:
        if update.channel_post and update.channel_post.chat.id == TELEGRAM_CHANNEL_ID:
            current_message_ids.add(update.channel_post.message_id)

    deleted_message_ids = {row[0] for row in stored_messages} - current_message_ids

    for message_id in deleted_message_ids:
        print(f"Message {message_id} has been deleted.")
        cursor.execute("UPDATE posts SET deleted=1 WHERE message_id=?", (message_id,))
        conn.commit()
        cursor.execute("SELECT wp_post_id FROM posts WHERE message_id=?", (message_id,))
        wp_post_id = cursor.fetchone()
        if wp_post_id:
            await delete_wordpress_post(wp_post_id[0])

    conn.close()


# Delete WordPress Post
async def delete_wordpress_post(wp_post_id):
    auth = (WP_USERNAME, WP_PASSWORD)
    response = requests.delete(f"{WORDPRESS_URL}/{wp_post_id}", auth=auth)
    print("Deleting WordPress Post:", wp_post_id)  # Debugging information
    print(
        "WordPress Delete Response:", response.status_code, response.text
    )  # Debugging information
    if response.status_code == 200:
        print(f"WordPress post {wp_post_id} deleted successfully.")


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
