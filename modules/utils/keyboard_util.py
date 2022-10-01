"""Creates the inlinekeyboard sent by the bot in its messages.
Callback_data format: <callback_family>_<callback_name>,[arg]"""
from typing import Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.data import PendingPost, PublishedPost, Config

REACTION = Config.reactions_get('reactions')
ROWS = Config.reactions_get('rows')


def get_confirm_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to confirm the creation of the post

    Returns:
        new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text="Si", callback_data="meme_confirm,submit"),
        InlineKeyboardButton(text="No", callback_data="meme_confirm,cancel")
    ]])

def get_preview_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to choose if the post should be previewed or not

    Returns:
        new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text="Si", callback_data="meme_preview,accept"),
        InlineKeyboardButton(text="No", callback_data="meme_preview,reject")
    ]])


def get_settings_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to edit the settings

    Returns:
        new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(" Anonimo ", callback_data="meme_settings,anonimo"),
        InlineKeyboardButton(" Con credit ", callback_data="meme_settings,credit"),
    ]])


def get_stats_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the stats menu

    Returns:
        new inline keyboard
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
        new inline keyboard
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🟢 0", callback_data="meme_approve_yes,"),
        InlineKeyboardButton("🔴 0", callback_data="meme_approve_no,")
    ], [InlineKeyboardButton("⏹ Stop", callback_data="meme_approve_status,pause")]])


def get_vote_kb(published_post: Optional[PublishedPost] = None) -> Optional[InlineKeyboardMarkup]:
    """Generates the InlineKeyboard for the published post and updates the correct number of reactions

    Args:
        published_post: published post to which the keyboard is attached

    Returns:
        new inline keyboard
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
    report_button = InlineKeyboardButton("🚩 Report", callback_data="meme_report_spot")
    if Config.meme_get('report'):
        if len(keyboard) > 0:
            keyboard[-1].append(report_button)
        else:
            keyboard.append([report_button])

    return InlineKeyboardMarkup(keyboard) if keyboard else None


def update_approve_kb(keyboard: list[list[InlineKeyboardButton]],
                      pending_post: PendingPost,
                      approve: int = -1,
                      reject: int = -1) -> InlineKeyboardMarkup:
    """Updates the InlineKeyboard when the valuation of a pending post changes

    Args:
        keyboard: previous keyboard
        pending_post: pending post to which the keyboard is attached
        approve: number of approve votes, if known
        reject: number of reject votes, if known

    Returns:
        updated inline keyboard
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
