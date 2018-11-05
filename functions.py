# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler

# Token
tokenconf = open('config/token.conf', 'r').read()
tokenconf = tokenconf.replace("\n", "")

# Token of your telegram bot that you created from @BotFather, write it on token.conf
TOKEN = tokenconf


#Bot functions

#Function: start_cmd
#Send message with bot's information
def start_cmd(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text="Informazioni bot")

#Function: spot_cmd
#Send the user a request for a spotted message
def spot_cmd(bot, update):

    # bot.sendMessage(chat_id = update.message.chat_id, text="Invia un messaggio da spottare ", reply_markup = types.ForceReply())
    update.message.reply_text("Invia il messaggio che vuoi spottare")
