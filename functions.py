# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,\
                        KeyboardButton, ReplyMarkup, ForceReply, PhotoSize, Video
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters

#Json
import json

# Token
tokenconf = open("config/token.conf", "r").read()
tokenconf = tokenconf.replace("\n", "")
#Admins group chatid
with open('config/adminsid.json') as j:
    ids = json.load(j)


# Token of your telegram bot that you created from @BotFather, write it on token.conf
TOKEN = tokenconf
ADMINS_ID = ids["admins_chat_id"]
CHANNEL_ID = ids["channel_chat_id"]

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
    bot.sendMessage(chat_id = update.message.chat_id, text="Invia un messaggio da spottare.", reply_markup = ForceReply())


#Function: spot_get
#Get the user text or media response to spot_cmd and forward it to the Admin chat
def spot_get(bot, update):
    try:
        if update.message.reply_to_message.text == "Invia un messaggio da spottare.":
            available = handle_type(bot,update.message,ADMINS_ID)
            if available:
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Si", callback_data = '0$'+str(update.message.message_id)+"$"+str(update.message.chat_id) ),\
                                                    InlineKeyboardButton("No", callback_data = '1$'+str(update.message.message_id)+"$"+str(update.message.chat_id))]])
                print
                bot.sendMessage(chat_id = ADMINS_ID,\
                                    text = "Pubblicare il messaggio di @%s?" % update.message.from_user.username,\
                                    reply_markup = reply_markup )
            else:
                bot.sendMessage(chat_id = update.message.chat_id, text = "È possibile solo inviare messaggi di testo,"+\
                " immagini, audio o video")
    except Exception as e:
        print(str(e))

#Function: handle_type
#Return True if the message is a text a photo, a voice, an audio or a video; False otherwise
def handle_type(bot, message, chat_id):
    try:
        text = message.text
        photo = message.photo
        voice = message.voice
        audio = message.audio
        video = message.video
        caption = message.caption

        if text:
            bot.sendMessage(chat_id = chat_id, text = text)
        elif photo:
            bot.sendPhoto(chat_id = chat_id, photo = photo[-1], caption = caption)
        elif voice:
            bot.sendVoice(chat_id = chat_id, voice = voice)
        elif audio:
            bot.sendAudio(chat_id = chat_id, audio = audio)
        elif video:
            bot.sendVideo(chat_id = chat_id, video = video, caption = caption)
        else:
            return False
        return True
    except Exception as e:
        print("handle: "+str(e))


#Function: publish
#Publish the spotted message on the channel and send the user an acknowledgement
def publish(bot, update, message_id, chat_id):
    try:
        message = bot.sendMessage(chat_id = int(chat_id),\
                text = "Il tuo messaggio è stato accettato e pubblicato!\nCorri a guardare le reazioni su @channel." ,\
                reply_to_message_id = int(message_id))
        handle_type(bot, message.reply_to_message, CHANNEL_ID)
    except Exception as e:
        print("publish: "+str(e))

#Function: refuse
#Acknowledge the user that the message has been refused
def refuse(bot, update, message_id, chat_id):
    try:
        bot.sendMessage(chat_id = int(chat_id), text = "Il tuo messaggio é stato rifiutato.",\
                        reply_to_message_id = int(message_id))
    except Exception as e:
        print("refuse: "+str(e))

#Function: callback_spot
#Handle the callback according to the Admin choise
def callback_spot(bot, update):
    try:
        query = update.callback_query
        data = query.data
        split = data.split("$")
        pr = split[0]
        message_id = split[1]
        chat_id = split[2]
        if data[0] == '0':
            publish(bot, update, message_id, chat_id)
            bot.answer_callback_query(query.id)
        else:
            refuse(bot, update, message_id, chat_id)
            bot.answer_callback_query(query.id)
    except Exception as e:
        print("callback: "+str(e))
