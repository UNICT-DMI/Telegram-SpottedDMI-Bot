# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyMarkup,\
                    ForceReply, PhotoSize, Video
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters

#Json
import json

# Token
tokenconf = open("config/token.conf", "r").read()
tokenconf = tokenconf.replace("\n", "")

#Admins group chat_id
with open("config/adminsid.json") as j:
    ids = json.load(j)
ADMINS_ID = ids["admins_chat_id"]
CHANNEL_ID = ids["channel_chat_id"]

# Token of your telegram bot that you created from @BotFather, write it on token.conf
TOKEN = tokenconf

#Bot functions

#Function: start_cmd
#Send message with bot's information
def start_cmd(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text = "Informazioni bot")

#Function: help_cmd
#Send help message
def help_cmd(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text = "Utilizza il comando /spot per raccontarci qualcosa.")

#Function: spot_cmd
#Send the user a request for a spotted message
def spot_cmd(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text = "Invia un messaggio da spottare.",\
                    reply_markup = ForceReply())

#Function: spot_get
#Get the user text or media response to spot_cmd and forward it to the Admin chat
def spot_get(bot, update):

    chat_id = update.message.chat_id

    if update.message.reply_to_message.text == "Invia un messaggio da spottare.":
        available, message_reply = handle_type(bot, update.message, ADMINS_ID)

        if available:
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Si", callback_data = "0"),\
                                                InlineKeyboardButton("No", callback_data = "1" )]])

            bot.sendMessage(chat_id = ADMINS_ID,\
                                text = "Pubblicare il messaggio di @%s?" % update.message.from_user.username,\
                                reply_markup = reply_markup, reply_to_message_id = message_reply.message_id)
            bot.sendMessage(chat_id = chat_id, text = "Il tuo messaggio è in fase di valutazione.\
                                                    \nTi informeremo non appena verrà analizzato.")
        else:
            bot.sendMessage(chat_id = chat_id, text = "È possibile solo inviare messaggi di testo,"+\
            " immagini, audio o video")
    handle_type

#Function: handle_type
#Return True if the message is a text a photo, a voice, an audio or a video; False otherwise
def handle_type(bot, message, chat_id):

    text = message.text
    photo = message.photo
    voice = message.voice
    audio = message.audio
    video = message.video
    animation = message.animation
    caption = message.caption

    if text:
        _message = bot.sendMessage(chat_id = chat_id, text = text)

    elif photo:
        _message = bot.sendPhoto(chat_id = chat_id, photo = photo[-1], caption = caption)

    elif voice:
        _message = bot.sendVoice(chat_id = chat_id, voice = voice)

    elif audio:
        _message = bot.sendAudio(chat_id = chat_id, audio = audio)

    elif video:
        _message = bot.sendVideo(chat_id = chat_id, video = video, caption = caption)

    elif animation:
        _message = bot.sendAnimation(chat_id = chat_id, animation = animation)

    else:
        return False, None

    return True, _message

#Function: publish
#Publish the spotted message on the channel and send the user an acknowledgement
def publish(bot, message_id, chat_id):

    message = bot.sendMessage(chat_id = chat_id,\
            text = "Messaggio in fase di pubblicazione." ,\
            reply_to_message_id = message_id)

    try:
        handle_type(bot, message.reply_to_message, CHANNEL_ID)
        bot.editMessageText(chat_id = chat_id, message_id = message_id,\
                            text = "Il tuo messaggio è stato accettato e pubblicato!\
                                    \nCorri a guardare le reazioni su %s." % (CHANNEL_ID))

    except:
        bot.editMessageText(chat_id = chat_id, message_id = message_id,\
                            text = "Errore critico durante la pubblicazione, \
                                    contatta gli admin per saperne di più" )

#Function: refuse
#Acknowledge the user that the message has been refused
def refuse(bot, message_id, chat_id):

    bot.sendMessage(chat_id = chat_id, text = "Il tuo messaggio è stato rifiutato.",\
                    reply_to_message_id = message_id)

#Function: callback_spot
#Handle the callback according to the Admin choise
def callback_spot(bot, update):

    query = update.callback_query
    data = query.data
    message = query.message
    reply = message.reply_to_message
    message_id = message.message_id
    chat_id = message.chat.id
    message_id_answ = reply.message_id
    chat_id_answ = reply.chat.id

    if data == "0":
        publish(bot, message_id_answ, chat_id_answ)
        bot.answer_callback_query(query.id)
        bot.editMessageText(chat_id = chat_id, message_id = message_id, text = "Pubblicato")

    else:
        refuse(bot, message_id_answ, chat_id_answ)
        bot.answer_callback_query(query.id)
        bot.editMessageText(chat_id = chat_id, message_id = message_id, text = "Rifiutato")
