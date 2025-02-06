# Microblog Sync

This project synchronizes posts between a Telegram channel and a WordPress blog. It uses a SQLite database to store the posts and the `python-telegram-bot` library to interact with the Telegram API.

## Prerequisites

- Python 3.x
- pip (Python package installer)

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/SmarterTechAustralia/microblog.git
    cd microblog
    ```

2. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

3. Create a [keys.yaml](http://_vscodecontentref_/1) file in the project root directory with the following structure:

    ```yaml
    telegram:
      bot_token: "YOUR_TELEGRAM_BOT_TOKEN"
      channel_id: "YOUR_TELEGRAM_CHANNEL_ID"

    wordpress:
      url: "YOUR_WORDPRESS_URL"
      username: "YOUR_WORDPRESS_USERNAME"
      password: "YOUR_WORDPRESS_PASSWORD"


## Usage

1. Initialize the database:

    ```sh
    python sync.py --init-db
    ```

2. Run the sync process:

    ```sh
    python sync.py
    ```
3. Create a `keys.yaml` file and fill it with the following content and replace your credential: 
```
telegram:
  bot_token: your_telegram_bot_token
  bot_username: your_bot_uername
  channel_id: your_channelID_that_starts_with-100

wordpress:
  url: "https://yourWPsite"
  username: wp_username
  password: WP_API_PASS
  
```

## Features

- Fetches messages from a Telegram channel.
- Downloads images from Telegram messages.
- Publishes posts to a WordPress blog.
- Updates existing WordPress posts.
- Marks deleted Telegram messages and deletes corresponding WordPress posts. (Disabled)

## Code Overview

- [sync.py](http://_vscodecontentref_/2): Main script that handles the synchronization process.
- [keys.yaml](http://_vscodecontentref_/3): Configuration file containing API keys and credentials.

## Functions

- `verify_bot_token()`: Verifies the Telegram bot token.
- `download_telegram_image(file_id)`: Downloads an image from Telegram.
- `init_db()`: Initializes the SQLite database.
- `fetch_channel_messages()`: Fetches messages from the Telegram channel.
- `process_message(message)`: Processes a Telegram message.
- `process_edited_message(message)`: Processes an edited Telegram message.
- `store_message(message_id, text, image_url, media_id, file_id)`: Stores a message in the SQLite database.
- `update_message(message_id, text, image_url, media_id, file_id)`: Updates a message in the SQLite database.
- `publish_to_wordpress(message_id, title, content, image_url, media_id)`: Publishes a post to WordPress.
- `update_wordpress_post(wp_post_id, title, content, image_url)`: Updates a WordPress post.
- `upload_image_to_wordpress(image_url)`: Uploads an image to WordPress.
- `update_wp_post_id(message_id, wp_post_id)`: Updates the WordPress post ID in the SQLite database.
- `check_deleted_messages()`: Checks for deleted messages and updates the database and WordPress accordingly.
- `delete_wordpress_post(wp_post_id)`: Deletes a WordPress post.
- `sync()`: Main sync process.
- `run_main()`: Runs the main async function.
- `main()`: Initializes the database and runs the main async function.


## Questions and help
For any questions or assistance, feel free to reach out. I will respond as soon as I can. If you find this project helpful, you can support me by buying me a coffee [here](https://buymeacoffee.com/kevinjamau).

## License

This project is licensed under the MIT License.