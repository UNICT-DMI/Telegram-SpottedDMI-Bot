# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyMarkup,\
                    ForceReply, PhotoSize, Video
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters

#Utils
import json
import emoji
import sqlite3
import sys
import os

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
    try:
        chat_id = update.message.chat_id
        if update.message.chat.type == "group":
            bot.sendMessage(chat_id = chat_id, text = "Questo comando non è utilizzabile in un gruppo. Chatta con @botprova in privato")

        else:
            bot.sendMessage(chat_id = update.message.chat_id, text = "Invia un messaggio da spottare.",\
                            reply_markup = ForceReply())
    except Exception as e:
        print("spotcmd "+str(e))

#Function: spot_get
#Get the user text or media response to spot_cmd and forward it to the Admin chat
def spot_get(bot, update):
    try:

        if update.message.reply_to_message.text == "Invia un messaggio da spottare.":
            available, message_reply = handle_type(bot, update.message, ADMINS_ID)

            if available:
                message_id = update.message.message_id
                chat_id = update.message.chat_id
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Sì",callback_data = '0'),\
                                                    InlineKeyboardButton("No", callback_data = '1')]])
                # reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Sì",callback_data = '0 %s %s' % (str(update.message.message_id),str(update.message.chat_id)) ),\
                #                                     InlineKeyboardButton("No", callback_data = '1 %s %s' % (str(update.message.message_id),str(update.message.chat_id)))]])


                bot.sendMessage(chat_id = ADMINS_ID,\
                                    text = "Pubblicare il seguente messaggio?",\
                                    reply_markup = reply_markup, reply_to_message_id = message_reply.message_id)

                sql_execute("INSERT INTO pending_spot (message_id, user_id, published)\
                            VALUES (%d,%d,0)" % (message_id, chat_id))

                bot.sendMessage(chat_id = chat_id, text = "Il tuo messaggio è in fase di valutazione.\
                                                        \nTi informeremo non appena verrà analizzato.")
            else:
                bot.sendMessage(chat_id = chat_id, text = "È possibile solo inviare messaggi di testo,"+\
                " immagini, audio o video")
    except Exception as e:
        print("spotget "+str(e))

#Function: handle_type
#Return True if the message is a text a photo, a voice, an audio or a video; False otherwise
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
        if chat_id == CHANNEL_ID:
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("👍", callback_data = "u"),\
                                            InlineKeyboardButton("👎", callback_data = "d" )]])
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
        print("handle "+str(e))

#Function: publish
#Publish the spotted message on the channel and send the user an acknowledgement
def publish(bot, message_id, chat_id):
    try:
        message = bot.sendMessage(chat_id = chat_id,\
                text = "Messaggio in fase di pubblicazione." ,\
                reply_to_message_id = message_id)


        handle_type(bot, message.reply_to_message, CHANNEL_ID)
        sql_execute("UPDATE pending_spot\
                    SET published = 1\
                    WHERE message_id = %d AND user_id = %d" % (message_id, chat_id))
        bot.editMessageText(chat_id = chat_id, message_id = message.message_id,\
                            text = "Il tuo messaggio è stato accettato e pubblicato!\
                                    \nCorri a guardare le reazioni su %s." % (CHANNEL_ID))
        sql_execute("DELETE FROM pending_spot\
                    WHERE message_id = %d AND user_id = %d" % (message_id, chat_id))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("publish ",str(e), fname, exc_tb.tb_lineno)

#Function: refuse
#Acknowledge the user that the message has been refused
def refuse(bot, message_id, chat_id):
    try:
        bot.sendMessage(chat_id = chat_id, text = "Il tuo messaggio è stato rifiutato.",\
                        reply_to_message_id = message_id)
        sql_execute("DELETE FROM pending_spot\
                    WHERE message_id = %d AND user_id = %d" % (message_id, chat_id))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("publish ",str(e), fname, exc_tb.tb_lineno)

#Function: callback_spot
#Handle the callback according to the Admin choise
def callback_spot(bot, update):
    try:
        query = update.callback_query
        data = query.data
        message = query.message
        reply = message.reply_to_message
        message_id = message.message_id
        chat_id = message.chat.id

        result = sql_execute("SELECT message_id, user_id FROM pending_spot\
                                WHERE published = 0")
        if not result == []:
            message_id_answ = result[0][0]
            chat_id_answ = result[0][1]

        if data == "0":
            publish(bot, message_id_answ, chat_id_answ)
            bot.editMessageText(chat_id = chat_id, message_id = message_id, text = "Pubblicato")
            bot.answer_callback_query(query.id)

        elif data == "1":
            refuse(bot, message_id_answ, chat_id_answ)
            bot.editMessageText(chat_id = chat_id, message_id = message_id, text = "Rifiutato")
            bot.answer_callback_query(query.id)
        else:
            spot_edit(bot, message, query)
            bot.answer_callback_query(query.id)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("callback ",str(e), fname, exc_tb.tb_lineno)


def spot_edit(bot,message,callback):
    try:
        message_id = message.message_id
        user_id = callback.from_user.id
        connection = sqlite3.connect("./data/spot.db")
        result = sql_execute("SELECT * FROM user_reactions\
                            WHERE message_id = %d AND user_id = %d" % (message_id, user_id), connection)

        if callback.data == "u":
            if result == []:
                sql_execute("INSERT INTO user_reactions (message_id, user_id, thumbsup, thumbsdown)\
                            VALUES (%d,%d,1,0)" % (message_id,user_id), connection)

            else:
                t_up = abs(result[0][2] - 1)
                t_down = result[0][3]
                if t_up == 1:
                    t_down = 0
                sql_execute("UPDATE user_reactions \
                            SET thumbsup = %d, thumbsdown = %d\
                            WHERE message_id = %d AND user_id = %d" % (t_up, t_down, message_id, user_id), connection)

        else:
            if result == []:
                sql_execute("INSERT INTO user_reactions (message_id, user_id, thumbsup, thumbsdown)\
                            VALUES (%d,%d,0,1)" % (message_id, user_id), connection)

            else:
                t_down = abs(result[0][3] - 1)
                t_up = result[0][2]
                if t_down == 1:
                    t_up = 0
                sql_execute("UPDATE user_reactions \
                            SET thumbsdown = %d, thumbsup = %d\
                            WHERE message_id = %d AND user_id = %d" % (t_down, t_up, message_id, user_id), connection)

        count_u = sql_execute("SELECT COUNT (thumbsup) FROM user_reactions\
                                WHERE thumbsup = 1 AND message_id = %d" % (message_id), connection)[0][0]
        count_d = sql_execute("SELECT COUNT (thumbsdown) FROM user_reactions\
                                WHERE thumbsdown = 1 AND message_id = %d" % (message_id), connection)[0][0]
        connection.commit()
        connection.close()
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("%s %d" % ("👍",count_u),\
                                            callback_data = "u"),\
                                            InlineKeyboardButton("%s %d" % ("👎",count_d),\
                                            callback_data = "d" )]])
        bot.editMessageReplyMarkup(chat_id = message.chat_id, message_id = message_id, reply_markup = reply_markup, timeout = 500)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("edit ",str(e), fname, exc_tb.tb_lineno)

def sql_execute(sql_query, connection = None):
    try:
        connected = True
        if not connection:
            connection = sqlite3.connect("./data/spot.db")
            connected = False

        cursor = connection.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
        if connected == False:
            connection.commit()
            connection.close()

        return result
    except sqlite3.Error as e:
            print("Database error: %s" % e)
    except Exception as e:
        print("sql "+str(e))
