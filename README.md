# Telegram-DMI-Bot

**Telegram-SpottedDMI-Bot** is the platform that powers **[@Spotted_DMI_Bot](https://telegram.me/Spotted_DMI_Bot)**, a Telegram bot that let students send an anonymous message to the channel community.

### Using the live version
The bot is live on Telegram with the username [@Spotted_DMI_Bot](https://telegram.me/Spotted_DMI_Bot).
Send **'/start'** to start it, **'/help'** to see a list of commands.

Please note that the commands and their answers are in Italian.

---

### Setting up a local istance
If you want to test the bot by creating your personal istance, follow this steps:
* **Clone this repository** or download it as zip.
* **Copy config/token.conf.dist into "token.conf" and write your telegram bot token here.** (If you don't have a token, message Telegram's [@BotFather](http://telegram.me/Botfather) to create a bot and get a token for it)
* **Send a message to your bot** on Telegram, even '/start' will do.

### System requirements

- Python 3
- python3-pip

#### To install with *pip3*

- python-telegram-bot

#### How to use
Add the API TOKEN in /config/token.conf
Add the numeric ids of the requested chats in /config/adminsid.json
Run from shell:
```
$ python main.py
```

### Docker container

#### How to use
Build image dmibot with docker:

```
$ docker build ./ -t spotted --build-arg TOKEN=<token_API> --build-arg ADMIN_CHAT_ID=<admin_chat_id> --build-arg CHANNEL_CHAT_ID=<channel_chat_it>
```

Run the container dmibot:

```
$ docker run -it spotted
```

Now you can go to the dmibot directory and run the bot:

```
$ cd /usr/local/dmibot/
$ python main.py
```

### License
This open-source software is published under the GNU General Public License (GNU GPL) version 3. Please refer to the "LICENSE" file of this project for the full text.

### Credits
