"""Handles the execution of commands by the bot"""
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.error import BadRequest, Unauthorized
from modules.handlers import STATE
from modules.handlers.job_handlers import clean_pending_job
from modules.debug.log_manager import logger
from modules.data.data_reader import read_md, config_map
from modules.data.meme_data import MemeData
from modules.utils.info_util import get_message_info, check_message_type
from modules.utils.post_util import send_post_to
from modules.utils.keyboard_util import get_confirm_kb, get_settings_kb, get_stats_kb
from datetime import datetime

# region cmd
def start_cmd(update: Update, context: CallbackContext):
    """Handles the /start command.
    Sends a welcoming message

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    text = read_md("start")
    info['bot'].send_message(chat_id=info['chat_id'],
                             text=text,
                             parse_mode=ParseMode.MARKDOWN_V2,
                             disable_web_page_preview=True)


def help_cmd(update: Update, context: CallbackContext):
    """Handles the /help command.
    Sends an help message

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    if info['chat_id'] == config_map['meme']['group_id']:  # if you are in the admin group
        text = read_md("instructions")
    else:  # you are NOT in the admin group
        text = read_md("help")
    info['bot'].send_message(chat_id=info['chat_id'],
                             text=text,
                             parse_mode=ParseMode.MARKDOWN_V2,
                             disable_web_page_preview=True)


def rules_cmd(update: Update, context: CallbackContext):
    """Handles the /rules command.
    Sends a message containing the rules

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    text = read_md("rules")
    info['bot'].send_message(chat_id=info['chat_id'],
                             text=text,
                             parse_mode=ParseMode.MARKDOWN_V2,
                             disable_web_page_preview=True)


def settings_cmd(update: Update, context: CallbackContext):
    """Handles the /settings command.
    Let's the user choose whether his posts will be credited or not

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    if update.message.chat.type != "private":  # you can only post with a private message
        info['bot'].send_message(
            chat_id=info['chat_id'],
            text="Non puoi usare quest comando ora\nChatta con @tendTo_bot in privato",
        )
        return

    info['bot'].send_message(chat_id=info['chat_id'],
                             text="***Come vuoi che sia il tuo post:***",
                             reply_markup=get_settings_kb(),
                             parse_mode=ParseMode.MARKDOWN_V2)


def post_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the /post command.
    Checks that the user is in a private chat and it's not banned and start the post conversation

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = get_message_info(update, context)
    if update.message.chat.type != "private":  # you can only post with a private message
        info['bot'].send_message(
            chat_id=info['chat_id'],
            text="Non puoi usare quest comando ora\nChatta con @Spotted_DMI_bot in privato",
        )
        return STATE['end']

    if MemeData.is_banned(user_id=info['sender_id']):  # you are banned
        info['bot'].send_message(chat_id=info['chat_id'], text="Sei stato bannato 😅")
        return STATE['end']

    # have already a post in pending
    if MemeData.is_pending(user_id=info['sender_id']):
        info['bot'].send_message(chat_id=info['chat_id'], text="Hai già un post in approvazione 🧐")
        return STATE['end']

    info['bot'].send_message(chat_id=info['chat_id'], text="Invia il post che vuoi pubblicare")
    return STATE['posting']


def ban_cmd(update: Update, context: CallbackContext):
    """Handles the /ban command.
    Ban a user by replying to one of his pending posts with /ban

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    if info['chat_id'] == config_map['meme']['group_id']:  # you have to be in the admin group
        g_message_id = update.message.reply_to_message.message_id
        user_id = MemeData.get_user_id(g_message_id=g_message_id, group_id=info['chat_id'])

        if user_id is None:
            info['bot'].send_message(chat_id=info['chat_id'], text="Per bannare qualcuno, rispondi al suo post con /ban")
            return

        MemeData.ban_user(user_id=user_id)
        MemeData.remove_pending_meme(g_message_id=g_message_id, group_id=info['chat_id'])
        info['bot'].edit_message_reply_markup(chat_id=info['chat_id'], message_id=g_message_id)
        info['bot'].send_message(chat_id=info['chat_id'], text="L'utente è stato bannato")


def sban_cmd(update: Update, context: CallbackContext):
    """Handles the /sban command.
    Sban a user by using this command and listing all the user_id to sban

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    if info['chat_id'] == config_map['meme']['group_id']:  # you have to be in the admin group
        if len(context.args) == 0:  # if no args have been passed
            info['bot'].send_message(chat_id=info['chat_id'], text="[uso]: /sban <user_id1> [...user_id2]")
            return
        for user_id in context.args:
            # the sban was unsuccesful (maybe the user id was not found)
            if not MemeData.sban_user(user_id=user_id):
                break
        else:
            info['bot'].send_message(chat_id=info['chat_id'], text="Sban effettuato")
            return
        info['bot'].send_message(chat_id=info['chat_id'], text="Uno o più sban sono falliti")


def reply_cmd(update: Update, context: CallbackContext):
    """Handles the /reply command.
    Send a message to a user by replying to one of his pending posts with /reply + the message you want to send

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    if info['chat_id'] == config_map['meme']['group_id']:  # you have to be in the admin group
        g_message_id = update.message.reply_to_message.message_id
        user_id = MemeData.get_user_id(g_message_id=g_message_id, group_id=info['chat_id'])
        if user_id is None or len(info['text']) <= 7:
            info['bot'].send_message(
                chat_id=info['chat_id'],
                text=
                "Per mandare un messaggio ad un utente, rispondere al suo post con /reply seguito da ciò che gli si vuole dire"
            )
            return
        try:
            info['bot'].send_message(chat_id=user_id,
                                     text="COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n" + info['text'][7:].strip())
            info['bot'].send_message(chat_id=info['chat_id'],
                                 text="L'utente ha ricevuto il seguente messaggio:\n"\
                                    "COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n" + info['text'][7:].strip(),
                                 reply_to_message_id=g_message_id)
        except (BadRequest, Unauthorized) as e:
            logger.warning("Notifying the user on /reply: %s", e)


def clean_pending_cmd(update: Update, context: CallbackContext):
    """Handles the /clean_pending command.
    Automatically rejects all pending posts that are older than the chosen amount of hours

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    if info['chat_id'] == config_map['meme']['group_id']:  # you have to be in the admin group
        clean_pending_job(context=context)


def cancel_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the /cancel command.
    Exits from the post pipeline and removes the eventual pending post of the user

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = get_message_info(update, context)
    if update.message.chat.type != "private":  # you can only cancel a post with a private message
        return STATE['end']
    g_message_id, group_id = MemeData.cancel_pending_meme(user_id=info['sender_id'])
    if g_message_id is not None:
        info['bot'].delete_message(chat_id=group_id, message_id=g_message_id)
    info['bot'].send_message(chat_id=info['chat_id'], text="Operazione annullata")
    return STATE['end']


def stats_cmd(update: Update, context: CallbackContext):
    """Handles the /stats command.
    Lets the user choose what stats they want to see

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)

    info['bot'].send_message(chat_id=info['chat_id'], text="Che statistica ti interessa?", reply_markup=get_stats_kb())


# endregion


# region msg
def post_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /post command.
    Checks the message the user wants to post, and goes to the final step

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = get_message_info(update, context)

    if not check_message_type(update.message):  # the type is NOT supported
        info['bot'].send_message(
            chat_id=info['chat_id'],
            text="Questo tipo di messaggio non è supportato\nÈ consentito solo testo, stikers, immagini, audio, video o poll\n\
                Invia il post che vuoi pubblicare\nPuoi annullare il processo con /cancel")
        return STATE['posting']

    info['bot'].send_message(chat_id=info['chat_id'],
                             text="Sei sicuro di voler publicare questo post?",
                             reply_to_message_id=info['message_id'],
                             reply_markup=get_confirm_kb())
    return STATE['confirm']


def forwarded_post_msg(update: Update, context: CallbackContext):
    """Handles the post forwarded in the channel group.
    Sends a reply in the channel group and stores it in the database, so that the post can be voted

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    if update.message.forward_from_chat is None:
        return
    forward_from_chat_id = update.message.forward_from_chat.id
    forward_from_id = update.message.forward_from_message_id

    if info['chat_id'] == config_map['meme']['channel_group_id'] and forward_from_chat_id == config_map['meme']['channel_id']:
        user_id = context.bot_data[f"{forward_from_chat_id},{forward_from_id}"]
        send_post_to(message=update.message, bot=info['bot'], destination="channel_group", user_id=user_id)
        del context.bot_data[f"{forward_from_chat_id},{forward_from_id}"]


# endregion

# region report spot

def report_post(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the key "Report".
    Checks the message the user wants to report, and goes to the final step

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = get_message_info(update, context)

    if not check_message_type(update.message):  # the type is NOT supported
        info['bot'].send_message(
            chat_id=info['chat_id'],
            text="Questo tipo di messaggio non è supportato\nÈ consentito solo testo, stikers, immagini, audio, video o poll\n\
                Invia il post che vuoi pubblicare\nPuoi annullare il processo con /cancel")
        return STATE['reporting_spot']
    
    chat_id = config_map['meme']['group_id'] # should be admin group
    channel_id = config_map['meme']['channel_group_id'] # should be users group

    abusive_message_id = context.user_data['current_post_reported']

    MemeData.set_post_report(user_id=info['sender_id'], c_message_id=abusive_message_id)

    info['bot'].forward_message(chat_id=chat_id,
                                from_chat_id=channel_id,
                                message_id=abusive_message_id)
    info['bot'].sendMessage(chat_id=chat_id, 
                            text="🚨🚨 SEGNALAZIONE 🚨🚨\n\n" + info['text'])
    info['bot'].send_message(chat_id=info['chat_id'],
                            text="Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!")

    return STATE['end']

# endregion

# region report user

def report_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the key "Report".
    Checks the message the user wants to report

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = get_message_info(update, context)
    if update.message.chat.type != "private":  # you can only post with a private message
        info['bot'].send_message(
            chat_id=info['chat_id'],
            text="Non puoi usare quest comando ora\nChatta con @Spotted_DMI_bot in privato")
        return STATE['end']

    user_report = MemeData.get_user_report(user_id=info['sender_id'])

    if user_report:
        delta_time = datetime.now() - datetime.strptime(user_report['message_date'], "%Y-%m-%d %H:%M:%S.%f")
        delta_minutes = delta_time.total_seconds()/60
        remain_minutes = int(config_map['meme']['report_wait_mins'] - delta_minutes)

        if context.user_data['report_sent'] and remain_minutes > 0:
            info['bot'].send_message(chat_id=info['chat_id'], text=f"Aspetta {remain_minutes} minuti.")
            return STATE['end']

    info['bot'].send_message(chat_id=info['chat_id'], text="Invia l'username di chi vuoi segnalare. Es. @massimobene")

    return STATE['reporting_user']

def report_user_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /report command after sent the @username.
    Checks the the user wants to report, and goes to ask the reason

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = get_message_info(update, context)
    if not check_message_type(update.message) or not info['text'].startswith('@') or info['text'].find(' ') != -1:  # the type is NOT supported
        info['bot'].send_message(
            chat_id=info['chat_id'],
            text="Questo tipo di messaggio non è supportato\nÈ consentito solo username telegram. Puoi annullare il processo con /cancel")
        return STATE['reporting_user']

    context.user_data['current_report_target'] = info['text']
    context.user_data['report_sent'] = False

    info['bot'].send_message(
        chat_id=info['chat_id'],
        text="Scrivi il motivo della tua segnalazione.\n" +
            f"Cerca di essere esaustivo, potrai inviare un altro report dopo {config_map['meme']['report_wait_mins']} minuti.\nPuoi annullare il processo con /cancel")

    return STATE['sending_user_report']

def report_user_sent_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /report command after sent the reason.
    Checks the the user wants to report, and goes to final step

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = get_message_info(update, context)
    if not check_message_type(update.message):  # the type is NOT supported
        info['bot'].send_message(
            chat_id=info['chat_id'],
            text="Questo tipo di messaggio non è supportato\nÈ consentito solo testo, stikers, immagini, audio, video o poll\n\
                Invia il post che vuoi pubblicare\nPuoi annullare il processo con /cancel")
        return STATE['sending_user_report']
    
    target_username = context.user_data['current_report_target']
    
    MemeData.set_user_report(user_id=info['sender_id'], target_username=target_username)
    context.user_data['report_sent'] = True

    chat_id = config_map['meme']['group_id'] # should be admin group
    info['bot'].sendMessage(chat_id=chat_id, text="🚨🚨 SEGNALAZIONE 🚨🚨\n\n" +
                                            "Username: " + target_username+ "\n\n" +
                                            info['text'])
    info['bot'].send_message(
        chat_id=info['chat_id'],
        text="Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!")

    return STATE['end']
# end region
