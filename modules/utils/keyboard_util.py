"""Creates the inlinekeyboard sent by the bot in its messages.
Callback_data format: <callback_family>_<callback_name>,[arg]"""
from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.data import PendingPost, PublishedPost
from modules.utils import REACTION


def get_confirm_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to confirm the creation of the post

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text="Si", callback_data="meme_confirm,yes"),
        InlineKeyboardButton(text="No", callback_data="meme_confirm,no")
    ]])


def get_settings_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to edit the settings

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(" Anonimo ", callback_data="meme_settings,anonimo"),
        InlineKeyboardButton(" Con credit ", callback_data="meme_settings,credit"),
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
            InlineKeyboardButton("👍", callback_data="stats_max,1"),
            InlineKeyboardButton("👎", callback_data="stats_max,0"),
        ],
        [InlineKeyboardButton("~  Media di ___ per spot  ~", callback_data="none")],
        [
            InlineKeyboardButton("voti", callback_data="stats_avg,votes"),
            InlineKeyboardButton("👍", callback_data="stats_avg,1"),
            InlineKeyboardButton("👎", callback_data="stats_avg,0"),
        ],
        [InlineKeyboardButton("~  Numero di ___ totale  ~", callback_data="none")],
        [
            InlineKeyboardButton("spot", callback_data="stats_tot,posts"),
            InlineKeyboardButton("voti", callback_data="stats_tot,votes"),
            InlineKeyboardButton("👍", callback_data="stats_tot,1"),
            InlineKeyboardButton("👎", callback_data="stats_tot,0"),
        ],
        [InlineKeyboardButton("Chiudi", callback_data="stats_close,")],
    ])


def get_approve_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the pending post

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🟢 0", callback_data="meme_approve_yes,"),
        InlineKeyboardButton("🔴 0", callback_data="meme_approve_no,")
    ]])


def get_vote_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the published post

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{REACTION['1']} 0", callback_data="meme_vote,1"),
        InlineKeyboardButton(f"{REACTION['0']} 0", callback_data="meme_vote,0")
    ],
                                 [
                                     InlineKeyboardButton(f"{REACTION['2']} 0", callback_data="meme_vote,2"),
                                     InlineKeyboardButton(f"{REACTION['3']} 0", callback_data="meme_vote,3"),
                                     InlineKeyboardButton(f"{REACTION['4']} 0", callback_data="meme_vote,4"),
                                     InlineKeyboardButton("🚩 Report", callback_data="meme_report_spot")
                                 ]])


def update_approve_kb(keyboard: List[List[InlineKeyboardButton]],
                      pending_post: PendingPost,
                      approve: int = -1,
                      reject: int = -1) -> InlineKeyboardMarkup:
    """Updates the InlineKeyboard when the valutation of a pending post changes

    Args:
        keyboard (List[List[InlineKeyboardButton]]): previous keyboard
        pending_post (PendingPost): pending post to which the keyboard is attached
        approve (int, optional): number of approve votes, if known. Defaults to -1.
        reject (int, optional): number of reject votes, if known. Defaults to -1.

    Returns:
        InlineKeyboardMarkup: updated inline keyboard
    """
    if approve >= 0:
        keyboard[0][0].text = f"🟢 {approve}"
    else:
        keyboard[0][0].text = f"🟢 {pending_post.get_votes(vote=True)}"
    if reject >= 0:
        keyboard[0][1].text = f"🔴 {reject}"
    else:
        keyboard[0][1].text = f"🔴 {pending_post.get_votes(vote=False)}"
    return InlineKeyboardMarkup(keyboard)


def update_vote_kb(keyboard: List[List[InlineKeyboardButton]], published_post: PublishedPost) -> InlineKeyboardMarkup:
    """Updates the InlineKeyboard when the valutation of a published post changes

    Args:
        keyboard (List[List[InlineKeyboardButton]]): previous keyboard
        published_post (PublishedPost): published post to which the keyboard is attached

    Returns:
        InlineKeyboardMarkup: updated inline keyboard
    """
    keyboard[0][0].text = f"{REACTION['1']} {published_post.get_votes(vote='1')}"
    keyboard[0][1].text = f"{REACTION['0']} {published_post.get_votes(vote='0')}"
    if len(keyboard) > 1:  # to keep support for older published memes
        keyboard[1][0].text = f"{REACTION['2']} {published_post.get_votes(vote='2')}"
        keyboard[1][1].text = f"{REACTION['3']} {published_post.get_votes(vote='3')}"
        keyboard[1][2].text = f"{REACTION['4']} {published_post.get_votes(vote='4')}"
    return InlineKeyboardMarkup(keyboard)
