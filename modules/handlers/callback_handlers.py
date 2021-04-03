"""Handles the execution of callbacks by the bot"""
from typing import Tuple
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.error import BadRequest, RetryAfter, Unauthorized
from modules.handlers import STATE
from modules.debug import logger
from modules.data import config_map, PendingPost, PublishedPost, PostData, Report, User
from modules.utils import EventInfo
from modules.utils.keyboard_util import REACTION, update_approve_kb, get_vote_kb, get_stats_kb


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
            info.bot.edit_message_reply_markup(chat_id=info.chat_id, message_id=info.message_id, reply_markup=reply_markup)
    except RetryAfter as e:
        logger.warning(e)

    return output


# region handle meme_callback
def confirm_callback(info: EventInfo, arg: str) -> Tuple[str, InlineKeyboardMarkup, int]:
    """Handles the confirm,[ yes | no ] callback.

    - yes: Saves the post as pending and sends it to the admins for them to check.
    - no: cancel the current spot conversation

    Args:
        info (dict): information about the callback
        arg (str): [ yes | no ]

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """
    if arg == "yes":  # if the the user wants to publish the post
        if User(info.user_id).is_pending:  # there is already a spot in pending by this user
            return None, None, STATE['end']

        if info.send_post_to_admins():
            text = "Il tuo post è in fase di valutazione\n"\
                f"Una volta pubblicato, lo potrai trovare su {config_map['meme']['channel_tag']}"
        else:
            text = "Si è verificato un problema\nAssicurati che il tipo di post sia fra quelli consentiti"

    elif arg == "no":  # if the the user changed his mind
        text = "Va bene, alla prossima 🙃"

    else:
        text = None
        logger.error("confirm_callback: invalid arg '%s'", arg)

    return text, None, STATE['end']


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
    was_added = publishedPost.set_user_vote(user_id=info.user_id, vote=arg)

    if was_added:
        info.answer_callback_query(text=f"Hai messo un {REACTION[arg]}")
    else:
        info.answer_callback_query(text=f"Hai tolto il {REACTION[arg]}")

    return None, get_vote_kb(published_post=publishedPost), None


def report_spot_callback(info: EventInfo, args: str) -> Tuple[str, InlineKeyboardMarkup, int]:  # pylint: disable=unused-argument
    """Handles the report callback.

    Args:
        info (dict): information about the callback
        arg (str): unused

    Returns:
        Tuple[str, InlineKeyboardMarkup, int]: text and replyMarkup that make up the reply, new conversation state
    """

    abusive_message_id = info.message.reply_to_message.message_id

    report = Report.get_post_report(user_id=info.user_id,
                                    channel_id=config_map['meme']['channel_id'],
                                    c_message_id=abusive_message_id)
    if report is not None:  # this user has already reported this post
        info.answer_callback_query(text="Hai già segnalato questo spot.")
        return None, None, STATE['end']
    try:
        info.bot.forward_message(chat_id=info.user_id, from_chat_id=info.chat_id, message_id=abusive_message_id)
        info.bot.send_message(chat_id=info.user_id,
                              text="Scrivi il motivo della segnalazione del post, altrimenti digita /cancel")
        info.answer_callback_query(text="Segnala in privato tramite il bot")
    except Unauthorized:
        info.answer_callback_query(text=f"Assicurati di aver avviato la chat con {config_map['bot_tag']}")
        return None, None, None

    info.user_data['current_post_reported'] = abusive_message_id

    return None, None, STATE['reporting_spot']


# endregion


def stats_callback(update: Update, context: CallbackContext):
    """Passes the stats callback to the correct handler

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_callback(update, context)
    info.answer_callback_query()  # end the spinning progress bar
    # the callback data indicates the correct callback and the arg to pass to it separated by ,
    data = info.query_data.split(",")
    try:
        message_text = globals()[f'{data[0][6:]}_callback'](data[1])  # call the function based on its name
    except KeyError as e:
        logger.error("stats_callback: %s", e)
        return

    if message_text:  # if there is a valid text, edit the menu with the new text
        info.bot.edit_message_text(chat_id=info.chat_id,
                                   message_id=info.message_id,
                                   text=message_text,
                                   reply_markup=get_stats_kb())
    else:  # remove the reply markup
        info.bot.edit_message_reply_markup(chat_id=info.chat_id, message_id=info.message_id, reply_markup=None)


# region handle stats_callback
def avg_callback(arg: str) -> str:
    """Handles the avg_[ votes | 0 | 1 ] callback.
    Shows the average of the %arg per post

    Args:
        arg (str): [ votes | 0 | 1 ]

    Returns:
        str: text for the reply
    """
    if arg == "votes":
        avg_votes = PostData.get_avg()
        text = f"Gli spot ricevono in media {avg_votes} voti"
    else:
        avg_votes = PostData.get_avg(arg)
        text = f"Gli spot ricevono in media {avg_votes} {REACTION[arg]}"

    return text


def max_callback(arg: str) -> str:
    """Handles the max_[ votes | 0 | 1 ] callback
    Shows the post with the most %arg

    Args:
        arg (str): [ votes | 0 | 1 ]

    Returns:
        str: text for the reply
    """
    if arg == "votes":
        max_votes, message_id, channel_id = PostData.get_max_id()
        text = f"Lo spot con più voti ne ha {max_votes}\n"\
            f"Lo trovi a questo link: https://t.me/c/{channel_id[4:]}/{message_id}"
    else:
        max_votes, message_id, channel_id = PostData.get_max_id(arg)
        text = f"Lo spot con più {REACTION[arg]} ne ha {max_votes}\n" \
            f"Lo trovi a questo link: https://t.me/c/{channel_id[4:]}/{message_id}"

    return text


def tot_callback(arg: str) -> str:
    """Handles the tot_[ posts | votes | 0 | 1 ] callback
    Shows the total number of %arg

    Args:
        arg (str): [ posts | votes | 0 | 1 ]

    Returns:
        str: text for the reply
    """
    if arg == "posts":
        n_posts = PostData.get_n_posts()
        text = f"Sono stati pubblicati {n_posts} spot nel canale fin'ora.\nPotresti ampliare questo numero..."
    elif arg == "votes":
        n_votes = PostData.get_n_votes()
        text = f"Il totale dei voti ammonta a {n_votes}"
    else:
        n_votes = PostData.get_n_votes(arg)
        text = f"Il totale dei {REACTION[arg]} ammonta a {n_votes}"

    return text


def close_callback(arg: None) -> str:  # pylint: disable=unused-argument
    """Handles the close callback
    Closes the stats menu

    Returns:
        str: text and replyMarkup that make up the reply
    """
    return None

def comment_callback(info: EventInfo, args: str) -> Tuple[str, InlineKeyboardMarkup, int]:  # pylint: disable=unused-argument
    """Handles the comment callback
    Opens the thread regarding the post

    Returns:
    """
    print(f"{info.chat_id} {info.message_id}")

    published_post = PublishedPost.from_channel(channel_id=info.chat_id, c_message_id=info.message_id)

    message_id = published_post.g_message_id

    info.answer_callback_query(url=f"https://t.me/c/1191261944/{message_id}?thread={message_id}")

    return None, None, STATE['end']

# endregion
