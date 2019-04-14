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

# Token of your telegram bot that you created from @BotFather, write it on token.conf
TOKEN = tokenconf

# Bot functions

# Function: start_cmd
# Send message with bot's information
def start_cmd(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text = "Questo bot permette agli studenti di pubblicare\
     un messaggio una foto o un video nel canale @Spotted_DMI, in maniera anonima")

# Function: help_cmd
# Send help message
def help_cmd(bot, update):
    bot.sendMessage(chat_id = update.message.chat_id, text = "/spot: rispondi al bot per inviare una richiesta di approvazione al messaggio che vuoi spottare.\
                    \n\n/rules: un elenco di regole da rispettare nell'invio degli spot.")

# Function = rules_cmd
# Send message with bot rules
def rules_cmd(bot, update):
    rule = "**SPOTTED DMI BOT RULES**\n"
    rule1 = "**1.** Non è possibile utilizzare il bot per **pubblicare messaggi offensivi**.\n"
    rule2 = "**2.** Non è possibile **spoilerare, pubblicizzare o spammare**.\n"
    rule3 = "**3.** Non è possibile utilizzare il bot per pubblicare foto/video in cui appaiono **volti non censurati** o messaggi audio contenenti **nome e cognome** per intero.\n"
    rule4 = "**4.** È fortemente sconsigliato l'uso di abbreviazioni, forme semplificate, sincopate ed apocopate.\n"
    rule5 = "**5.** **Ogni abuso sarà punito.**"
    bot.sendMessage(chat_id = update.message.chat_id, text = rule + rule1 + rule2 + rule3 + rule4 + rule5, parse_mode='Markdown')

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
        print("spotcmd "+str(e))
        open("logs/errors.txt", "a+").write("spotcmd ",str(e)+"\n")        

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

                # sql_execute("INSERT INTO pending_spot (message_id, user_id, published)\
                #            VALUES (%d,%d,0)" % (message_id, chat_id))

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
                # bot.deleteMessage(chat_id = update.message.chat_id, message_id = update.message.message_id)
            else:
                bot.editMessageText(chat_id = update.message.chat_id, message_id = update.message.message_id,
                text = "Invia la proposta come messaggio di testo!|\n\n\n|%d|%d" % (message_id, chat_id))
    except Exception as e:
        print("message_handler "+str(e))
        open("logs/errors.txt", "a+").write("message_handler ",str(e)+"\n")        

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
        open("logs/errors.txt", "a+").write("handle ",str(e)+"\n")        

# Function: publish
# Publish the spotted message on the channel and send the user an acknowledgement
def publish(bot, message_id, chat_id):
    try:
        message = bot.sendMessage(chat_id = chat_id,\
                text = "Messaggio in fase di pubblicazione." ,\
                reply_to_message_id = message_id)

        handle_type(bot, message.reply_to_message, CHANNEL_ID)

        bot.editMessageText(chat_id = chat_id, message_id = message.message_id,\
                            text = "Il tuo messaggio è stato accettato e pubblicato!\
                                    \nCorri a guardare le reazioni su %s." % (CHANNEL_ID))

        # moved to "callback_spot"
        # sql_execute("DELETE FROM pending_spot\
        #             WHERE message_id = %d AND user_id = %d" % (message_id, chat_id))


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("publish ",str(e), fname, exc_tb.tb_lineno)
        open("logs/errors.txt", "a+").write("publish ",str(e)+"\n")        

# Function: refuse
# Acknowledge the user that the message has been refused
def refuse(bot, message_id, chat_id):
    try:
        bot.sendMessage(chat_id = chat_id,\
         text = "Il tuo messaggio è stato rifiutato. Controlla che rispetti gli standard del regolamento tramite il comando /rules .",\
                        reply_to_message_id = message_id)

        # sql_execute("DELETE FROM pending_spot\
        #    WHERE message_id = %d AND user_id = %d" % (message_id, chat_id))

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("publish ",str(e), fname, exc_tb.tb_lineno)
        open("logs/errors.txt", "a+").write("publish ",str(e)+"\n")        

# Function: callback_spot
# Handle the callback according to the Admin choise
def callback_spot(bot, update):
    try:
        query = update.callback_query
        data = query.data
        message = query.message
        message_id = message.message_id
        chat_id = message.chat.id

        candidate_message_id = message.reply_to_message.message_id

        # result = sql_execute("SELECT message_id, user_id FROM pending_spot WHERE published = 0")
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
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Proponi modifica", callback_data = "_p"),InlineKeyboardButton("Rifiuta", callback_data = "_r" )]])
                bot.editMessageText(chat_id = chat_id, message_id = message_id, text = "Vuoi proporre una modifica al messaggio?", reply_markup = reply_markup)
                bot.answer_callback_query(query.id)

            elif data[0] == "_":
                if data[1] == "r":
                    refuse(bot, message_id_answ, chat_id_answ)
                    bot.editMessageText(chat_id = chat_id, message_id = message_id, text = "Rifiutato.")

                elif data[1] == "p":
                    bot.deleteMessage(chat_id = chat_id, message_id = message_id)
                    bot.sendMessage(chat_id = chat_id,
                        message_id = message_id,
                        text = "Scrivi la modifica da proporre.|\n\n\n|%d|%d" % (message_id_answ, chat_id_answ),
                        reply_markup = ForceReply())

                # sql_execute("DELETE FROM pending_spot WHERE message_id = %d AND user_id = %d" % (message_id_answ, chat_id_answ))
                # bot.answer_callback_query(query.id)

        if data == "u" or data == "d":
            spot_edit(bot, message, query)
            bot.answer_callback_query(query.id)
    except Exception as e:
        print("callback_spot ",str(e))
        open("logs/errors.txt", "a+").write("callback_spot ",str(e)+"\n")
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # print("callback ",str(e), fname, exc_tb.tb_lineno)

# Function: spot_edit
# Edit the reactions button of a sent message
def spot_edit(bot,message,callback):
    try:
        message_id = message.message_id
        user_id = callback.from_user.id
        connection = sqlite3.connect("./data/spot.db")
        result = sql_execute("SELECT * FROM user_reactions\
                            WHERE message_id = %d AND user_id = %d" % (message_id, user_id), connection)

        if callback.data == "u":
            if result == []:
                pass
                # sql_execute("INSERT INTO user_reactions (message_id, user_id, thumbsup, thumbsdown)\
                #             VALUES (%d,%d,1,0)" % (message_id,user_id), connection)

            else:
                t_up = abs(result[0][2] - 1)
                t_down = result[0][3]
                if t_up == 1:
                    t_down = 0
                # sql_execute("UPDATE user_reactions \
                #            SET thumbsup = %d, thumbsdown = %d\
                #            WHERE message_id = %d AND user_id = %d" % (t_up, t_down, message_id, user_id), connection)

        else:
            if result == []:
                pass
                # sql_execute("INSERT INTO user_reactions (message_id, user_id, thumbsup, thumbsdown)\
                #             VALUES (%d,%d,0,1)" % (message_id, user_id), connection)

            else:
                t_down = abs(result[0][3] - 1)
                t_up = result[0][2]
                if t_down == 1:
                    t_up = 0

                # sql_execute("UPDATE user_reactions \
                #             SET thumbsdown = %d, thumbsup = %d\
                #             WHERE message_id = %d AND user_id = %d" % (t_down, t_up, message_id, user_id), connection)

        # count_u = sql_execute("SELECT COUNT (thumbsup) FROM user_reactions\
        #                        WHERE thumbsup = 1 AND message_id = %d" % (message_id), connection)[0][0]
        # count_d = sql_execute("SELECT COUNT (thumbsdown) FROM user_reactions\
        #                        # WHERE thumbsdown = 1 AND message_id = %d" % (message_id), connection)[0][0]

        connection.commit()
        connection.close()
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("%s %d" % ("👍",count_u),\
                                            callback_data = "u"),\
                                            InlineKeyboardButton("%s %d" % ("👎",count_d),\
                                            callback_data = "d" )]])
        bot.editMessageReplyMarkup(chat_id = message.chat_id, message_id = message_id, reply_markup = reply_markup, timeout = 0.001)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("edit ",str(e), fname, exc_tb.tb_lineno)
        open("logs/errors.txt", "a+").write("edit ",str(e)+"\n")

def ban_cmd(bot, update, args):
    try:
        if update.message.chat_id == int(ADMINS_ID):
            user_id = args
            message = bot.sendMessage(chat_id = int(user_id[0]), text = "Sei stato bannato.")
            if message:
                f = open("./data/banned.lst", "a+")
                f.write(user_id[0]+"\n")
    except Exception as e:
        print("ban "+str(e))
        open("logs/errors.txt", "a+").write("ban ",str(e)+"\n")        
