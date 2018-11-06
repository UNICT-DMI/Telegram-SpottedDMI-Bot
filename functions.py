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
#Get the user text or media response to spot_cmd and forward it to the Admin chat
def spot_get(bot,update):

    text = update.message.text
    photo = update.message.photo
    voice = update.message.voice
    audio = update.message.audio
    video = update.message.video
    caption = update.message.caption

    if text or photo or voice or audio or video:

        if text:
            bot.sendMessage(chat_id = ADMINS_ID, text = text)
        elif photo:
            bot.sendPhoto(chat_id = ADMINS_ID, photo = photo[-1], caption = caption)
        elif voice:
            bot.sendVoice(chat_id = ADMINS_ID, voice = voice)
        elif audio:
            bot.sendAudio(chat_id = ADMINS_ID, audio = audio)
        elif video:
            bot.sendVideo(chat_id = ADMINS_ID, video = video, caption = caption)

        #reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Sì", callback_data = publish(bot,update) ), InlineKeyboardButton("No", callback_data = refuse(bot,update))]])

        bot.sendMessage(chat_id = ADMINS_ID, text = "Pubblicare il messaggio di @%s?" % update.message.from_user.username )
    else:
        bot.sendMessage(chat_id = update.message.chat_id, text = "E' possibile solo inviare messaggi di testo, immagini, audio o video")
