"""Modules used in this bot"""

import signal

from telegram.error import TelegramError
from telegram.ext import Application, CallbackContext

from spotted.data import Config, PendingPost, init_db
from spotted.debug import logger
from spotted.handlers import add_commands, add_handlers, add_jobs
from spotted.handlers.job_handlers import clean_pending


async def _drain_notify(context: CallbackContext):
    """Notifies admins that the bot is shutting down and starts the drain check loop"""
    admin_group_id = Config.post_get("admin_group_id")
    n_pending = len(PendingPost.get_all(admin_group_id=admin_group_id))

    if n_pending == 0:
        logger.info("No pending posts, shutting down immediately")
        context.application.stop_running()
        return

    timeout = Config.debug_get("drain_timeout")
    await context.bot.send_message(
        chat_id=admin_group_id,
        text=(
            f"Il bot si sta spegnendo. Ci sono {n_pending} spot in sospeso.\n"
            f"Approvateli o rifiutateli entro {timeout // 60} minuti."
        ),
    )

    context.application.job_queue.run_repeating(
        _drain_check, interval=5, first=5, data={"timeout": timeout, "elapsed": 0}
    )


async def _drain_check(context: CallbackContext):
    """Checks if drain is complete (no pending posts or timeout reached)"""
    admin_group_id = Config.post_get("admin_group_id")
    n_pending = len(PendingPost.get_all(admin_group_id=admin_group_id))
    data = context.job.data
    data["elapsed"] += 5

    if n_pending == 0:
        logger.info("Drain complete: no pending posts remaining")
        context.job.schedule_removal()
        context.application.stop_running()
    elif data["elapsed"] >= data["timeout"]:
        logger.warning("Drain timeout reached with %d pending posts", n_pending)
        pending_posts = PendingPost.get_all(admin_group_id=admin_group_id)
        await clean_pending(
            context.bot,
            admin_group_id,
            pending_posts,
            "Il bot è stato riavviato e il tuo spot in sospeso è andato perso.\n"
            "Per favore, invia nuovamente il tuo spot con /spot",
        )
        await context.bot.send_message(
            chat_id=admin_group_id,
            text=f"Timeout raggiunto. {n_pending} spot in sospeso sono stati eliminati. Il bot si spegne.",
        )
        context.job.schedule_removal()
        context.application.stop_running()


async def _post_stop(application: Application):
    """Called after the application stops. Sends a final message to admins."""
    try:
        admin_group_id = Config.post_get("admin_group_id")
        await application.bot.send_message(chat_id=admin_group_id, text="Bot spento.")
    except TelegramError:
        logger.error("Failed to send shutdown message to admin group")


def run_bot():
    """Init the database, add the handlers and start the bot"""

    init_db()
    application = (
        Application.builder().token(Config.settings_get("token")).post_init(add_commands).post_stop(_post_stop).build()
    )
    add_handlers(application)
    add_jobs(application)

    def _handle_signal(sig, _frame):
        """Custom signal handler that starts the drain process instead of immediately stopping"""
        if PendingPost.is_draining():
            logger.info("Received signal %s while already draining, ignoring", signal.Signals(sig).name)
            return
        logger.info("Received signal %s, starting graceful drain", signal.Signals(sig).name)
        PendingPost.start_drain()
        application.job_queue.run_once(_drain_notify, when=0)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    application.run_polling(stop_signals=())
