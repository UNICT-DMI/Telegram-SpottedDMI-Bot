# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,\
                        KeyboardButton, ReplyMarkup, ForceReply, PhotoSize, Video
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters
# Token
tokenconf = open('config/token.conf', 'r').read()
tokenconf = tokenconf.replace("\n", "")
#Admins group chatid
adminsconf = open('config/adminsid.conf', 'r').read()

# Token of your telegram bot that you created from @BotFather, write it on token.conf
TOKEN = tokenconf
ADMINS_ID = adminsconf

#Bot functions

#Function: start_cmd
#Send message with bot's information
def start_cmd(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text="Informazioni bot")

#Function: help_cmd
#Send help message
def help_cmd(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text="Utilizza il comando /spot per raccontarci qualcosa.")

#Function: spot_cmd
#Send the user a request for a spotted message
def spot_cmd(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text="Invia un messaggio da spottare ", reply_markup = ForceReply())
    

#Function: spot_get
#Get the user response to spot_cmd and forward it to the Admin chat
def spot_get(bot,update):
    try:
        msg_type = update.message.effective_attachment
        if msg_type == None:
            text = update.message.text
            bot.sendMessage(chat_id = ADMINS_ID, text = text)
        # elif type(msg_type) == "PhotoSize":
        #     photo = update.message.photo
        #     bot.sendPhoto(chat_id = ADMINS_ID, photo = photo)
        # print (type(msg_type))
    except Exception as e:
        print (str(e))
