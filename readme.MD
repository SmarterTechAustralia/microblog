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

    - Enter your virtual environment in Linux:

    ```sh
    source bin/activate 
    ```

    - Or if you are using Windows:
    ```sh
    .\Scripts\activate
    ```

   > **_Note:_** Replace `python3` with `python` if you are on Windows.

2. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

3. Create a [keys.yaml](http://_vscodecontentref_/1) file in the project root directory with the following structure:
     - in linux try `sudo nano keys.yaml` 

    ```yaml
    telegram:
      bot_token: "YOUR_TELEGRAM_BOT_TOKEN"
      channel_id: "YOUR_TELEGRAM_CHANNEL_ID"

    wordpress:
      urlen: "YOUR_EN_WORDPRESS_URL"
      urlfa: "YOUR_FA_WORDPRESS_URL"
      username: "YOUR_WORDPRESS_USERNAME"
      password: "YOUR_WORDPRESS_API_KEY"
    ```

4. Update your [keys.yaml](http://_vscodecontentref_/2) with Telegram Bot and WordPress credentials:
    - **Telegram Bot**:
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

            4. **Add the Bot Token and Channel ID to [keys.yaml](http://_vscodecontentref_/3)**:
                - Use the bot token and channel ID in the [keys.yaml](http://_vscodecontentref_/4) file as shown in the installation section.

    - **WordPress Site**:
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
                - Use this API key in the [keys.yaml](http://_vscodecontentref_/5) file you have created previously.

## Usage

1. Initialize the database:

    ```sh
    python sync.py --init-db
    ```

2. Run the sync process:

    ```sh
    python sync.py
    ```

> **_Note:_** Ensure your virtual environment is activated before running the sync process.

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
For any questions or assistance, feel free to reach out. I will respond as soon as I can. If you find this project helpful, you can support me by buying me a coffee 
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/kevinjamau)

## License

This project is licensed under the MIT License.