"""Creates the inlinekeyboard sent by the bot in its messages.
Callback_data format: <callback_family>_<callback_name>,[arg]"""
from itertools import islice, zip_longest

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from spotted.data import Config, PendingPost
from spotted.utils.constants import APPROVED_KB, REJECTED_KB


def get_confirm_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to confirm the creation of the post

    Returns:
        new inline keyboard
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="Si", callback_data="post_confirm,submit"),
                InlineKeyboardButton(text="No", callback_data="post_confirm,cancel"),
            ]
        ]
    )


def get_preview_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to choose if the post should be previewed or not

    Returns:
        new inline keyboard
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="Si", callback_data="post_preview,accept"),
                InlineKeyboardButton(text="No", callback_data="post_preview,reject"),
            ]
        ]
    )


def get_settings_kb() -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard to edit the settings

    Returns:
        new inline keyboard
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(" Anonimo ", callback_data="settings,anonimo"),
                InlineKeyboardButton(" Con credit ", callback_data="settings,credit"),
            ]
        ]
    )


def get_approve_kb(pending_post: PendingPost = None, approve: int = -1, reject: int = -1) -> InlineKeyboardMarkup:
    """Generates the InlineKeyboard for the pending post.
    If the pending post is None, the keyboard will be generated with 0 votes.
    Otherwise, the keyboard will be generated with the correct number of votes.
    To avoid unnecessary queries, the number of votes can be passed as an argument
    and will be assumed to be correct.

    Args:
        pending_post: existing pending post to which the keyboard is attached
        approve: number of approve votes known in advance
        reject: number of reject votes known in advance

    Returns:
        new inline keyboard
    """
    if pending_post is None:  # the post has just been created
        n_approve = 0
        n_reject = 0
    else:
        n_approve = pending_post.get_votes(vote=True) if approve < 0 else approve
        n_reject = pending_post.get_votes(vote=False) if reject < 0 else reject
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"🟢 {n_approve}", callback_data="approve_yes"),
                InlineKeyboardButton(f"🔴 {n_reject}", callback_data="approve_no"),
            ],
            [InlineKeyboardButton("⏹ Stop", callback_data="approve_status,pause,0")],
        ]
    )


def get_autoreply_kb(page: int, items_per_page: int) -> list[list[InlineKeyboardButton]]:
    """Generates the keyboard for the autoreplies

    Args:
        page: page of the autoreplies
        items_per_page: number of items per page

    Returns:
        new part of keyboard
    """
    keyboard = []

    autoreplies = islice(Config.autoreplies_get("autoreplies"), page * items_per_page, (page + 1) * items_per_page)

    for row in zip_longest(*[iter(autoreplies)] * 2, fillvalue=None):
        new_row = []
        for autoreply in row:
            if autoreply is not None:
                new_row.append(InlineKeyboardButton(autoreply, callback_data=f"autoreply,{autoreply}"))
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
        navigation_row.append(InlineKeyboardButton("⏮ Previous", callback_data=f"approve_status,pause,{page - 1}"))
    else:
        navigation_row.append(none_button)

    navigation_row.append(InlineKeyboardButton("▶️ Resume", callback_data="approve_status,play"))

    if len(Config.autoreplies_get("autoreplies")) > (page + 1) * items_per_page:
        navigation_row.append(InlineKeyboardButton("⏭ Next", callback_data=f"approve_status,pause,{page + 1}"))
    else:
        navigation_row.append(none_button)

    keyboard.append(navigation_row)

    return InlineKeyboardMarkup(keyboard)


def get_published_post_kb() -> InlineKeyboardMarkup | None:
    """Generates the InlineKeyboard for the published post adding the report button if needed

    Returns:
        new inline keyboard
    """
    keyboard: list[InlineKeyboardButton] = []
    # the last button in the last row will be the report button
    report_button = InlineKeyboardButton("🚩 Report", callback_data="report_spot")
    follow_button = InlineKeyboardButton("👁 Follow", callback_data="follow_spot")
    if Config.post_get("report"):
        if len(keyboard) > 0:
            keyboard[-1].append(report_button)
        else:
            keyboard.append([report_button])

    keyboard.append([follow_button])
    return InlineKeyboardMarkup(keyboard) if keyboard else None


async def get_post_outcome_kb(
    bot: Bot, votes: list[tuple[int, bool]], reason: str | None = None
) -> InlineKeyboardMarkup:
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
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🟢 {(await bot.get_chat(approve)).username}" if approve else "", callback_data="none"
                ),
                InlineKeyboardButton(
                    f"🔴 {(await bot.get_chat(reject)).username}" if reject else "", callback_data="none"
                ),
            ]
        )

    is_approved = len(approved_by) > len(rejected_by) and reason is None
    outcome_text = APPROVED_KB if is_approved else REJECTED_KB

    if reason is not None and not is_approved:
        outcome_text += f" [{reason}]"

    keyboard.append(
        [
            InlineKeyboardButton(outcome_text, callback_data="none"),
        ]
    )
    return InlineKeyboardMarkup(keyboard)
