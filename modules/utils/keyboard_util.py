"""Creates the inlinekeyboard sent by the bot in its messages.
Callback_data format: <callback_family>_<callback_name>,[arg]"""
from itertools import islice, zip_longest
from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot
from modules.data import Config, PublishedPost, PendingPost
from modules.utils.constants import APPROVED_KB, REJECTED_KB

REACTION = Config.reactions_get('reactions')
ROWS = Config.reactions_get('rows')
AUTOREPLIES = Config.autoreplies_get('autoreplies')

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
    ], [InlineKeyboardButton("⏹ Stop", callback_data="meme_approve_status,pause,0")]])

def get_autoreply_kb(page: int, items_per_page: int) -> List[List[InlineKeyboardButton]]:
    """Generates the keyboard for the autoreplies

    Args:
        page: page of the autoreplies
        items_per_page: number of items per page

    Returns:
        new part of keyboard
    """
    keyboard = []

    autoreplies = islice(AUTOREPLIES, page * items_per_page, (page + 1) * items_per_page)

    for row in zip_longest(*[iter(autoreplies)] * 2, fillvalue=None):
        new_row = []
        for autoreply in row:
            if autoreply is not None:
                new_row.append(InlineKeyboardButton(autoreply, callback_data=f"meme_autoreply,{autoreply}"))
        keyboard.append(new_row)

    return keyboard

def get_paused_kb(page: int, items_per_page: int) -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the paused post

    Args:
        page: page of the autoreplies

    Returns:
        autoreplies keyboard append with resume button
    """
    keyboard = get_autoreply_kb(page, items_per_page)

    # navigation buttons
    navigation_row = []
    # to keep the same number of buttons in the row
    none_button = InlineKeyboardButton(" ", callback_data="none")

    if page > 0:
        navigation_row.append(InlineKeyboardButton("⏮ Previous", callback_data=f"meme_approve_status,pause,{page - 1}"))
    else:
        navigation_row.append(none_button)

    navigation_row.append(InlineKeyboardButton("▶️ Resume", callback_data="meme_approve_status,play"))

    if len(AUTOREPLIES) > (page + 1) * items_per_page:
        navigation_row.append(InlineKeyboardButton("⏭ Next", callback_data=f"meme_approve_status,pause,{page + 1}"))
    else:
        navigation_row.append(none_button)

    keyboard.append(navigation_row)

    return InlineKeyboardMarkup(keyboard)

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


def get_post_outcome_kb(bot: Bot, votes: list[tuple[int, bool]], reason: Optional[str] = None) -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the outcome of a post

    Args:
        bot: bot instance
        votes: list of votes
        reason: reason for the rejection, currently used on autoreplies

    Returns:
        new inline keyboard
    """
    keyboard = []

    approved_by = [vote[0] for vote in votes if vote[1]]
    rejected_by = [vote[0] for vote in votes if not vote[1]]

    # keyboard with 2 columns: one for the approve votes and one for the reject votes
    for approve, reject in zip_longest(approved_by, rejected_by, fillvalue=False):
        keyboard.append([
            InlineKeyboardButton(f"🟢 {bot.get_chat(approve).username}" if approve else '', callback_data="none"),
            InlineKeyboardButton(f"🔴 {bot.get_chat(reject).username}" if reject else '', callback_data="none")
        ])

    is_approved = len(approved_by) > len(rejected_by)
    outcome_text = APPROVED_KB if is_approved else REJECTED_KB

    if reason is not None and not is_approved:
        outcome_text += f" [{reason}]"

    keyboard.append([
        InlineKeyboardButton(outcome_text, callback_data="none"),
    ])
    return InlineKeyboardMarkup(keyboard)
