# Microblog Sync


This project synchronizes posts between a Telegram channel and a WordPress blog. It uses a SQLite database to store the posts and the `python-telegram-bot` library to interact with the Telegram API.



> We strongly believe that we cannot trust media controlled by billionaires. If we use them, we should also keep a copy on our own website and database. That's why we created this Python program—to help you save everything you publish on your Telegram channel, both on your local machine and your WordPress site.

## Prerequisites

    - Windows, Linux, or WSL (Windows Subsystem for Linux) on Windows is highly recommended  
    - Python 3.x
    - pip (Python package installer)
    - Telegram Channel
    - Telegram Bot
    - WordPress Site

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/SmarterTechAustralia/microblog.git
    cd microblog
    ```

    - It is recommended to run it in a virtual environment. For example:

    ```sh
    python3 -m venv .
    ```

    - Replace `python3` with `python` if you are on Windows.

2. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

3. Create a `keys.yaml` file in the project root directory with the following structure:

    ```yaml
    telegram:
      bot_token: "YOUR_TELEGRAM_BOT_TOKEN"
      channel_id: "YOUR_TELEGRAM_CHANNEL_ID"

    wordpress:
      url: "YOUR_WORDPRESS_URL"
      username: "YOUR_WORDPRESS_USERNAME"
      password: "YOUR_WORDPRESS_PASSWORD"
    ```
4. update your `kesys.yaml` with Telegram Bot and WordPress credential
    - Telegram Bot
        - You should have or create a Telegram bot and add it to your channel as an admin. Follow these steps:
            1. **Create a Telegram Bot**:
                - Open the Telegram app and search for the `@BotFather` bot.
                - Start a chat with `@BotFather` and send the command `/newbot`.
                - Follow the instructions to choose a name and username for your bot.
                - After completing the setup, `@BotFather` will provide you with a bot token. Save this token as you will need it later.

            2. **Get the Channel ID**:
                - Add your bot to the desired Telegram channel.
                - Make the bot an admin of the channel.
                - To get the channel ID, you can use the following method:
                    - Forward a message from your channel to `@userinfobot` on Telegram.
                    - `@userinfobot` will reply with information about the forwarded message, including the channel ID (it will be a negative number).

            3. **Configure the Bot**:
                - Ensure your bot has the necessary permissions to read messages and post in the channel.

            4. **Add the Bot Token and Channel ID to `keys.yaml`**:
                - Use the bot token and channel ID in the `keys.yaml` file as shown in the installation section.
    - WordPress Site
        - You should have a WordPress site with an admin username and an active API key:
        1. **Set Up a WordPress Site**:
            - Ensure you have a WordPress site up and running.
            - You should have an admin username and password for your WordPress site.

        2. **Generate an API Key**:
            - Log in to your WordPress admin dashboard.
            - Navigate to `Users` > `Profile`.
            - Scroll down to the `Application Passwords` section.
            - Enter a name for the application (e.g., "Microblog Sync") and click `Add New Application Password`.
            - Copy the generated API key and save it securely as you will need it later.
            - Use this API key in the `keys.yaml` file you have created previously.


## Usage

1. Initialize the database:

    ```sh
    python sync.py --init-db
    ```

2. Run the sync process:

    ```sh
    python sync.py
    ```

## Features

- Fetches messages from a Telegram channel.
- Downloads images from Telegram messages.
- Publishes posts to a WordPress blog.
- Updates existing WordPress posts.
- Marks deleted Telegram messages and deletes corresponding WordPress posts. (Disabled)

## Code Overview

- `sync.py`: Main script that handles the synchronization process.
- `keys.yaml`: Configuration file containing API keys and credentials.

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

## Running the app automatically

### On Linux

To run the app automatically using a cron job, follow these steps:

1. Open the crontab file for editing:

    ```sh
    crontab -e
    ```

2. Add a new cron job to run the sync script at your desired interval. For example, to run the script every hour, add the following line:

    ```sh
    0 * * * * /usr/bin/python3 /home/kevin/projects/microblog/sync.py
    ```

3. Save and close the crontab file. The cron job will now run the script automatically at the specified interval.

### On Windows

To run the app automatically using Task Scheduler, follow these steps:

1. Open Task Scheduler from the Start menu.

2. Click on "Create Basic Task" in the Actions pane.

3. Follow the wizard to set up the task:
    - Name: Enter a name for the task (e.g., "Microblog Sync").
    - Trigger: Choose how often you want the task to run (e.g., daily, weekly).
    - Action: Select "Start a program" and browse to the Python executable (e.g., `C:\Python39\python.exe`).
    - Add arguments: Enter the path to the sync script (e.g., `C:\Users\Kevin\projects\microblog\sync.py`).

4. Finish the wizard and the task will be created. The Task Scheduler will now run the script automatically at the specified interval.


## Questions and help
For any questions or assistance, feel free to reach out. I will respond as soon as I can. If you find this project helpful, you can support me by buying me a coffee [here](https://buymeacoffee.com/kevinjamau).

## License

This project is licensed under the MIT License.