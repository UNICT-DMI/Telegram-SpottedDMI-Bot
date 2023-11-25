"""Approve actions the admin can take on a pending post."""
import logging

from telegram import Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import CallbackContext

from spotted.data import Config, PendingPost
from spotted.utils import EventInfo
from spotted.utils.keyboard_util import get_approve_kb, get_paused_kb

logger = logging.getLogger(__name__)


async def approve_status_callback(update: Update, context: CallbackContext):
    """Handles the approve_status callback.
    Pauses or resume voting on a specific pending post

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        text and replyMarkup that make up the reply, new conversation state
    """
    info = EventInfo.from_callback(update, context)
    action = info.args[0]
    pause_page = int(info.args[1]) if len(info.args) > 1 else 0
    items_per_page = Config.settings_get("post", "autoreplies_per_page")

    new_keyboard = None
    if action == "pause":  # if the the admin wants to pause approval of the post
        await info.answer_callback_query("In pausa")
        new_keyboard = get_paused_kb(pause_page, items_per_page)
    elif action == "play":  # if the the admin wants to resume approval of the post
        pending_post = PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=info.message_id)
        if pending_post:
            await info.answer_callback_query("Ripreso")
            new_keyboard = get_approve_kb(pending_post=pending_post)

    if new_keyboard is None:
        logger.error("approve_status_callback: invalid arg '%s','%d'", action, pause_page)
        return
    await info.edit_inline_keyboard(new_keyboard=new_keyboard)


async def reject_post(info: EventInfo, pending_post: PendingPost, reason: str | None = None):
    """Rejects a pending post

    Args:
        info: information about the callback
        pending_post: pending post to reject
        reason: reason for the rejection, currently used on autoreply
    """
    user_id = pending_post.user_id
    pending_post.set_admin_vote(info.user_id, False)

    try:
        await info.bot.send_message(
            chat_id=user_id, text="Il tuo ultimo post è stato rifiutato\nPuoi controllare le regole con /rules"
        )  # notify the user
    except (BadRequest, Forbidden) as ex:
        logger.warning("Notifying the user on approve_no: %s", ex)

    # Shows the list of admins who refused the pending post and removes it form the db
    await info.show_admins_votes(pending_post, reason)
    pending_post.delete_post()


async def approve_yes_callback(update: Update, context: CallbackContext):
    """Handles the approve_yes callback.
    Add a positive vote to the post, updating the keyboard if necessary.
    If the number of positive votes is greater than the number of votes required, the post is approved,
    deleting it from the pending_post table and copying it to the channel

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_callback(update, context)
    pending_post = PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=info.message_id)
    if pending_post is None:  # this pending post is not present in the database
        return

    await info.answer_callback_query()  # end the spinning progress bar
    n_approve = pending_post.set_admin_vote(info.user_id, True)

    # The post passed the approval phase and is to be published
    if n_approve >= Config.post_get("n_votes"):
        user_id = pending_post.user_id
        await info.send_post_to_channel(user_id=user_id)

        try:
            await info.bot.send_message(
                chat_id=user_id, text=f"Il tuo ultimo post è stato pubblicato su {Config.post_get('channel_tag')}"
            )  # notify the user
        except (BadRequest, Forbidden) as ex:
            logger.warning("Notifying the user on approve_yes: %s", ex)

        # Shows the list of admins who approved the pending post and removes it form the db
        await info.show_admins_votes(pending_post)
        pending_post.delete_post()
        return

    if n_approve != -1:  # the vote changed
        new_keyboard = get_approve_kb(pending_post=pending_post, approve=n_approve)
        await info.edit_inline_keyboard(new_keyboard=new_keyboard)


async def approve_no_callback(update: Update, context: CallbackContext):
    """Handles the approve_no callback.
    Add a negative vote to the post, updating the keyboard if necessary.
    If the number of negative votes is greater than the number of votes required, the post is rejected,
    deleting it from the pending_post table and notifying the user

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_callback(update, context)
    pending_post = PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=info.message_id)
    if pending_post is None:  # this pending post is not present in the database
        return

    await info.answer_callback_query()  # end the spinning progress bar
    n_reject = pending_post.set_admin_vote(info.user_id, False)

    # The post has been refused
    if n_reject >= Config.post_get("n_votes"):
        await reject_post(info=info, pending_post=pending_post)
        return

    if n_reject != -1:  # the number of votes changed
        new_keyboard = get_approve_kb(pending_post=pending_post, reject=n_reject)
        await info.edit_inline_keyboard(new_keyboard=new_keyboard)
