# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2023-11-12

### Added

- Add **/reload** command to reload the bot configuration without restarting it
- Add banned users list to the **/sban** command [ closes #124 ] [ from #140 ]
- Add scoped command list to differentiate between user and admin commands
- Added python package anyone can install to immediately run the bot, without going through git
  - The python package name will be `telegram-spotted-dmi-bot` (hence `pip install telegram-spotted-dmi-bot`)
  - The name of the main module will be `spotted` (hence `import spotted`)
- the project will be versioned, starting from 2.0.0. So you will need a tag with a new version to publish the new python package
- Timestamp to the user_follow table to keep track of when a user started following a post
- Utility script `run_sql` to run an arbitrary sql script on the indicated sqlite3 database

### Fixed

- Anonymous messages are deleted [ rebase over #132 ]
- Preview feature [ cherry-pick #138 ]
- Display the right message when the post is rejected with a reason [ cherry-pick #139 ]

### Changed

- Directory structure will be modified to follow the [src standard](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/#src-layout-vs-flat-layout)
- Split the `callback_handlers` functions in multiple files and avoid using `globals`
- All configuration files are now intern to the bot and serve as the default. When launched, the bot will look for some user-provided configurations that will override the defaults. Their path can be configured through command-line arguments.
- Support for changing the main branch from good old "upgrade" to "main" (must be done in the repo settings)
- Use `sqlite3.PARSE_DECLTYPES` for the database connection to perform an automatic conversion between `datetime` (python) and `timestamp` (sqlite) types

### Removed

- Reaction feature (it's no longer utilized since Telegram has implemented its own)
- Identical links assigned in each translation file
- Duplicate index file for the english version

[3.0.0]: https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot/compare/upgrade...v3.0.0
