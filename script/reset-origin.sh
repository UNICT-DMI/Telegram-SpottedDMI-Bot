# Hard resets the current branch so that it is even with the https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot.git repo
# The updated branch is then force pushed to the remote origin, which should be your fork.
# WARNING: you will lose all local commits that are not on the https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot.git repo
git fetch https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot.git refs/heads/upgrade:dmi-upstream/upgrade
git reset --hard dmi-upstream/upgrade
git push -f origin upgrade