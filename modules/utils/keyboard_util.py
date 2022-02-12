"""Creates the inlinekeyboard sent by the bot in its messages.
Callback_data format: <callback_family>_<callback_name>,[arg]"""
from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.data import PendingPost, PublishedPost, config_reactions, config_map

REACTION = config_reactions['reactions']
ROWS = config_reactions['rows']


def get_confirm_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to confirm the creation of the post

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text="Si", callback_data="meme_confirm,submit"),
        InlineKeyboardButton(text="No", callback_data="meme_confirm,cancel")
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
    keyboard = [
        [InlineKeyboardButton("~  Lo spot con più ___  ~", callback_data="none")],
        [
            InlineKeyboardButton("voti", callback_data="stats_max,votes"),
        ],
        *[[InlineKeyboardButton(REACTION[reaction_id], callback_data=f"stats_max,{reaction_id}")
           for reaction_id in row]
          for row in ROWS],
        [InlineKeyboardButton("~  Media di ___ per spot  ~", callback_data="none")],
        [
            InlineKeyboardButton("voti", callback_data="stats_avg,votes"),
        ],
        *[[InlineKeyboardButton(REACTION[reaction_id], callback_data=f"stats_avg,{reaction_id}")
           for reaction_id in row]
          for row in ROWS],
        [InlineKeyboardButton("~  Numero di ___ totale  ~", callback_data="none")],
        [
            InlineKeyboardButton("spot", callback_data="stats_tot,posts"),
            InlineKeyboardButton("voti", callback_data="stats_tot,votes"),
        ],
        *[[InlineKeyboardButton(REACTION[reaction_id], callback_data=f"stats_tot,{reaction_id}")
           for reaction_id in row]
          for row in ROWS],
        [InlineKeyboardButton("Chiudi", callback_data="stats_close,")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_approve_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the pending post

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🟢 0", callback_data="meme_approve_yes,"),
        InlineKeyboardButton("🔴 0", callback_data="meme_approve_no,")
    ], [InlineKeyboardButton("⏹ Stop", callback_data="meme_approve_status,pause")]])


def get_vote_kb(published_post: PublishedPost = None) -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the published post and updates the correct number of reactions

    Args:
        published_post (PublishedPost, optional): published post to which the keyboard is attached. Defaults to None

    Returns:
        InlineKeyboardMarkup: new inline keyboard
    """
    keyboard = []
    for row in ROWS:  # for each ROW or the keyboard...
        new_row = []
        for reaction_id in row:  # ... add all the reactions for that row
            n_votes = "0" if published_post is None else published_post.get_votes(vote=reaction_id)
            new_row.append(InlineKeyboardButton(f"{REACTION[reaction_id]} {n_votes}",
                                                callback_data=f"meme_vote,{reaction_id}"))
        keyboard.append(new_row)
    # the last button in the last row will be the report button
    if config_map['meme']['report']:
        if len(keyboard) > 0:
            keyboard[-1].append(InlineKeyboardButton("🚩 Report", callback_data="meme_report_spot,"))
        else:
            keyboard.append([InlineKeyboardButton("🚩 Report", callback_data="meme_report_spot,")])
    return InlineKeyboardMarkup(keyboard)


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
