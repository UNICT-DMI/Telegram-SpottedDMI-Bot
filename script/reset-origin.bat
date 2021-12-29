@echo off
rem Hard resets the current branch so that it is even with the https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot.git repo
rem The updated branch is then force pushed to the remote origin, which should be your fork.
rem WARNING: you will lose all local commits that are not on the https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot.git repo
git fetch https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot.git refs/heads/upgrade:dmi-upstream/upgrade
git switch upgrade
git reset --hard dmi-upstream/upgrade
git push -f origin upgrade