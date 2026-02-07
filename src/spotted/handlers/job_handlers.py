"""Scheduled jobs of the bot"""

import io
from binascii import Error as BinasciiError
from datetime import datetime, timedelta, timezone

import pyzipper
from cryptography.fernet import Fernet
from telegram.error import BadRequest, Forbidden
from telegram.ext import CallbackContext

from spotted.data import Config, PendingPost
from spotted.debug import logger
from spotted.utils import EventInfo


async def clean_pending(bot, admin_group_id: int, pending_posts: list, user_text: str) -> int:
    """Cleans up the given pending posts: deletes admin messages, notifies users, removes from store.

    Args:
        bot: the Telegram bot instance
        admin_group_id: id of the admin group
        pending_posts: list of PendingPost to clean up
        user_text: message to send to each poster

    Returns:
        number of admin messages successfully deleted
    """
    removed = 0
    for pending_post in pending_posts:
        try:
            await bot.delete_message(chat_id=admin_group_id, message_id=pending_post.g_message_id)
            removed += 1
        except BadRequest as ex:
            logger.error("Deleting old pending message: %s", ex)
        try:
            await bot.send_message(chat_id=pending_post.user_id, text=user_text)
        except (BadRequest, Forbidden) as ex:
            logger.warning("Notifying user on clean_pending: %s", ex)
        pending_post.delete_post()
    return removed


async def clean_pending_job(context: CallbackContext):
    """Job called each day at 05:00 utc.
    Automatically rejects all pending posts that are older than the chosen amount of hours

    Args:
        context: context passed by the jobqueue
    """
    info = EventInfo.from_job(context)
    admin_group_id = Config.post_get("admin_group_id")

    before_time = datetime.now(tz=timezone.utc) - timedelta(hours=Config.post_get("remove_after_h"))
    pending_posts = PendingPost.get_all(admin_group_id=admin_group_id, before=before_time)

    removed = await clean_pending(
        info.bot,
        admin_group_id,
        pending_posts,
        "Gli admin erano sicuramente molto impegnati e non sono riusciti a valutare lo spot in tempo",
    )

    await info.bot.send_message(
        chat_id=admin_group_id, text=f"Sono stati eliminati {removed} messaggi rimasti in sospeso"
    )


def get_zip_backup() -> bytes:
    """Zip the database file and return the bytes of the zip file,
    optionally encrypting it with a password if `crypto_key` is set in the settings.
    It is called if `zip_backup` is set to `True` in the settings.

    Returns:
        bytes of the (possibly encrypted) zip file
    """
    db_path = Config.debug_get("db_file")
    zip_stream = io.BytesIO()
    with pyzipper.AESZipFile(
        zip_stream,
        "w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES if Config.debug_get("crypto_key") else None,
    ) as zf:
        if Config.debug_get("crypto_key"):
            zf.setpassword(Config.debug_get("crypto_key").encode("utf-8"))
        zf.write(db_path, arcname="spotted.sqlite3")
    zip_stream.seek(0)
    return zip_stream.read()


def get_backup() -> bytes:
    """Get the database backup, either encrypted or not.
    When the `crypto_key` setting is set, the backup is encrypted with Fernet,
    otherwise it's returned as is, in plaintext.

    Returns:
        bytes of the backup file, either encrypted or not
    """
    path = Config.debug_get("db_file")
    with open(path, "rb") as database_file:
        if Config.debug_get("crypto_key"):
            cipher = Fernet(Config.debug_get("crypto_key"))
            return cipher.encrypt(database_file.read())
        return database_file.read()


async def db_backup_job(context: CallbackContext):
    """Job called each day at 05:00 utc.
    Automatically upload and send last version of db for backup

    Args:
        context: context passed by the jobqueue
    """
    admin_group_id = Config.post_get("admin_group_id")
    try:
        db_backup = get_zip_backup() if Config.debug_get("zip_backup") else get_backup()

        await context.bot.send_document(
            chat_id=admin_group_id,
            document=db_backup,
            filename="spotted.backup.zip" if Config.debug_get("zip_backup") else "spotted.backup.sqlite3",
            caption="✅ Backup effettuato con successo",
        )
    except BinasciiError as ex:
        await context.bot.send_message(chat_id=admin_group_id, text=f"✖️ Impossibile effettuare il backup\n\n{ex}")
