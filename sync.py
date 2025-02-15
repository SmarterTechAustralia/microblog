from curses import echo
import os
import sqlite3
from tkinter import W
import requests
import asyncio
from telegram import Bot, InputFile
from telegram.error import TelegramError
from io import BytesIO
import yaml
from datetime import datetime, timezone
import langid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script directory
yaml_path = os.path.join(BASE_DIR, "keys.yaml")  # Absolute path to keys.yaml

with open(yaml_path, "r") as file:
    keys = yaml.safe_load(file)

    # Telegram Bot Credentials
    TELEGRAM_BOT_TOKEN = keys["telegram"]["bot_token"]
    TELEGRAM_CHANNEL_ID = keys["telegram"]["channel_id"]

    # WordPress Credentials
    WORDPRESS_URLEN = keys["wordpress"]["urlen"]
    WORDPRESS_URLFA = keys["wordpress"]["urlfa"]
    WP_USERNAME = keys["wordpress"]["username"]
    WP_PASSWORD = keys["wordpress"]["password"]

    # Bluesky Credentials
    # bluesky_username = keys["bluesky"]["handle"]
    # bluesky_password = keys["bluesky"]["password"]

# Initialize Telegram Bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def verify_bot_token():
    try:
        bot_info = await bot.get_me()
        # print("Bot Info:", bot_info)
    except TelegramError as e:
        print("Failed to verify bot token:", e)


# Define the download_telegram_image function
async def download_telegram_image(file_id):
    # print("Downloading image:", file_id)
    try:
        os.makedirs("images", exist_ok=True)
        image_path = os.path.join("images", f"{file_id}.jpg")

        if os.path.exists(image_path):
            # print("Image already exists:", image_path)
            return image_path

        file = await bot.get_file(file_id)
        file_path = file.file_path

        response = requests.get(file_path)
        if response.status_code == 200:
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
            text_language TEXT,
            image_url TEXT,
            wp_post_id INTEGER,
            wp_media_id INTEGER,
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
            print("No new messages feteched to process.")
            return

        for update in updates:
            # print("Raw Update:", update)  # Print raw data received from Telegram

            if (
                update.message and update.message.chat.id == TELEGRAM_CHANNEL_ID
            ):  # Check if the message is from the correct channel
                print("Message")
                await process_message(update.message)
            elif (
                update.channel_post
                and update.channel_post.chat.id == TELEGRAM_CHANNEL_ID
            ):  # Check if the channel post is from the correct channel
                print("Channael Post")
                await process_message(update.channel_post)
            elif (
                update.edited_message
                and update.edited_message.chat.id == TELEGRAM_CHANNEL_ID
            ):  # Check if the edited message is from the correct channel
                print("Edited Message")
                await process_edited_message(update.edited_message)
            elif (
                update.edited_channel_post
                and update.edited_channel_post.chat.id == TELEGRAM_CHANNEL_ID
            ):  # Check if the edited channel post is from the correct channel
                print("Edited Channel Post")
                await process_edited_message(update.edited_channel_post)
            else:
                print("Unknown message type:", update, "\n\n\n")

    except TelegramError as e:
        print("Failed to fetch messages:", e)


# Process Telegram Message
async def process_message(message):
    text = message.caption or message.text or ""
    image_url = None

    if message.photo:
        file_id = new_func(message)
        conn = sqlite3.connect("microblog.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT image_url FROM posts WHERE image_url LIKE ?", (f"%{file_id}%",)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            # If the image is already stored in the database, use the existing URL
            print("Image already stored in the database:", result[0])
            image_url = result[0]
        else:
            # If the image is not stored in the database, download it and store the URL
            image_url = await download_telegram_image(file_id)

    await store_message(message.message_id, text, image_url)


def new_func(message):
    file_id = message.photo[-1].file_id
    return file_id


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
    text_language = langid.classify(text)[0]
    if text_language == "en":
        WORDPRESS_URL = WORDPRESS_URLEN
    elif text_language == "fa":
        WORDPRESS_URL = WORDPRESS_URLFA
    else:  # Default to English
        WORDPRESS_URL = WORDPRESS_URLEN

    print(WORDPRESS_URL)
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    created_at = datetime.now(timezone.utc).isoformat()
    updated_at = created_at
    cursor.execute(
        """
        INSERT INTO posts (message_id, text, text_language, image_url, created_at, updated_at) VALUES (?, ? ,?, ?, ?, ?)
        ON CONFLICT(message_id) DO UPDATE SET text=?, image_url=?, updated_at=?
    """,
        (
            message_id,
            text,
            text_language,
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
    if wp_post_id and isinstance(wp_post_id[0], int):
        await update_wordpress_post(
            WORDPRESS_URL, message_id, wp_post_id[0], text, text, image_url
        )
    else:
        await publish_to_wordpress(WORDPRESS_URL, message_id, text, text, image_url)


# Update Message in SQLite and WordPress
async def update_message(message_id, text, image_url):
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    updated_at = datetime.now(timezone.utc).isoformat()
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
    if wp_post_id and isinstance(wp_post_id[0], int):
        await update_wordpress_post(message_id, wp_post_id[0], text, text, image_url)
    else:
        print(f"No WordPress post ID found for message ID {message_id}")


# Publish Post to WordPress
async def publish_to_wordpress(WORDPRESS_URL, message_id, title, content, image_url):
    print("Publishing to WordPress:", message_id)  # Debugging information
    auth = (WP_USERNAME, WP_PASSWORD)
    media_id = None

    if image_url:
        conn = sqlite3.connect("microblog.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT wp_media_id FROM posts WHERE message_id=?", (message_id,)
        )
        result = cursor.fetchone()
        if result and result[0]:
            media_id = result[0]
        else:
            media_id = await upload_image_to_wordpress(WORDPRESS_URL, image_url)
        conn = sqlite3.connect("microblog.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE posts SET wp_media_id=? WHERE message_id=?
        """,
            (media_id, message_id),
        )
        conn.commit()
        conn.close()

    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "featured_media": media_id if media_id else None,
    }

    # print("Publishing to WordPress:", post_data)  # Debugging information
    response = requests.post(
        f"{WORDPRESS_URL}/wp-json/wp/v2/posts", json=post_data, auth=auth
    )
    print("Response:", response)  # Debugging information

    if response.status_code == 201:
        wp_post_id = response.json()["id"]
        print(f"WordPress post {wp_post_id} created successfully.")
        await update_wp_post_id(message_id, wp_post_id)
    else:
        print(f"Failed to publish to WordPress: {response.status_code} {response.text}")


# Update WordPress Post
async def update_wordpress_post(
    WORDPRESS_URL, message_id, wp_post_id, title, content, image_url
):
    auth = (WP_USERNAME, WP_PASSWORD)
    media_id = None

    if image_url:

        conn = sqlite3.connect("microblog.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT wp_media_id FROM posts WHERE message_id=?", (message_id,)
        )
        result = cursor.fetchone()
        if result and result[0]:
            media_id = result[0]
        else:
            media_id = await upload_image_to_wordpress(image_url)

        cursor.execute(
            """
            UPDATE posts SET wp_media_id=? WHERE message_id=?
        """,
            (media_id, message_id),
        )
        conn.commit()
        conn.close()

    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "featured_media": media_id if media_id else None,
    }

    # print("Updating WordPress Post:", wp_post_id, post_data)  # Debugging information
    response = requests.post(
        f"{WORDPRESS_URL}/wp-json/wp/v2/posts/{wp_post_id}", json=post_data, auth=auth
    )

    if response.status_code == 200:
        print(f"WordPress post {wp_post_id} updated successfully.")
    elif response.status_code == 404:
        print(f"WordPress post {wp_post_id} not found, creating a new post.")
        await publish_to_wordpress(WORDPRESS_URL, message_id, title, content, image_url)


async def upload_image_to_wordpress(WORDPRESS_URL, image_path):
    auth = (WP_USERNAME, WP_PASSWORD)
    wpmwdiaurl = f"{WORDPRESS_URL}/wp-json/wp/v2/media"

    with open(image_path, "rb") as img_file:
        files = {"file": img_file}
        headers = {
            "Authorization": "Basic <base64-encoded-credentials>",
            "Content-Type": "image/jpeg",
        }
        try:
            response = requests.post(
                wpmwdiaurl,
                files=files,
                auth=auth,
                headers={
                    "Content-Disposition": f'attachment; filename="{os.path.basename(image_path)}"'
                },
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            wp_media_id = response.json()["id"]

            return wp_media_id

        except requests.exceptions.RequestException as e:
            print(f"Error uploading image: {e}")
            if response.status_code != 201:
                print(f"Response status code: {response.status_code} {response.text}")
            return None


# Update WordPress Post ID in SQLite
async def update_wp_post_id(message_id, wp_post_id):
    print(f"Updating WordPress Post ID for message ID {message_id} to {wp_post_id}")
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


# Check for Deleted Messages in Telegram Channel and Delete from WordPress
# This function is not working as expected. It needs to be fixed.


async def check_deleted_messages():
    conn = sqlite3.connect("microblog.db")
    cursor = conn.cursor()
    cursor.execute("SELECT message_id, wp_post_id FROM posts WHERE deleted=0")
    stored_messages = cursor.fetchall()
    print("Stored Messages ID:", stored_messages)

    updates = await bot.get_updates()
    current_message_ids = set()

    for update in updates:
        if update.channel_post and update.channel_post.chat.id == TELEGRAM_CHANNEL_ID:
            current_message_ids.add(update.channel_post.message_id)
    print("Current Message IDs:", current_message_ids)
    deleted_message_ids = {row[0] for row in stored_messages} - current_message_ids
    print("Deleted Message IDs:", deleted_message_ids)

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
    response = requests.delete(
        f"{WORDPRESS_URL}/wp-json/wp/v2/posts/{wp_post_id}", auth=auth
    )
    print("Deleting WordPress Post:", wp_post_id)  # Debugging information

    if response.status_code == 200:
        print(f"WordPress post {wp_post_id} deleted successfully.")


# Sync Process
async def sync():
    print("Starting sync process...")
    await fetch_channel_messages()
    # disabled the check_deleted_messages function until it is fixed
    # await check_deleted_messages()
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
