"""/stats command"""
import logging
from telegram import Update
from telegram.ext import CallbackContext
from modules.utils import EventInfo, get_stats_kb
from modules.data import PostData, Config

REACTION = Config.reactions_get('reactions')
logger = logging.getLogger(__name__)


def stats_cmd(update: Update, context: CallbackContext):
    """Handles the /stats command.
    Lets the user choose what stats they want to see

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    info.bot.send_message(chat_id=info.chat_id, text="Che statistica ti interessa?", reply_markup=get_stats_kb())


def stats_callback(update: Update, context: CallbackContext):
    """Passes the stats callback to the correct handler

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_callback(update, context)
    info.answer_callback_query()  # end the spinning progress bar
    # the callback data indicates the correct callback and the arg to pass to it separated by ,
    data = info.query_data.split(",")
    try:
        message_text = globals()[f'{data[0][6:]}_callback'](data[1])  # call the function based on its name
    except KeyError as ex:
        logger.error("stats_callback: %s", ex)
        return

    # if there is a valid text, edit the menu with the new text
    if message_text:
        if message_text != info.text:
            info.bot.edit_message_text(chat_id=info.chat_id,
                                       message_id=info.message_id,
                                       text=message_text,
                                       reply_markup=get_stats_kb())
    else:  # remove the reply markup
        info.edit_inline_keyboard()


# region handle stats_callback
def avg_callback(arg: str) -> str:
    """Handles the avg_[ votes | 0 | 1 ] callback.
    Shows the average of the %arg per post

    Args:
        arg: [ votes | 0 | 1 ]

    Returns:
        text for the reply
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
        arg: [ votes | 0 | 1 ]

    Returns:
        text for the reply
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
        arg: [ posts | votes | 0 | 1 ]

    Returns:
        text for the reply
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


def close_callback(_: None) -> None:
    """Handles the close callback
    Closes the stats menu

    Returns:
        text and replyMarkup that make up the reply
    """
    return None
# endregion
