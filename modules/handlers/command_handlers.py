"""Commands for the meme bot"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from modules.data.data_reader import read_md, config_map
from modules.data.meme_data import MemeData
from modules.utils.info_util import get_message_info, check_message_type
from modules.utils.post_util import send_post_to

STATE = {'posting': 1, 'confirm': 2, 'end': -1}


# region cmd
def start_cmd(update: Update, context: CallbackContext):
    """Handles the /start command

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
    """Handles the /help command

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
    """Handles the /rules command

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
    """Handles the /settings command

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

    keyboard = [[
        InlineKeyboardButton(" Anonimo ", callback_data="meme_settings_anonimo"),
        InlineKeyboardButton(" Con credit ", callback_data="meme_settings_credit"),
    ]]

    info['bot'].send_message(chat_id=info['chat_id'],
                             text="***Come vuoi che sia il tuo post:***",
                             reply_markup=InlineKeyboardMarkup(keyboard),
                             parse_mode=ParseMode.MARKDOWN_V2)


def post_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the /post command
    Checks that the user is in a private chat and it's not banned and start the post process

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: value passed to the handler, if requested
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
    """Handles the /ban command
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
    """Handles the /sban command
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
    """Handles the /reply command
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
        info['bot'].send_message(chat_id=user_id,
                                 text="COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n" + info['text'][7:].strip())
        info['bot'].send_message(chat_id=info['chat_id'],
                                 text="L'utente ha ricevuto il seguente messaggio:\n"\
                                    "COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n" + info['text'][7:].strip(),
                                 reply_to_message_id=g_message_id)


def cancel_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /cancel command.
    Exit from the post pipeline

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: value passed to the handler, if requested
    """
    info = get_message_info(update, context)

    info['bot'].send_message(chat_id=info['chat_id'], text="Post annullato")
    return STATE['end']


# endregion


# region msg
def post_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /post command.
    Checks the message the user wants to post, and goes to the final step

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: value passed to the handler, if requested
    """
    info = get_message_info(update, context)

    if not check_message_type(update.message):  # the type is NOT supported
        info['bot'].send_message(
            chat_id=info['chat_id'],
            text="Questo tipo di messaggio non è supportato\nÈ consentito solo testo, stikers, immagini, audio o video\n\
                Invia il post che vuoi pubblicare\nPuoi annullare il processo con /cancel",
        )
        return STATE['posting']

    info['bot'].send_message(chat_id=info['chat_id'],
                             text="Sei sicuro di voler publicare questo post?",
                             reply_to_message_id=info['message_id'],
                             reply_markup=InlineKeyboardMarkup([[
                                 InlineKeyboardButton(text="Si", callback_data="meme_confirm_yes"),
                                 InlineKeyboardButton(text="No", callback_data="meme_confirm_no")
                             ]]))
    return STATE['confirm']


def forwarded_post_msg(update: Update, context: CallbackContext):
    """Handles the post forwarded in the channel group.
    Sends a reply in the channel group and stores it in the database, so that the post can be voted

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = get_message_info(update, context)
    forward_from_chat_id = update.message.forward_from_chat.id
    forward_from_id = update.message.forward_from_message_id

    if info['chat_id'] == config_map['meme']['channel_group_id'] and forward_from_chat_id == config_map['meme']['channel_id']:
        user_id = context.bot_data[f"{forward_from_chat_id},{forward_from_id}"]
        send_post_to(message=update.message, bot=info['bot'], destination="channel_group", user_id=user_id)
        del context.bot_data[f"{forward_from_chat_id},{forward_from_id}"]


# endregion
