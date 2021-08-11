"""Handles the execution of callbacks by the bot"""
from typing import Tuple
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from telegram.error import BadRequest, RetryAfter, Unauthorized
from modules.debug import logger
from modules.data import config_map, PendingPost, PublishedPost, User
from modules.utils import EventInfo
from modules.utils.keyboard_util import REACTION, get_approve_kb, update_approve_kb, get_vote_kb


def old_reactions(data: str) -> str:
    """Used to mantain compatibility with the old reactions.
    Can be removed later

    Args:
        data (str): callback data

    Returns:
        str: new reaction data corrisponding with the old reaction
    """
    if data == "meme_vote_yes":
        return "meme_vote,1"
    if data == "meme_vote_no":
        return "meme_vote,0"
    return data


def meme_callback(update: Update, context: CallbackContext) -> int:
    """Passes the meme callback to the correct handler

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: value to return to the handler, if requested
    """
    info = EventInfo.from_callback(update, context)
    data = old_reactions(info.query_data)
    # the callback data indicates the correct callback and the arg to pass to it separated by ,
    data = data.split(",")
    try:
        # call the correct function
        message_text, reply_markup, output = globals()[f'{data[0][5:]}_callback'](info, data[1])

    except KeyError as e:
        message_text = reply_markup = output = None
        logger.error("meme_callback: %s", e)

    try:
        if message_text:  # if there is a valid text, edit the menu with the new text
            info.bot.edit_message_text(chat_id=info.chat_id,
                                       message_id=info.message_id,
                                       text=message_text,
                                       reply_markup=reply_markup)
        elif reply_markup:  # if there is a valid reply_markup, edit the menu with the new reply_markup
            info.edit_inline_keyboard(new_keyboard=reply_markup)
    except RetryAfter as e:
        logger.warning(e)

    return output


# region handle meme_callback
def settings_callback(info: EventInfo, arg: str) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the settings,[ anonimo | credit ] callback.

    - anonimo: Removes the user_id from the table of credited users, if present.
    - credit: Adds the user_id to the table of credited users, if it wasn't already there.

    Args:
        info (dict): information about the callback
        arg (str): [ anonimo | credit ]

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    user = User(info.user_id)
    if arg == "anonimo":  # if the user wants to be anonym
        # if the user was already anonym
        if user.become_anonym():
            text = "Sei già anonimo"
        else:
            text = "La tua preferenza è stata aggiornata\n"\
                "Ora i tuoi post saranno anonimi"

    elif arg == "credit":  # if the user wants to be credited
        if user.become_credited():
            text = "Sei già creditato nei post\n"
        else:
            text = "La tua preferenza è stata aggiornata\n"

        if info.user_username:  # the user has a valid username
            text += f"I tuoi post avranno come credit @{info.user_username}"
        else:
            text += "ATTENZIONE:\nNon hai nessun username associato al tuo account telegram\n"\
                "Se non lo aggiungi, non sarai creditato"
    else:
        text = None
        logger.error("settings_callback: invalid arg '%s'", arg)

    return text, None, None


def approve_status_callback(info: EventInfo, arg: None) -> Tuple[str, InlineKeyboardMarkup, int]:  # pylint: disable=unused-argument
    """Handles the approve_status callback.
    Pauses or resume voting on a specific pending post

    Args:
        info (dict): information about the callback
        arg (str): [ pause | play ]

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    if arg == "pause":  # if the the admin wants to pause approval of the post
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text="▶️ Resume", callback_data="meme_approve_status,play")]])
    elif arg == "play":  # if the the admin wants to resume approval of the post
        pending_post = PendingPost.from_group(group_id=info.chat_id, g_message_id=info.message_id)
        keyboard = update_approve_kb(get_approve_kb().inline_keyboard, pending_post)
    else:
        keyboard = None
        logger.error("confirm_callback: invalid arg '%s'", arg)

    return None, keyboard, None


def approve_yes_callback(info: EventInfo, arg: None) -> Tuple[str, InlineKeyboardMarkup, int]:  # pylint: disable=unused-argument
    """Handles the approve_yes callback.
    Approves the post, deleting it from the pending_post table, publishing it in the channel \
    and putting it in the published post table

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    pending_post = PendingPost.from_group(group_id=info.chat_id, g_message_id=info.message_id)
    if pending_post is None:  # this pending post is not present in the database
        return None, None, None

    info.answer_callback_query()  # end the spinning progress bar
    n_approve = pending_post.set_admin_vote(info.user_id, True)

    # The post passed the approval phase and is to be published
    if n_approve >= config_map['meme']['n_votes']:
        user_id = pending_post.user_id
        info.send_post_to_channel(user_id=user_id)

        try:
            info.bot.send_message(
                chat_id=user_id,
                text=f"Il tuo ultimo post è stato pubblicato su {config_map['meme']['channel_tag']}")  # notify the user
        except (BadRequest, Unauthorized) as e:
            logger.warning("Notifying the user on approve_yes: %s", e)

        # Shows the list of admins who approved the pending post and removes it form the db
        pending_post.show_admins_votes(bot=info.bot, approve=True)
        pending_post.delete_post()
        return None, None, None

    if n_approve != -1:  # the vote changed
        keyboard = info.reply_markup.inline_keyboard
        return None, update_approve_kb(keyboard=keyboard, pending_post=pending_post, approve=n_approve), None

    return None, None, None


def approve_no_callback(info: EventInfo, arg: None) -> Tuple[str, InlineKeyboardMarkup, int]:  # pylint: disable=unused-argument
    """Handles the approve_no callback.
    Rejects the post, deleting it from the pending_post table

    Args:
        info (dict): information about the callback

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    pending_post = PendingPost.from_group(group_id=info.chat_id, g_message_id=info.message_id)
    if pending_post is None:  # this pending post is not present in the database
        return None, None, None

    info.answer_callback_query()  # end the spinning progress bar
    n_reject = pending_post.set_admin_vote(info.user_id, False)

    # The post has been refused
    if n_reject >= config_map['meme']['n_votes']:
        user_id = pending_post.user_id

        try:
            info.bot.send_message(
                chat_id=user_id,
                text="Il tuo ultimo post è stato rifiutato\nPuoi controllare le regole con /rules")  # notify the user
        except (BadRequest, Unauthorized) as e:
            logger.warning("Notifying the user on approve_no: %s", e)

        # Shows the list of admins who refused the pending post and removes it form the db
        pending_post.show_admins_votes(bot=info.bot, approve=False)
        pending_post.delete_post()
        return None, None, None

    if n_reject != -1:  # the vote changed
        keyboard = info.reply_markup.inline_keyboard
        return None, update_approve_kb(keyboard=keyboard, pending_post=pending_post, reject=n_reject), None

    return None, None, None


def vote_callback(info: EventInfo, arg: str) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the vote,[ 0 | 1 | 2 | 3 | 4 ] callback.

    Args:
        info (dict): information about the callback
        arg (str): [ 0 | 1 | 2 | 3 | 4 ]


    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    publishedPost = PublishedPost.from_channel(channel_id=info.chat_id, c_message_id=info.message_id)
    if publishedPost is None:
        publishedPost = PublishedPost.create(channel_id=info.chat_id, c_message_id=info.message_id)
        publishedPost.set_votes(info.inline_keyboard)

    was_added = publishedPost.set_user_vote(user_id=info.user_id, vote=arg)

    if was_added:
        info.answer_callback_query(text=f"Hai messo un {REACTION[arg]}")
    else:
        info.answer_callback_query(text=f"Hai tolto il {REACTION[arg]}")

    return None, get_vote_kb(published_post=publishedPost), None




# endregion





# endregion
