# Telegram-SpottedDMI-Bot

**Telegram-SpottedDMI-Bot** is the platform that powers **[@Spotted_DMI_Bot](https://telegram.me/Spotted_DMI_Bot)**, a Telegram bot that let students send an anonymous message to the channel community.

### Using the live version
The bot is live on Telegram with the username [**@Spotted_DMI_Bot**](https://telegram.me/Spotted_DMI_Bot).
To see the posts, once published, check [**Spotted DMI**](https://t.me/Spotted_DMI)
Send **'/start'** to start it, **'/help'** to see a list of commands.

Please note that the commands and their answers are in Italian.

## Table of contents

- **[:wrench: Setting up a local istance](#wrench-setting-up-a-local-istance)**
- **[:whale: Setting up a Docker container](#whale-setting-up-a-docker-container)**
- **[:bar_chart: _\[Optional\]_ Setting up testing](#bar_chart-optional-setting-up-testing)**
- **[:books: Documentation](#books-documentation)**

---

## :wrench: Setting up a local istance

#### System requirements
- [Python 3 (3.8.5)](https://www.python.org/downloads/)
- python-pip3

#### Install with *pip3*
Listed in requirements.txt
- [python-telegram-bot](https://pypi.org/project/python-telegram-bot/)
- [requests](https://pypi.org/project/requests/)
- [PyYAML](https://pypi.org/project/PyYAML/)

### Steps:
- Clone this repository
- Rename "data/db/sqlite.db.dist" in "data/db/sqlite.db"
- Rename "data/yaml/reactions.yaml.dist" in "data/yaml/reactions.yaml" and edit the desired parameters.
- Rename "config/settings.yaml.dist" in "config/settings.yaml" and edit the desired parameters:
```yaml
debug:
  local_log: save each and every message in a log file. Make sure the path "logs/messages.log" is valid before putting it to 1

meme:
  channel_group_id: id of the group associated with the channel. Required if comments are enabled
  channel_id: id of the channel to which the bot will send the approved memes
  channel_tag: tag of the channel to which the bot will send the approved memes
  comments: whether or not the channel the bot will send the memes to has comments enabled
  group_id: id of the admin group the memebot will use
  n_votes: votes needed to approve/reject a pending post
  remove_after_h: number of hours after wich pending posts will be automatically by /clean_pending
  reset_on_load: whether or not the database should reset every time the bot launches. USE CAREFULLY
  report_wait_mins: number of minutes the user has to wait before being able to report another user again
  tag: whether or not the bot should tag the admins or just write their usernames

test:
  api_hash: hash of the telegram app used for testing
  api_id: id of the telegram app used for testing
  remote:  whether you want to test the remote database, the local one or both
  session: session of the telegram app used for testing
  bot_tag: tag of the telegram bot used for testing. Include the '@' character
  token: token for the telegram bot used for testing
  #... all the tags above. They will be overwritten when testing

token: token of the telegram bot
bot_tag: tag of the telegram bot
```
- **Run** `python3 main.py`

## :whale: Setting up a Docker container

#### System requirements
- Docker


### Steps:
- Clone this repository
- In "config/settings.yaml.dist", edit the desired values. Be mindful that the one listed below will overwrite the ones in "config/settings.yaml.dist", even if they aren't used in the command line
- **Run** `docker build --tag botimage --build-arg TOKEN=<token_arg> <...> .` 

| In the command line <br>(after each --build-arg) | Type | Function | Optional |
| --- | --- | --- | --- |
| **TOKEN=<token_args>** | string | the token for your telegram bot | REQUIRED |
| **GROUP_ID=<group_id>** | int | id of the admin group the memebot will use | REQUIRED |
| **CHANNEL_ID=<channel_id>** | int | id of the channel to which the bot will send the approved memes  | REQUIRED |
| **CHANNEL_GROUP_ID=<channel_id>** | int | id of the group associated with the channel | REQUIRED IF<br>comments = true |
- **Run** `docker run -d --name botcontainer botimage`

### To stop/remove the container:
- **Run** `docker stop botcontainer` to stop the container
- **Run** `docker rm -f botcontainer` to remove the container

## :bar_chart: _[Optional]_ Setting up testing

### Create a Telegram app:

#### Steps:
- Sign in your Telegram account with your phone number **[here](https://my.telegram.org/auth)**. Then choose “API development tools”
- If it is your first time doing so, it will ask you for an app name and a short name, you can change both of them later if you need to. Submit the form when you have completed it
- You will then see the **api_id** and **api_hash** for your app. These are unique to your app, and not revocable.
- Put those values in the _conf/settings.yaml_ file for local or in the _conf/settings.yaml.dist_ file if you are setting up a docker container
```yaml
test:
    api_hash: HERE
    api_id: HERE
...
```
- Copy the file _tests/conftest.py_ in the root folder and **Run** `python3 conftest.py `. Follow the procedure and copy the session string it provides in the settings file:
```yaml
test:
...
    session: HERE
...
```
- You can then delete the _conftest.py_ file present in the root folder, you won't need it again
- Edit the remaining values in the file as you see fit

**Check [here](https://dev.to/blueset/how-to-write-integration-tests-for-a-telegram-bot-4c0e) you you want to have more information on the steps above**

### In local:

#### Install with *pip3*
- [telethon](https://pypi.org/project/Telethon/)
- [pytest](https://pypi.org/project/pytest/)
- [pytest-asyncio](https://pypi.org/project/pytest-asyncio/)

#### Steps:
- **Run** `pytest`

### In a docker container:

#### Steps:
- Add telethon, pytest and pytest-asyncio to the requirements.txt file
- Access the container and **Run** `pytest` or edit the Dockerfile to do so

## :books: Documentation
Check the gh-pages branch

[Link to the documentation](https://unict-dmi.github.io/Telegram-SpottedDMI-Bot/)
