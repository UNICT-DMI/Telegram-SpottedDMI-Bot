# Telegram-SpottedDMI-Bot

[![Test and docs](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/prod.workflow.yml/badge.svg)](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/prod.workflow.yml)
[![Docker image](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/docker.yml/badge.svg)](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/docker.yml)
[![CodeFactor](https://www.codefactor.io/repository/github/unict-dmi/telegram-spotteddmi-bot/badge)](https://www.codefactor.io/repository/github/unict-dmi/telegram-spotteddmi-bot)

**Telegram-SpottedDMI-Bot** is the platform that powers **[@Spotted_DMI_Bot](https://telegram.me/Spotted_DMI_Bot)**, a Telegram bot that let students send an anonymous message to the channel community.

### 🔴 Using the live version

The bot is live on Telegram with the username [**@Spotted_DMI_Bot**](https://telegram.me/Spotted_DMI_Bot).
To see the posts, once published, check [**Spotted DMI**](https://t.me/Spotted_DMI)
Send **'/start'** to start it, **'/help'** to see a list of commands.

Please note that the commands and their answers are in Italian.

---

## 🤖 Telegram bot setup

If you want to deploy your own version of this bot, you will need to have a telegram bot available. You should read [this guide](https://core.telegram.org/bots#3-how-do-i-create-a-bot) for more details, but in short:

- Send a message to [@Botfather](https://t.me/botfather)
- Follow the guided procedure
- You will recieve a token. Whoever knows that token has complete control over your bot, so handle it with care
- You will need that token later, for it is a needed value in the settings

## 💻 Setting up a local istance

#### System requirements

- [Python 3 (3.9)](https://www.python.org/downloads/)
- python-pip3

#### Install with _pip3_

Listed in requirements.txt.  
The main ones are:

- [python-telegram-bot](https://pypi.org/project/python-telegram-bot/)
- [requests](https://pypi.org/project/requests/)
- [PyYAML](https://pypi.org/project/PyYAML/)

### Steps:

- Clone this repository
- \[_OPTIONAL_\] Create _"data/yaml/reactions.yaml"_ and edit the desired parameters.
- Create [_"config/settings.yaml"_](#⚙️-settings) and edit the desired parameters. **Make sure to add a valid _token_ setting**.
- Make sure the bot is in present both in the admin group and in the spot channel. It may need to have admin privileges. If comments are enabled, the bot has to be in the comment group too as an admin.
- What follows are some example settings with explaination for each:

- **Run** `python3 main.py`

## 🐳 Setting up a Docker container

#### System requirements

- [Docker](https://www.docker.com/)

### Steps:

- Clone this repository
- \[_OPTIONAL_\] Create _"data/yaml/reactions.yaml"_ and edit the desired parameters.
- Create [_"config/settings.yaml"_](#⚙️-settings) and edit the desired parameters. **Make sure to add a valid _token_ setting**.
- \[_OPTIONAL_\] You could also leave the settings files alone, and use [_environment variables_](#settings-override) on the container instead.
- Make sure the bot is in present both in the admin group and in the spot channel. It may need to have admin privileges. If comments are enabled, the bot has to be in the comment group too as an admin.
- All the env vars with the same name (case insensitive) will override the ones in the settings file.
  To update the **meme** settings, prefix the env var name with **MEME\_**. The same is true for the **test** settings, that have to be prefixed with **TEST\_**.
- **Run** `docker build --tag botimage .`
- **Run** `docker run -d --name botcontainer -e TOKEN=<token_arg> [other env vars] botimage`

### Examples

First run

```bash
docker build --tag botimage .
```

Then something like

```bash
docker run -d --name botcontainer -e TOKEN=<token_arg> -e MEME_CHANNEL_ID=-4 -e MEME_GROUP_ID=-5 TEST_TOKEN=<token_test> botimage
```

### To stop/remove the container:

- **Run** `docker stop botcontainer` to stop the container
- **Run** `docker rm -f botcontainer` to remove the container

## 📦 DevContainer

The VsCode [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension lets you use a Docker container as a full-featured development environment. It allows you to open any folder inside (or mounted into) a container and take advantage of VsCode's full feature set.

### System requirements

- [VsCode](https://code.visualstudio.com/)
- [Docker](https://www.docker.com/)

### Steps

- Start VsCode, run the **Remote-Containers: Reopen in container** command from the Command Palette (F1)

## ⚙️ Settings

When it is initialized, the bot reads both the _"data/yaml/reactions.yaml"_ and the _"config/settings.yaml"_ files.  
Feel free to customize the settings file. Make sure to add a valid **token** value to run the bot.

```yaml
# config/settings.yaml
debug:
  local_log: false # save each and every message in a log file. Make sure the path "logs/messages.log" is valid when enabled
  reset_on_load: false # whether or not the database should reset every time the bot launches. USE CAREFULLY

meme:
  channel_group_id: -100 # id of the group associated with the channel. Required if comments are enabled
  channel_id: -200 # id of the channel to which the bot will send the approved memes
  channel_tag: "@channel" # tag of the channel to which the bot will send the approved memes
  comments: true # whether or not the channel the bot will send the memes to has comments enabled
  group_id: -300 # id of the admin group the memebot will use
  n_votes: 2 # votes needed to approve/reject a pending post
  remove_after_h: 12 # number of hours after wich pending posts will be automatically by /clean_pending
  report_wait_mins: 30 # number of minutes the user has to wait before being able to report another user again
  report: true # whether to add a report button as an inline keyboard after each post
  tag:
    false # whether or not the bot should tag the admins or just write their usernames
    # whether the bot should delete any anonym comment coming from a channel.
    # The bots must have delete permission in the group and comments must be enabled
  delete_anonymous_comments:
    true
    # whether the bot should replace any anonymous comment with a message by itself.
    # WARNING: delete_anonymous_comments must be true for this option to make sense.
    # Otherwise the comment would be doubled.
    # The bots must have delete permission in the group and comments must be enabled
  replace_anonymous_comments: false

test:
  api_hash: XXXXXXXXXXX # hash of the telegram app used for testing
  api_id: 123456 # id of the telegram app used for testing
  remote: false # whether you want to test the remote database, the local one or both
  session: XXXXXXXXXXXX # session of the telegram app used for testing
  bot_tag: "@test_bot" # tag of the telegram bot used for testing. Include the '@' character
  token: xxxxxxxxxxxx # token for the telegram bot used for testing
  #... all the tags above. They will be overwritten when testing

token: xxxxxxxxxxxx # token of the telegram bot
bot_tag: "@bot" # tag of the telegram bot
```

### Settings override

The settings may also be set through environment variables.  
All the env vars with the same name (case insensitive) will override the ones in the settings file.
To update the **meme** settings, prefix the env var name with **MEME\_**. The same is true for the **test** settings, that have to be prefixed with **TEST\_** and the **debug** settings, to be prefixed with **DEBUG\_**.

```env
# Environment values
TOKEN=xxxxxx        # will override the *token* value found in settings.yaml
MEME_N_VOTES=4      # will override the *meme.n_votes* value found in settings.yaml
DEBUG_LOCAL_LOG=4   # will override the *debug.local_log* value found in settings.yaml
```

The complete order of precedence is for the application of configuration settings is

```
env var > settings.yaml > settings.yaml.default
```

Since every setting has a default value specified in _settings.yaml.default_ except for **token**, this is the only necessary settings to add when setting up the bot for the first time.

### Settings typing

Typings is provided by default for eny value specified through the _.yaml_ files.
On the other hand, if you use the environment variables, everything will be treated as a string.  
To prevent this, you can use the _settings.yaml.types_ specifying a type for each setting.
This way it will be casted in the specified type.

Supported types:

- bool
- int
- float
- list (of str)

Any unknown type won't be casted.
This means that env var will remain strings.

```yaml
# settings.yaml.types
debug:
  local_log: bool
  reset_on_load: bool
meme:
  channel_group_id: int
  channel_id: int
  channel_tag: str
  comments: bool
  group_id: int
  n_votes: int
  remove_after_h: int
  tag: bool
  report: bool
  report_wait_mins: int
  replace_anonymous_comments: bool
  delete_anonymous_comments: bool
test:
  api_hash: str
  api_id: int
  session: str
  bot_tag: str
  token: str
token: str
bot_tag: str
```

## 🧪 _[Optional]_ Setting up testing

#### Install with _pip3_

Listed in requirements_dev.txt

- [pytest](https://pypi.org/project/pytest/)

#### Steps:

- **Run** `pytest tests/unit` to run the unit tests
- **Run** `pytest tests/e2e` to run the e2e tests (this requires test configurations)

## 📚 Documentation

Check the gh-pages branch

[Link to the documentation](https://unict-dmi.github.io/Telegram-SpottedDMI-Bot/)
