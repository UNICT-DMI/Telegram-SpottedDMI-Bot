"""Handles the execution of callbacks by the bot"""
from typing import Optional, Tuple
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.error import BadRequest, RetryAfter, Unauthorized
from modules.debug import logger
from modules.data import Config, PendingPost, PublishedPost, User
from modules.utils import EventInfo
from modules.utils.keyboard_util import REACTION, get_approve_kb, update_approve_kb, get_vote_kb, get_paused_kb


def old_reactions(data: str) -> str:
    """Used to maintain compatibility with the old reactions.
    Can be removed later

    Args:
        data: callback data

    Returns:
        new reaction data corresponding with the old reaction
    """
    if data == "meme_vote_yes":
        return "meme_vote,1"
    if data == "meme_vote_no":
        return "meme_vote,0"
    return data


def meme_callback(update: Update, context: CallbackContext) -> int:
    """Passes the meme callback to the correct handler

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        value to return to the handler, if requested
    """
    info = EventInfo.from_callback(update, context)
    data = old_reactions(info.query_data)
    # the callback data indicates the correct callback and the arg to pass to it separated by ,
    data = data.split(",")
    try:
        # call the correct function
        message_text, reply_markup, output = globals()[f'{data[0][5:]}_callback'](info, data[1])

    except KeyError as ex:
        message_text = reply_markup = output = None
        logger.error("meme_callback: %s", ex)

    try:
        # if there is a valid text, edit the menu with the new text
        if message_text and message_text != info.text:
            info.bot.edit_message_text(chat_id=info.chat_id,
                                       message_id=info.message_id,
                                       text=message_text,
                                       reply_markup=reply_markup)
        elif reply_markup:  # if there is a valid reply_markup, edit the menu with the new reply_markup
            info.edit_inline_keyboard(new_keyboard=reply_markup)
    except RetryAfter as ex:
        logger.warning(ex)

    return output


def settings_callback(info: EventInfo, arg: str) -> Tuple[Optional[str], None, None]:
    """Handles the settings,[ anonimo | credit ] callback.

    - anonimo: Removes the user_id from the table of credited users, if present.
    - credit: Adds the user_id to the table of credited users, if it wasn't already there.

    Args:
        info: information about the callback
        arg: [ anonimo | credit ]

    Returns:
        text and replyMarkup that make up the reply, new conversation state
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


def approve_status_callback(info: EventInfo, arg: None) -> Tuple[None, Optional[InlineKeyboardMarkup], None]:
    """Handles the approve_status callback.
    Pauses or resume voting on a specific pending post

    Args:
        info: information about the callback
        arg: [ pause | play ]

    Returns:
        text and replyMarkup that make up the reply, new conversation state
    """
    keyboard = None
    if arg == "pause":  # if the the admin wants to pause approval of the post
        keyboard = get_paused_kb()
    elif arg == "play":  # if the the admin wants to resume approval of the post
        pending_post = PendingPost.from_group(
            group_id=info.chat_id, g_message_id=info.message_id)
        if pending_post:
            keyboard = update_approve_kb(
                get_approve_kb().inline_keyboard, pending_post)
    else:
        logger.error("confirm_callback: invalid arg '%s'", arg)

    return None, keyboard, None


def autoreply_callback(info: EventInfo, arg: str) -> Tuple[None, None, None]:
    """Handles the autoreply callback.
    Reply to the user that requested the post

    Args:
        info: information about the callback
        arg: [ autoreply ]

    Returns:
        text and replyMarkup that make up the reply, new conversation state
    """

    all_autoreplies = Config.autoreplies_get('autoreplies')
    current_reply = all_autoreplies.get(arg)

    info.bot.send_message(chat_id=info.user_id, text=current_reply)

    return None, None, None


def approve_yes_callback(info: EventInfo, _: None) -> Tuple[None, Optional[InlineKeyboardMarkup], None]:
    """Handles the approve_yes callback.
    Approves the post, deleting it from the pending_post table, publishing it in the channel \
    and putting it in the published post table

    Args:
        info: information about the callback

    Returns:
        text and replyMarkup that make up the reply, new conversation state
    """
    pending_post = PendingPost.from_group(group_id=info.chat_id, g_message_id=info.message_id)
    if pending_post is None:  # this pending post is not present in the database
        return None, None, None

    info.answer_callback_query()  # end the spinning progress bar
    n_approve = pending_post.set_admin_vote(info.user_id, True)

    # The post passed the approval phase and is to be published
    if n_approve >= Config.meme_get('n_votes'):
        user_id = pending_post.user_id
        info.send_post_to_channel(user_id=user_id)

        try:
            info.bot.send_message(
                chat_id=user_id,
                text=f"Il tuo ultimo post è stato pubblicato su {Config.meme_get('channel_tag')}")  # notify the user
        except (BadRequest, Unauthorized) as ex:
            logger.warning("Notifying the user on approve_yes: %s", ex)

        # Shows the list of admins who approved the pending post and removes it form the db
        info.show_admins_votes(pending_post)
        pending_post.delete_post()
        return None, None, None

    if n_approve != -1:  # the vote changed
        keyboard = info.reply_markup.inline_keyboard
        return None, update_approve_kb(keyboard=keyboard, pending_post=pending_post, approve=n_approve), None

    return None, None, None


def approve_no_callback(info: EventInfo, _: None) -> Tuple[None, Optional[InlineKeyboardMarkup], None]:
    """Handles the approve_no callback.
    Rejects the post, deleting it from the pending_post table

    Args:
        info: information about the callback

    Returns:
        text and replyMarkup that make up the reply, new conversation state
    """
    pending_post = PendingPost.from_group(group_id=info.chat_id, g_message_id=info.message_id)
    if pending_post is None:  # this pending post is not present in the database
        return None, None, None

    info.answer_callback_query()  # end the spinning progress bar
    n_reject = pending_post.set_admin_vote(info.user_id, False)

    # The post has been refused
    if n_reject >= Config.meme_get('n_votes'):
        user_id = pending_post.user_id

        try:
            info.bot.send_message(
                chat_id=user_id,
                text="Il tuo ultimo post è stato rifiutato\nPuoi controllare le regole con /rules")  # notify the user
        except (BadRequest, Unauthorized) as ex:
            logger.warning("Notifying the user on approve_no: %s", ex)

        # Shows the list of admins who refused the pending post and removes it form the db
        info.show_admins_votes(pending_post)
        pending_post.delete_post()
        return None, None, None

    if n_reject != -1:  # the vote changed
        keyboard = info.reply_markup.inline_keyboard
        return None, update_approve_kb(keyboard=keyboard, pending_post=pending_post, reject=n_reject), None

    return None, None, None


def vote_callback(info: EventInfo, arg: str) -> Tuple[None, Optional[InlineKeyboardMarkup], None]:
    """Handles the vote,[ 0 | 1 | 2 | 3 | 4 ] callback.

    Args:
        info: information about the callback
        arg: [ 0 | 1 | 2 | 3 | 4 ]


    Returns:
        text and replyMarkup that make up the reply, new conversation state
    """
    published_post = PublishedPost.from_channel(channel_id=info.chat_id, c_message_id=info.message_id)
    if published_post is None:
        published_post = PublishedPost.create(channel_id=info.chat_id, c_message_id=info.message_id)
        published_post.set_votes(info.inline_keyboard)

    was_added = published_post.set_user_vote(user_id=info.user_id, vote=arg)

    if was_added:
        info.answer_callback_query(text=f"Hai messo un {REACTION[arg]}")
    else:
        info.answer_callback_query(text=f"Hai tolto il {REACTION[arg]}")

    return None, get_vote_kb(published_post=published_post), None
