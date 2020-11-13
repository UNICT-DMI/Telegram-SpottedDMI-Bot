"""Creates the inlinekeyboard sent by the bot in its messages"""
from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.data.meme_data import MemeData


def get_confirm_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to confirm the creation of the post

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text="Si", callback_data="meme_confirm_yes"),
        InlineKeyboardButton(text="No", callback_data="meme_confirm_no")
    ]])


def get_stats_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the stats menu

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("~  Lo spot con più ___  ~", callback_data="none")],
        [
            InlineKeyboardButton("voti", callback_data="stats_max,votes"),
            InlineKeyboardButton("👍", callback_data="stats_max,yes"),
            InlineKeyboardButton("👎", callback_data="stats_max,no"),
        ],
        [InlineKeyboardButton("~  Media di ___ per spot  ~", callback_data="none")],
        [
            InlineKeyboardButton("voti", callback_data="stats_avg,votes"),
            InlineKeyboardButton("👍", callback_data="stats_avg,yes"),
            InlineKeyboardButton("👎", callback_data="stats_avg,no"),
        ],
        [InlineKeyboardButton("~  Numero di ___ totale  ~", callback_data="none")],
        [
            InlineKeyboardButton("spot", callback_data="stats_tot,posts"),
            InlineKeyboardButton("voti", callback_data="stats_tot,votes"),
            InlineKeyboardButton("👍", callback_data="stats_tot,yes"),
            InlineKeyboardButton("👎", callback_data="stats_tot,no"),
        ],
        [InlineKeyboardButton("Chiudi", callback_data="stats_close,")],
    ])


def get_approve_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the pending post

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🟢 0", callback_data="meme_approve_yes"),
        InlineKeyboardButton("🔴 0", callback_data="meme_approve_no")
    ]])


def get_vote_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the published post

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("👍 0", callback_data="meme_vote_yes"),
        InlineKeyboardButton("👎 0", callback_data="meme_vote_no")
    ]])


def update_approve_kb(keyboard: List[List[InlineKeyboardButton]],
                      g_message_id: int,
                      group_id: int,
                      approve: int = -1,
                      reject: int = -1) -> InlineKeyboardMarkup:
    """Updates the InlineKeyboard when the valutation of a pending post changes

    Args:
        keyboard (List[List[InlineKeyboardButton]]): previous keyboard
        g_message_id (int): id of the pending post in question ni the admin group
        group_id (int): id of the admin group
        approve (int, optional): number of approve votes, if known. Defaults to -1.
        reject (int, optional): number of reject votes, if known. Defaults to -1.

    Returns:
        InlineKeyboardMarkup: updated inline keyboard
    """
    if approve >= 0:
        keyboard[0][0].text = f"🟢 {approve}"
    else:
        keyboard[0][0].text = f"🟢 {MemeData.get_pending_votes(g_message_id, group_id, vote=True)}"
    if reject >= 0:
        keyboard[0][1].text = f"🔴 {reject}"
    else:
        keyboard[0][1].text = f"🔴 {MemeData.get_pending_votes(g_message_id, group_id, vote=False)}"
    return InlineKeyboardMarkup(keyboard)


def update_vote_kb(keyboard: List[List[InlineKeyboardButton]],
                   c_message_id: int,
                   channel_id: int,
                   upvote: int = -1,
                   downvote: int = -1) -> InlineKeyboardMarkup:
    """Updates the InlineKeyboard when the valutation of a published post changes

    Args:
        keyboard (List[List[InlineKeyboardButton]]): previous keyboard
        c_message_id (int): id of the published post in question
        channel_id (int): id of the channel
        upvote (int, optional): number of upvotes, if known. Defaults to -1.
        downvote (int, optional): number of downvotes, if known. Defaults to -1.

    Returns:
        InlineKeyboardMarkup: updated inline keyboard
    """
    if upvote >= 0:
        keyboard[0][0].text = f"👍 {upvote}"
    else:
        keyboard[0][0].text = f"👍 {MemeData.get_published_votes(c_message_id, channel_id, vote=True)}"
    if downvote >= 0:
        keyboard[0][1].text = f"👎 {downvote}"
    else:
        keyboard[0][1].text = f"👎 {MemeData.get_published_votes(c_message_id, channel_id, vote=False)}"
    return InlineKeyboardMarkup(keyboard)
