# Microblog Sync

This project synchronizes posts between a Telegram channel and a WordPress blog. It uses a SQLite database to store the posts and the `python-telegram-bot` library to interact with the Telegram API.

## Prerequisites

- Python 3.x
- pip (Python package installer)

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/microblog-sync.git
    cd microblog-sync
    ```

2. Install the required Python packages:

    ```sh
    pip install requests schedule python-telegram-bot pyyaml
    ```

3. Create a [keys.yaml](http://_vscodecontentref_/0) file in the project directory with your credentials:

    ```yaml
    telegram:
      bot_token: "YOUR_TELEGRAM_BOT_TOKEN"
      channel_id: "@your_channel"

    wordpress:
      url: "https://yourwordpress.com/wp-json/wp/v2/posts"
      username: "your_username"
      password: "your_password"
    ```

## Usage

1. Initialize the database:

    ```sh
    python -c "from sysnc import init_db; init_db()"
    ```

2. Run the synchronization script:

    ```sh
    python sysnc.py
    ```

## Project Structure

- [sysnc.py](http://_vscodecontentref_/1): Main script to synchronize posts between Telegram and WordPress.
- [keys.yaml](http://_vscodecontentref_/2): Configuration file containing Telegram and WordPress credentials.

## License

This project is licensed under the MIT License.