"""Commands for the meme bot"""
from typing import Tuple
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.error import BadRequest, Unauthorized
from modules.debug.log_manager import logger
from modules.data.data_reader import config_map
from modules.data.meme_data import MemeData
from modules.utils.info_util import get_callback_info
from modules.utils.keyboard_util import update_approve_kb, update_vote_kb
from modules.utils.post_util import send_post_to, show_admins_votes

STATE = {'posting': 1, 'confirm': 2, 'end': -1}


def meme_callback(update: Update, context: CallbackContext) -> int:
    """Passes the callback to the correct handler

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: value passed to the handler, if requested
    """
    info = get_callback_info(update, context)
    data = info['data']
    try:
        message_text, reply_markup, output = globals()[f'{data[5:]}_callback'](info)  # call the function based on its name
    except KeyError as e:
        message_text = reply_markup = output = None
        logger.error("meme_callback: %s", e)

    if message_text:  # if there is a valid text, edit the menu with the new text
        info['bot'].edit_message_text(chat_id=info['chat_id'],
                                      message_id=info['message_id'],
                                      text=message_text,
                                      reply_markup=reply_markup)
    elif reply_markup:  # if there is a valid reply_markup, edit the menu with the new reply_markup
        info['bot'].edit_message_reply_markup(chat_id=info['chat_id'],
                                              message_id=info['message_id'],
                                              reply_markup=reply_markup)
    return output


# region handle meme_callback
def confirm_yes_callback(info: dict) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the confirm_yes callback.
    Saves the post as pending and sends it to the admins for them to check

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    user_message = info['message'].reply_to_message
    admin_message = send_post_to(message=user_message, bot=info['bot'], destination="admin")
    if admin_message:
        text = "Il tuo post è in fase di valutazione\n"\
            "Una volta pubblicato, lo potrai trovare su @Spotted_DMI"
    else:
        text = "Si è verificato un problema\nAssicurati che il tipo di post sia fra quelli consentiti"
    return text, None, STATE['end']


def confirm_no_callback(info: dict) -> Tuple[str, InlineKeyboardMarkup, int]:  # pylint: disable=unused-argument
    """Handles the confirm_no callback.
    Saves the post as pending and sends it to the admins for them to check

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    message_text = "Va bene, alla prossima 🙃"
    return message_text, None, STATE['end']


def settings_anonimo_callback(info: dict) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the settings_sei_ghei callback.
    Removes the user_id from the table of credited users, if present

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    # if the user was already anonym
    if MemeData.become_anonym(user_id=info['sender_id']):
        text = "Sei già anonimo"
    else:
        text = "La tua preferenza è stata aggiornata\n"\
            "Ora i tuoi post saranno anonimi"

    return text, None, None


def settings_credit_callback(info: dict) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the settings_foto_cane callback.
    Adds the user_id to the table of credited users, if it wasn't already there

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    # if the user was already credited
    if MemeData.become_credited(user_id=info['sender_id']):
        text = "Sei già creditato nei post\n"
    else:
        text = "La tua preferenza è stata aggiornata\n"

    if info['sender_username']:  # the user has a valid username
        text += f"I tuoi post avranno come credit @{info['sender_username']}"
    else:
        text += "ATTENZIONE:\nNon hai nessun username associato al tuo account telegram\n"\
            "Se non lo aggiungi, non sarai creditato"
    return text, None, None


def approve_yes_callback(info: dict) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the approve_yes callback.
    Approves the post, deleting it from the pending_post table, publishing it in the channel \
    and putting it in the published post table

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    n_approve = MemeData.set_admin_vote(info['sender_id'], info['message_id'], info['chat_id'], True)

    # The post passed the approval phase and is to be published
    if n_approve >= config_map['meme']['n_votes']:
        message = info['message']
        user_id = MemeData.get_user_id(g_message_id=info['message_id'], group_id=info['chat_id'])
        published_post = send_post_to(message=message, bot=info['bot'], destination="channel")

        if config_map['meme']['comments']:  # if comments are enabled, save the user_id, so the user can be credited
            info['bot_data'][f"{published_post.chat_id},{published_post.message_id}"] = user_id

        try:
            info['bot'].send_message(chat_id=user_id,
                                     text="Il tuo ultimo post è stato pubblicato su @Spotted_DMI")  # notify the user
        except (BadRequest, Unauthorized) as e:
            logger.warning("Notifying the user on approve_yes: %s", e)

        # Shows the list of admins who approved the pending post and removes it form the db
        show_admins_votes(chat_id=info['chat_id'], message_id=info['message_id'], bot=info['bot'], approve=True)
        MemeData.remove_pending_meme(info['message_id'], info['chat_id'])
        return None, None, None

    if n_approve != -1:  # the vote changed
        keyboard = info['reply_markup'].inline_keyboard
        return None, update_approve_kb(keyboard, info['message_id'], info['chat_id'], approve=n_approve), None

    return None, None, None


def approve_no_callback(info: dict) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the approve_no callback.
    Rejects the post, deleting it from the pending_post table

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    n_reject = MemeData.set_admin_vote(info['sender_id'], info['message_id'], info['chat_id'], False)

    # The post has been refused
    if n_reject >= config_map['meme']['n_votes']:
        user_id = MemeData.get_user_id(g_message_id=info['message_id'], group_id=info['chat_id'])

        try:
            info['bot'].send_message(
                chat_id=user_id,
                text="Il tuo ultimo post è stato rifiutato\nPuoi controllare le regole con /rules")  # notify the user
        except (BadRequest, Unauthorized) as e:
            logger.warning("Notifying the user on approve_no: %s", e)

        # Shows the list of admins who refused the pending post and removes it form the db
        show_admins_votes(chat_id=info['chat_id'], message_id=info['message_id'], bot=info['bot'], approve=False)
        MemeData.remove_pending_meme(info['message_id'], info['chat_id'])
        return None, None, None

    if n_reject != -1:  # the vote changed
        keyboard = info['reply_markup'].inline_keyboard
        return None, update_approve_kb(keyboard, info['message_id'], info['chat_id'], reject=n_reject), None

    return None, None, None


def vote_yes_callback(info: dict) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the vote_yes callback.
    Upvotes the post

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    n_upvotes, was_added = MemeData.set_user_vote(user_id=info['sender_id'],
                                                  c_message_id=info['message_id'],
                                                  channel_id=info['chat_id'],
                                                  vote=True)

    if n_upvotes != -1:  # the vote changed
        if was_added:
            info['bot'].answerCallbackQuery(callback_query_id=info['query_id'], text="Hai messo un 👍")
        else:
            info['bot'].answerCallbackQuery(callback_query_id=info['query_id'], text="Hai tolto il 👍")
        keyboard = info['reply_markup'].inline_keyboard
        return None, update_vote_kb(keyboard, info['message_id'], info['chat_id'], upvote=n_upvotes), None

    return None, None, None


def vote_no_callback(info: dict) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the vote_no callback.
    Downvotes the post

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    n_downvotes, was_added = MemeData.set_user_vote(user_id=info['sender_id'],
                                                    c_message_id=info['message_id'],
                                                    channel_id=info['chat_id'],
                                                    vote=False)

    if n_downvotes != -1:  # the vote changed
        if was_added:
            info['bot'].answerCallbackQuery(callback_query_id=info['query_id'], text="Hai messo un 👎")
        else:
            info['bot'].answerCallbackQuery(callback_query_id=info['query_id'], text="Hai tolto il 👎")
        keyboard = keyboard = info['reply_markup'].inline_keyboard
        return None, update_vote_kb(keyboard, info['message_id'], info['chat_id'], downvote=n_downvotes), None

    return None, None, None


# endregion
