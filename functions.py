# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyMarkup,\
                    ForceReply, PhotoSize, Video
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters

# Utils
import json
import sys
import os

import data_functions as dataf

# Token
tokenconf = open("config/token.conf", "r").read()
tokenconf = tokenconf.replace("\n", "")

# Admins group chat_id
with open("config/adminsid.json") as j:
    ids = json.load(j)
ADMINS_ID = ids["admins_chat_id"]
CHANNEL_ID = ids["channel_chat_id"]
COMMENTS_ID = ids['comments_chat_id']

# Token of your telegram bot that you created from @BotFather, write it on token.conf
TOKEN = tokenconf

# Log functions
def log_error(component, ex):
    print("{}: {}".format(component, str(ex)))
    open("logs/errors.txt", "a+").write("spotcmd {}\n".format(str(ex)))

# Bot functions

# Function: start_cmd
# Send message with bot's information
def start_cmd(bot, update):
    welcome_msg = str(open("text/welcome.md", "r").read())

    bot.sendMessage(chat_id = update.message.chat_id, text = welcome_msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True)

# Function: help_cmd
# Send help message
def help_cmd(bot, update):
    help_msg = str(open("text/help.md", "r").read())

    bot.sendMessage(chat_id = update.message.chat_id, text = help_msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True)

# Function = rules_cmd
# Send message with bot rules
def rules_cmd(bot, update):
    rules_msg = str(open("text/rules.md", "r").read())

    bot.sendMessage(chat_id = update.message.chat_id, text = rules_msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True)

# Function: spot_cmd
# Send the user a request for a spotted message
def spot_cmd(bot, update):
    try:
        chat_id = update.message.chat_id

        f = open("./data/banned.lst", "r").read()

        banned = False
        if f != "":
            for i in f.strip().split("\n"):
                if int(i) == chat_id:
                    banned = True

        if banned:
            bot.sendMessage(chat_id = chat_id, text = "Sei stato bannato.")
        elif update.message.chat.type == "group":
            bot.sendMessage(chat_id = chat_id, text = "Questo comando non è utilizzabile in un gruppo. Chatta con @Spotted_DMI_bot in privato")

        else:
            bot.sendMessage(chat_id = update.message.chat_id, text = "Invia un messaggio da spottare.",\
                            reply_markup = ForceReply())
    except Exception as e:
        log_error("spot cmd", e)

# Function: message_handle
# Handle the user text response to bot message
def message_handle(bot, update):
    try:
        text = update.message.reply_to_message.text

        if text == "Invia un messaggio da spottare.":
            available, message_reply = handle_type(bot, update.message, ADMINS_ID)

            if available:
                message_id = update.message.message_id
                chat_id = update.message.chat_id
                candidate_msgid = message_reply.message_id

                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Sì",callback_data = '0'),\
                                                    InlineKeyboardButton("No", callback_data = '1')]])

                bot.sendMessage(chat_id = ADMINS_ID,\
                                    text = "Pubblicare il seguente messaggio?",\
                                    reply_markup = reply_markup, reply_to_message_id = candidate_msgid)

                dataf.add_pending_spot(candidate_msgid, chat_id, message_id)

                bot.sendMessage(chat_id = chat_id, text = "Il tuo messaggio è in fase di valutazione.\
                                                        \nTi informeremo non appena verrà analizzato.")
            else:
                bot.sendMessage(chat_id = chat_id, text = "È possibile solo inviare messaggi di testo,"+\
                " immagini, audio o video")
        elif text.split("|")[0] == "Scrivi la modifica da proporre." or text.split("|")[0] == "Invia la proposta come testo!":
            data = text.split("|")
            chat_id = int(data[-1])
            message_id = int(data[-2])
            if update.message.text:
                bot.sendMessage(chat_id = chat_id, reply_to_message_id = message_id, text = update.message.text)
                bot.sendMessage(chat_id = update.message.chat_id, text = "Proposta inviata.")
            else:
                bot.editMessageText(chat_id = update.message.chat_id, message_id = update.message.message_id,
                text = "Invia la proposta come messaggio di testo!|\n\n\n|%d|%d" % (message_id, chat_id))
    except Exception as e:
        log_error("message_handler", e)

# Function: handle_type
# Return True if the message is a text a photo, a voice, an audio or a video; False otherwise
def handle_type(bot, message, chat_id):
    try:
        text = message.text
        photo = message.photo
        voice = message.voice
        audio = message.audio
        video = message.video
        animation = message.animation
        caption = message.caption
        reply_markup = None

        # REMOVE COMMENTS if you want to return to the old mode (no comments in the channel)
        # if chat_id == CHANNEL_ID:
        #     reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("👍", callback_data = "u"),\
        #                                     InlineKeyboardButton("👎", callback_data = "d" )]])
        if text:
            _message = bot.sendMessage(chat_id = chat_id, text = text, reply_markup = reply_markup)

        elif photo:
            _message = bot.sendPhoto(chat_id = chat_id, photo = photo[-1], caption = caption, reply_markup = reply_markup)

        elif voice:
            _message = bot.sendVoice(chat_id = chat_id, voice = voice, reply_markup = reply_markup)

        elif audio:
            _message = bot.sendAudio(chat_id = chat_id, audio = audio, reply_markup = reply_markup)

        elif video:
            _message = bot.sendVideo(chat_id = chat_id, video = video, caption = caption, reply_markup = reply_markup)

        elif animation:
            _message = bot.sendAnimation(chat_id = chat_id, animation = animation, reply_markup = reply_markup)
        else:
            return False, None

        return True, _message
    except Exception as e:
        log_error("handle", e)

# Function: publish
# Publish the spotted message on the channel and send the user an acknowledgement
def publish(bot, message_id, chat_id):
    try:
        message = bot.sendMessage(chat_id = chat_id,\
                text = "Messaggio in fase di pubblicazione." ,\
                reply_to_message_id = message_id)

        success, spot_message = handle_type(bot, message.reply_to_message, CHANNEL_ID)

        # REMOVE COMMENTS if you want to return to the old mode (no comments in the channel)
        # if success:
        #     dataf.add_spot_data(spot_message.message_id)

        bot.editMessageText(chat_id = chat_id, message_id = message.message_id,\
                            text = "Il tuo messaggio è stato accettato e pubblicato!\
                                    \nCorri a guardare le reazioni su @%s." % bot.getChat(CHANNEL_ID).username)
    except Exception as e:
        log_error("publish", e)

# Function: refuse
# Acknowledge the user that the message has been refused
def refuse(bot, message_id, chat_id):
    try:
        bot.sendMessage(chat_id = chat_id,\
         text = "Il tuo messaggio è stato rifiutato. Controlla che rispetti gli standard del regolamento tramite il comando /rules .",\
                        reply_to_message_id = message_id)

    except Exception as e:
        log_error("refuse", e)

# Function: callback_spot
# Handle the callback according to the Admin choise
def callback_spot(bot, update):
    try:
        query = update.callback_query
        data = query.data
        message = query.message
        message_id = message.message_id
        chat_id = message.chat.id

        if data == "u" or data == "d":
            spot_edit(bot, message, query)
            bot.answer_callback_query(query.id)
        else:
            candidate_message_id = message.reply_to_message.message_id

            result = dataf.load_pending_spot(candidate_message_id)

            if result:
                message_id_answ = result["msgid"]
                chat_id_answ = result["userid"]

                if data == "0":
                    publish(bot, message_id_answ, chat_id_answ)
                    bot.editMessageText(chat_id = chat_id, message_id = message_id, text = "Pubblicato.")
                    bot.answer_callback_query(query.id)
                    dataf.delete_pending_spot(candidate_message_id)

                elif data == "1":
                    refuse(bot, message_id_answ, chat_id_answ)
                    bot.editMessageText(chat_id = chat_id, message_id = message_id, text = "Rifiutato.")
                    dataf.delete_pending_spot(candidate_message_id)
                    bot.answer_callback_query(query.id)

    except Exception as e:
        log_error("callback_spot", e)

# Function: update_spot
# Update the reactions button of a sent message
def update_spot(bot, message, spot_data):
    message_id = message.message_id
    dataf.save_spot_data(message_id, spot_data)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("%s %d" % ("👍", spot_data["user_reactions"]["u"]),\
                                        callback_data = "u"),\
                                        InlineKeyboardButton("%s %d" % ("👎", spot_data["user_reactions"]["d"]),\
                                        callback_data = "d" )]])
    bot.editMessageReplyMarkup(chat_id = message.chat_id, message_id = message_id, reply_markup = reply_markup, timeout = 1)


# Function: spot_edit
# Edit the reactions button of a sent message
def spot_edit(bot, message, query):
    try:
        message_id = message.message_id
        user_id = query.from_user.id

        spot_data = dataf.load_spot_data(message_id)

        user_id_s = str(user_id)

        if user_id_s in spot_data["voting_userids"].keys():
            past_react = spot_data["voting_userids"][user_id_s]

            if past_react == query.data :
                spot_data["user_reactions"][past_react] = spot_data["user_reactions"][past_react] - 1
                spot_data["voting_userids"].pop(user_id_s) 
                update_spot(bot, message, spot_data)               
                return

            spot_data["user_reactions"][past_react] = spot_data["user_reactions"][past_react] - 1
        
        spot_data["user_reactions"][query.data] = spot_data["user_reactions"][query.data] + 1
        spot_data["voting_userids"][user_id_s] = query.data

        update_spot(bot, message, spot_data)               
        bot.answerCallbackQuery(callback_query_id=query.id, text="Hai messo un %s" % ("👍" if query.data=="u" else "👎"))

    except Exception as e:
        log_error("edit", e)

def ban_cmd(bot, update, args):
    try:
        if update.message.chat_id == int(ADMINS_ID):
            user_id = args
            message = bot.sendMessage(chat_id = int(user_id[0]), text = "Sei stato bannato.")
            if message:
                f = open("data/banned.lst", "a+")
                f.write(user_id[0]+"\n")
    except Exception as e:
        log_error("ban", e)


# Function: comment_msg
# Makes a comment under the newly published spot to allow users to react to it
def comment_msg(bot, update):
    try:
        message = update.message
        if message.chat_id == int(COMMENTS_ID) and message.forward_from_chat.id == int(CHANNEL_ID):
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("👍", callback_data = "u"),\
                            InlineKeyboardButton("👎", callback_data = "d" )]])
            vote_message = bot.send_message(chat_id=message.chat_id, text="Vota lo spot", reply_markup=reply_markup, reply_to_message_id=message.message_id)
            dataf.add_spot_data(vote_message.message_id)
    except Exception as e:
        log_error("comment_msg", e)