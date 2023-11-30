# Telegram-SpottedDMI-Bot

[![Docs](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/docs.yml/badge.svg)](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/docs.yml)
[![Lint](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/lint.yml/badge.svg)](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/lint.yml)
[![Test](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/test.yml/badge.svg)](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/test.yml)
[![Docker image](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/docker.yml/badge.svg)](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/docker.yml)
[![Publish](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/publish.yml/badge.svg)](https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/actions/workflows/publish.yml)
[![CodeFactor](https://www.codefactor.io/repository/github/unict-dmi/telegram-spotteddmi-bot/badge)](https://www.codefactor.io/repository/github/unict-dmi/telegram-spotteddmi-bot)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

---

## 📂 Project structure

```shell
.
├── .devcontainer # DevContainer configuration for VsCode
├── .github/workflows # CI/CD workflows
├── docs # Documentation
├── scripts # Utility script for setting up the project
├── src
│   ├── spotted # Main package
│   │   ├── __init__.py # Init file for the package
│   │   ├── __main__.py # Entry point for the package
│   │   ├── config # Configuration files
│   │   ├── data # Data related function
│   │   ├── debug # Debug related functions
│   │   ├── handlers # Collection of handlers for the bot
│   │   └── utils # Utility functions
├── tests # Tests
│   ├── e2e # End to end tests
│   ├── integration # Integration tests
│   └── unit # Unit tests
├── Dockerfile # Dockerfile used to build the image
├── pyproject.toml # Package configuration file
└── README.md # This file
```

## 💻 Setting up a local instance for contributing (from git)

#### System requirements

- [Python 3 (3.10)](https://www.python.org/downloads/)
- [pip3](https://pip.pypa.io/en/stable/)

#### Dependencies

All the requirements are listed in the `pyproject.toml` file.
The most important ones are:

- [python-telegram-bot](https://pypi.org/project/python-telegram-bot/)
- [requests](https://pypi.org/project/requests/)
- [PyYAML](https://pypi.org/project/PyYAML/)

#### Install with _pip3_

```shell
# [Optional] Create a virtual environment
python3 -m venv .venv

# [Optional] Activate the virtual environment
source .venv/bin/activate # Linux
.venv\Scripts\activate.bat # Windows

# Using the -e flag will install the package in editable mode
# If you change the code, you won't need to reinstall the package
# If you want to install it in a non-editable mode, just remove the -e flag
pip3 install -e .
```

### Steps:

- Clone this repository
- Create a [_"settings.yaml"_](#settings) file and edit the desired parameters. **It must contain at least a valid _'token'_ and _'post.admin_group_id'_ values**.
  - You could also skip the files and use [_environment variables_](#settings-override) instead.
- Make sure the bot is in present both in the admin group and in the spot channel. It may need to have admin privileges. If comments are enabled, the bot has to be in the comment group too as an admin.
- **Run** `python3 -m spotted` to [start the bot](#running-the-bot)

## 💻 Setting up a local instance for running (from pip)

#### System requirements

- [Python 3 (3.10)](https://www.python.org/downloads/)
- [pip3](https://pip.pypa.io/en/stable/)

#### Install with _pip3_

Install the package:

```shell
pip3 install telegram-spotted-dmi-bot
```

### Steps:

- Create a [_"settings.yaml"_](#settings) file and edit the desired parameters. **It must contain at least a valid _'token'_ and _'post.admin_group_id'_ values**.
  - You could also skip the files and use [_environment variables_](#settings-override) instead.
- **Run** `python3 -m spotted` to [start the bot](#running-the-bot)

## 🐳 Setting up a Docker container

#### System requirements

- [Docker](https://www.docker.com/)

### Steps:

- Clone this repository
- Make sure the bot is in present both in the admin group and in the spot channel. It may need to have admin privileges. If comments are enabled, the bot has to be in the comment group too as an admin.
- **Run** `docker build --tag spotted-image .`
- When starting the container, use [_environment variables_](#settings-override) to configure the bot.
- **Run** `docker run -d --name spotted -e TOKEN=<token_arg> [other env vars] spotted-image`

> [!Tip]  
> When it is built, the container will copy the _"settings.yaml"_ and the _"autoreplies.yaml"_ files, in the root directory, if present.
> While it is possible to provide the configuration this way, it is recommended to use the environment variables instead, as they will override the values from the files.

> [!Warning]  
> The database file created inside the container will be lost when the container is removed.
> If you want to keep the database, you should mount a volume to the container.
> You can do so by adding the `-v <host_path>:<container_path>` flag to the `docker run` command.
> See the [examples](#mounting-a-volume) for more details.

### Examples

First run

```bash
docker build --tag spotted-image .
```

Then something like

```bash
docker run -d --name spotted-container -e TOKEN=<token_arg> -e POST_CHANNEL_ID=-4 -e POST_GROUP_ID=-5 -e POST_CHANNEL_GROUP_ID=-6 spotted-image
```

If you want to check the logs in real time, you can run

```bash
# -f flag to follow the logs, otherwise it will just print the last ones
docker logs -f spotted-container
```

If you want to access the container's shell, you can run

```bash
docker exec -it spotted-container /bin/bash
```

#### Mounting a volume

If you want to keep the database file, you can mount a volume to the container.
This will assume the default database path, which is _"./spotted.sqlite3"_.

```bash
# The file will survive the container removal, stored in the volume "spotted-db"
docker run -d --name spotted-container -v spotted-db:/app -e TOKEN=<token_arg> -e POST_CHANNEL_ID=-4 -e POST_GROUP_ID=-5 -e POST_CHANNEL_GROUP_ID=-6 spotted-image
```

If you want to be able to access the database file from the host, you can use a bind mount instead.

```bash
# The file will be available in the host under the path "./spotted.sqlite3"
docker run -d --name spotted-container -v .:/app -e TOKEN=<token_arg> -e POST_CHANNEL_ID=-4 -e POST_GROUP_ID=-5 -e POST_CHANNEL_GROUP_ID=-6 spotted-image
```

#### Package version

If you want to change the version displayed by the package inside the container, you can do when building the image:

```bash
docker build --tag spotted-image --build-arg VERSION=<version> .
# Example
docker build --tag spotted-image --build-arg VERSION=3.0.0 .
```

Keep in mind that this will only change the version displayed by `python3 -m spotted --version`, not the version of the package itself.

### To stop/remove the container:

- **Run** `docker stop spotted-container` to stop the container
- **Run** `docker rm -f spotted-container` to remove the container

## 📦 DevContainer

The VsCode [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension lets you use a Docker container as a full-featured development environment. It allows you to open any folder inside (or mounted into) a container and take advantage of VsCode's full feature set.

### System requirements

- [VsCode](https://code.visualstudio.com/)
- [Docker](https://www.docker.com/)

### Steps

- Start VsCode, run the **Remote-Containers: Reopen in container** command from the Command Palette (F1)

## Running the bot

After installation, the bot can be started with the command:

```shell
python3 -m spotted
```

There are a few command-line arguments you can use to customize the bot behaviour:

- `--settings` or `-s`: path to the _"settings.yaml"_ file. Default: _"./settings.yaml"_ (relative to the pwd)
- `--auto-replies` or `-a`: path to the _"auto_replies.yaml"_ file. Default: _"./auto_replies.yaml"_ (relative to the pwd)

Also, keep in mind that the bot will generate an sqlite database file in the path indicated by the _settings.yaml_ file named _"spotted.sqlite3"_ by default. The file will be created if missing, but the **path must be valid**.
Lastly, if logs are enabled, the bot will log under the path specified in _settings.yaml_.
By default, it would be _"logs/spotted.log"_ and _"logs/spotted_error.log"_.
The path **will be created** if it does not exist.

## Settings

When it is initialized, the bot reads both the _"config/yaml/autoreplies.yaml"_ and the _"config/settings.yaml"_ files inside the package, which contain the default values for the settings.
Then the configuration gets overwritten using the _"settings.yaml"_ and the _"auto_replies.yaml"_ files you provide.
The bot expects to find both files in the `pwd` directory, meaning the directory from which you run the bot.
You can change this behaviour by specifying the path to the files with the `--config` and `--auto-replies` flags.

```shell
python3 -m spotted -c /path/to/settings.yaml -a /path/to/autoreplies.yaml
```

Feel free to customize the settings file,but make sure to add a valid **token** and **post.admin_group_id** values, since they are mandatory.

```yaml
# config/settings.yaml
debug:
  local_log: false # save each and every message in a log file. Make sure the path "logs/messages.log" is valid when enabled
  reset_on_load: false # whether or not the database should reset every time the bot launches. USE CAREFULLY
  log_file: "logs/spotted.log" # path to the log file, if local_log is enabled. Relative to the pwd
  log_error_file: "logs/spotted_error.log" # path to the error log file. Relative to the pwd
  db_file: "spotted.sqlite3" # path to the database file. Relative to the pwd

post:
  # id of the group associated with the channel. Telegram will send automatically forward the posts there. Required if comments are enabled
  community_group_id: -100
  channel_id: -200 # id of the channel to which the bot will send the approved posts
  channel_tag: "@channel" # tag of the channel to which the bot will send the approved posts
  comments: true # whether or not the channel the bot will send the posts to has comments enabled
  admin_group_id: -300 # id of the admin group the bot will use
  n_votes: 2 # votes needed to approve/reject a pending post
  remove_after_h: 12 # number of hours after wich pending posts will be automatically by /clean_pending
  report_wait_mins: 30 # number of minutes the user has to wait before being able to report another user again
  report:
    true # whether to add a report button as an inline keyboard after each post
    # whether the bot should delete any anonym comment coming from a channel.
    # The bots must have delete permission in the group and comments must be enabled
  delete_anonymous_comments:
    true
    # whether the bot should replace any anonymous comment with a message by itself.
    # WARNING: delete_anonymous_comments must be true for this option to make sense.
    # Otherwise the comment would be doubled.
    # The bots must have delete permission in the group and comments must be enabled
  replace_anonymous_comments: false

token: xxxxxxxxxxxx # token of the telegram bot
bot_tag: "@bot" # tag of the telegram bot
```

### Settings override

The settings may also be set through environment variables.  
All the env vars with the same name (case insensitive) will override the ones in the settings file.
To update the **post** settings, prefix the env var name with **POST\_**. The same is true for the **debug** settings, to be prefixed with **DEBUG\_**.

```env
# Environment values
TOKEN=xxxxxx        # will override the *token* value found in settings.yaml
POST_N_VOTES=4      # will override the *post.n_votes* value found in settings.yaml
DEBUG_LOCAL_LOG=4   # will override the *debug.local_log* value found in settings.yaml
```

The complete order of precedence for the application of configuration settings is

```
env var > (user provided) settings.yaml > (package provided) settings.yaml
```

> [!Note]
> The bot provides a **/reload** command that will reload the settings without restarting the bot.
> Keep in mind that the order of precedence will be the same, meaning that the env vars will always override the _settings.yaml_ files.

Since every setting has a default value specified in the default _settings.yaml_ except for **token** and the **chat_id**s of the groups and the channel, those are the only necessary setting to add when setting up the bot for the first time.
All other values will be assigned a valid default value if not specified.

### Settings typing

Typings are provided by default for eny value specified through the _.yaml_ files.
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
  log_file: str
  log_error_file: str
  db_file: str
post:
  community_group_id: int
  channel_id: int
  channel_tag: str
  comments: bool
  admin_group_id: int
  n_votes: int
  remove_after_h: int
  report: bool
  report_wait_mins: int
  replace_anonymous_comments: bool
  delete_anonymous_comments: bool
token: str
bot_tag: str
```

## 🧪 _[Optional]_ Setting up testing and linting

If you plan to contribute to this project, you may want to run the tests and the linters locally.

> [!Note]  
> When creating a pull request, all the tests and linters will be run automatically using the [github actions](.github/workflows).
> If the tests fail, the pull request won't be merged until all the errors are fixed.
> Hence, it is recommended to run the tests and the linters locally before pushing your changes.

#### Dependencies

All the dev requirements are listed in the `pyproject.toml` file under `[project.optional-dependencies]`.

- [pytest](https://pypi.org/project/pytest/)
- [pytest-cov](https://pypi.org/project/pytest-cov/)
- [pytest-mock](https://pypi.org/project/pytest-mock/)
- [pytest-asyncio](https://pypi.org/project/pytest-asyncio/)
- [pylint](https://pypi.org/project/pylint/)
- [black](https://pypi.org/project/black/)
- [isort](https://pypi.org/project/isort/)

#### Install with _pip3_

After having cloned the repository and having installed the main package with `pip3 install -e .`, you can install the dev dependencies with:

```shell
pip3 install -e .[test]
pip3 install -e .[lint]
```

#### Testing:

- **Run** `pytest tests/unit` to run the unit tests
- **Run** `pytest tests/integration` to run the integration tests
  <!-- TODO -->
  <!-- - **Run** `pytest tests/e2e` to run the e2e tests (this requires test configurations) -->

#### Linting:

- **Run** `pylint src tests` to lint the code
- **Run** `black --check src tests` to make sure the code is formatted correctly. If it is not, you can run `black src` to format it automatically
- **Run** `isort --check-only src tests` to make sure the imports are sorted correctly. If they are not, you can run `isort src` to sort them automatically

### Scripts

The `script` folder contains some utility scripts such as [_script/local-ci.sh_](./script/local-ci.sh) that can be used to simulate the whole CI pipeline locally.
Make sure to have the dev dependencies installed before running them.

Furthermore, the package provides a `run_sql` script that can be used to run an arbitrary sql script on the indicated sqlite3 database.

```shell
run_sql <path_to_sql_script> <path_to_db_file>
# Example
run_sql ./script/create_db.sql ./spotted.sqlite3
```

> [!Important]
> Make sure to backup your database before running any scripts on it, since all alteration will happen in place, and there is no way to undo them.

## 📚 Documentation

[Link to the documentation](https://unict-dmi.github.io/Telegram-SpottedDMI-Bot/)
