"""Handles the execution of commands by the bot"""
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from modules.handlers import STATE, CHAT_PRIVATE_ERROR, INVALID_MESSAGE_TYPE_ERROR
from modules.handlers.job_handlers import clean_pending_job
from modules.data import config_map, read_md, PendingPost, Report, User
from modules.utils import EventInfo
from modules.utils.keyboard_util import get_confirm_kb, get_settings_kb, get_stats_kb


# region cmd
def start_cmd(update: Update, context: CallbackContext):
    """Handles the /start command.
    Sends a welcoming message

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    text = read_md("start")
    info.bot.send_message(chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)


def help_cmd(update: Update, context: CallbackContext):
    """Handles the /help command.
    Sends an help message

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id']:  # if you are in the admin group
        text = read_md("instructions")
    else:  # you are NOT in the admin group
        text = read_md("help")
    info.bot.send_message(chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)


def rules_cmd(update: Update, context: CallbackContext):
    """Handles the /rules command.
    Sends a message containing the rules

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    text = read_md("rules")
    info.bot.send_message(chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)


def settings_cmd(update: Update, context: CallbackContext):
    """Handles the /settings command.
    Let's the user choose whether his posts will be credited or not

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if not info.is_private_chat:  # you can only post with a private message
        info.bot.send_message(chat_id=info.chat_id, text=CHAT_PRIVATE_ERROR)
        return None

    info.bot.send_message(chat_id=info.chat_id,
                          text="***Come vuoi che sia il tuo post:***",
                          reply_markup=get_settings_kb(),
                          parse_mode=ParseMode.MARKDOWN_V2)


def post_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the /post command.
    Checks that the user is in a private chat and it's not banned and start the post conversation

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    user = User(info.user_id)
    if not info.is_private_chat:  # you can only post from a private chat
        info.bot.send_message(chat_id=info.chat_id, text=CHAT_PRIVATE_ERROR)
        return STATE['end']

    if user.is_banned:  # the user is banned
        info.bot.send_message(chat_id=info.chat_id, text="Sei stato bannato 😅")
        return STATE['end']

    if user.is_pending:  # there is already a post in pending
        info.bot.send_message(chat_id=info.chat_id, text="Hai già un post in approvazione 🧐")
        return STATE['end']

    info.bot.send_message(chat_id=info.chat_id, text="Invia il post che vuoi pubblicare")
    return STATE['posting']


def ban_cmd(update: Update, context: CallbackContext):
    """Handles the /ban command.
    Ban a user by replying to one of his pending posts with /ban

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id']:  # you have to be in the admin group
        g_message_id = update.message.reply_to_message.message_id
        pending_post = PendingPost.from_group(group_id=info.chat_id, g_message_id=g_message_id)

        if pending_post is None:
            info.bot.send_message(chat_id=info.chat_id, text="Per bannare qualcuno, rispondi al suo post con /ban")
            return

        user = User(pending_post.user_id)
        user.ban()
        pending_post.delete_post()
        info.bot.edit_message_reply_markup(chat_id=info.chat_id, message_id=g_message_id)
        info.bot.send_message(chat_id=info.chat_id, text="L'utente è stato bannato")


def sban_cmd(update: Update, context: CallbackContext):
    """Handles the /sban command.
    Sban a user by using this command and listing all the user_id to sban

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id']:  # you have to be in the admin group
        if len(context.args) == 0:  # if no args have been passed
            info.bot.send_message(chat_id=info.chat_id, text="[uso]: /sban <user_id1> [...user_id2]")
            return
        for user_id in context.args:
            # the sban was unsuccesful (maybe the user id was not found)
            if not User(user_id).sban():
                break
        else:
            info.bot.send_message(chat_id=info.chat_id, text="Sban effettuato")
            return
        info.bot.send_message(chat_id=info.chat_id, text="Uno o più sban sono falliti")


def reply_cmd(update: Update, context: CallbackContext):
    """Handles the /reply command.
    Send a message to a user by replying to one of his pending posts with /reply + the message you want to send

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id']:  # you have to be in the admin group

        if len(info.text) <= 7:  # the reply is empty
            info.bot.send_message(
                chat_id=info.chat_id,
                text="La reply è vuota\n"\
                "Per mandare un messaggio ad un utente, rispondere al suo post o report con /reply "\
                "seguito da ciò che gli si vuole dire"
            )
            return None

        g_message_id = update.message.reply_to_message.message_id

        pending_post = PendingPost.from_group(group_id=info.chat_id, g_message_id=g_message_id)
        if pending_post is not None:  # the message was a pending post
            info.bot.send_message(chat_id=pending_post.user_id,
                                  text="COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n" + info.text[7:].strip())
            info.bot.send_message(chat_id=info.chat_id,
                                    text="L'utente ha ricevuto il seguente messaggio:\n"\
                                        "COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n" + info.text[7:].strip(),
                                    reply_to_message_id=g_message_id)
            return None
        report = Report.from_group(group_id=info.chat_id, g_message_id=g_message_id)
        if report is not None:  # the message was a report
            info.bot.send_message(chat_id=report.user_id,
                                  text="COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n" + info.text[7:].strip())
            info.bot.send_message(chat_id=info.chat_id,
                                    text="L'utente ha ricevuto il seguente messaggio:\n"\
                                        "COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n" + info.text[7:].strip(),
                                    reply_to_message_id=g_message_id)
            return None

        info.bot.send_message(
                chat_id=info.chat_id,
                text="Il messaggio selezionato non è valido.\n"\
                "Per mandare un messaggio ad un utente, rispondere al suo post o report con /reply "\
                "seguito da ciò che gli si vuole dire"
            )


def clean_pending_cmd(update: Update, context: CallbackContext):
    """Handles the /clean_pending command.
    Automatically rejects all pending posts that are older than the chosen amount of hours

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id']:  # you have to be in the admin group
        clean_pending_job(context=context)


def cancel_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the /cancel command.
    Exits from the post pipeline and removes the eventual pending post of the user

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_private_chat:  # you can only cancel a post with a private message
        return STATE['end']
    pending_post = PendingPost.from_user(user_id=info.user_id)
    if pending_post:  # if the user has a pending post in evaluation, delete it
        group_id = pending_post.group_id
        g_message_id = pending_post.g_message_id
        pending_post.delete_post()

        info.bot.delete_message(chat_id=group_id, message_id=g_message_id)
        info.bot.send_message(chat_id=info.chat_id, text="Lo spot precedentemente inviato è stato cancellato")
    else:
        info.bot.send_message(chat_id=info.chat_id, text="Operazione annullata")
    return STATE['end']


def stats_cmd(update: Update, context: CallbackContext):
    """Handles the /stats command.
    Lets the user choose what stats they want to see

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    info.bot.send_message(chat_id=info.chat_id, text="Che statistica ti interessa?", reply_markup=get_stats_kb())


# endregion

# region msg


def post_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /post command.
    Checks the message the user wants to post, and goes to the final step

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)

    if not info.is_valid_message_type:  # the type is NOT supported
        info.bot.send_message(
            chat_id=info.chat_id,
            text=
            "Questo tipo di messaggio non è supportato\nÈ consentito solo testo, stikers, immagini, audio, video o poll\n"\
            "Invia il post che vuoi pubblicare\nPuoi annullare il processo con /cancel")
        return STATE['posting']

    info.bot.send_message(chat_id=info.chat_id,
                          text="Sei sicuro di voler publicare questo post?",
                          reply_to_message_id=info.message_id,
                          reply_markup=get_confirm_kb())
    return STATE['confirm']


def forwarded_post_msg(update: Update, context: CallbackContext):
    """Handles the post forwarded in the channel group.
    Sends a reply in the channel group and stores it in the database, so that the post can be voted

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if update.message.forward_from_chat is None:
        return

    if info.chat_id == config_map['meme']['channel_group_id']\
        and info.forward_from_chat_id == config_map['meme']['channel_id']\
        and info.user_name == "Telegram":
        info.send_post_to_channel_group()


# endregion

# region report spot


def report_post(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the key "Report".
    Checks the message the user wants to report, and goes to the final step

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)

    if not info.is_private_chat:
        return STATE['reporting_spot']

    if not info.is_valid_message_type:  # the type is NOT supported
        info.bot.send_message(chat_id=info.chat_id, text=INVALID_MESSAGE_TYPE_ERROR)
        return STATE['reporting_spot']

    chat_id = config_map['meme']['group_id']  # should be admin group

    channel_id, target_message_id = context.user_data['current_post_reported'].split(",")

    info.bot.forward_message(chat_id=chat_id, from_chat_id=channel_id, message_id=target_message_id)
    admin_message = info.bot.sendMessage(chat_id=chat_id, text="🚨🚨 SEGNALAZIONE 🚨🚨\n\n" + info.text)
    info.bot.send_message(chat_id=info.chat_id,
                          text="Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!")

    Report.create_post_report(user_id=info.user_id,
                              channel_id=channel_id,
                              c_message_id=target_message_id,
                              admin_message=admin_message)

    return STATE['end']


# endregion

# region report user


def report_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the key "Report".
    Checks the message the user wants to report

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_private_chat:  # you can only post with a private message
        info.bot.send_message(chat_id=info.chat_id, text=CHAT_PRIVATE_ERROR)
        return STATE['end']

    user_report = Report.get_last_user_report(user_id=info.user_id)

    if user_report is not None:
        minutes_enlapsed = user_report.minutes_passed
        remain_minutes = int(config_map['meme']['report_wait_mins'] - minutes_enlapsed)

        if remain_minutes > 0:
            info.bot.send_message(chat_id=info.chat_id, text=f"Aspetta {remain_minutes} minuti.")
            return STATE['end']

    info.bot.send_message(chat_id=info.chat_id, text="Invia l'username di chi vuoi segnalare. Es. @massimobene")

    return STATE['reporting_user']


def report_user_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /report command after sent the @username.
    Checks the the user wants to report, and goes to ask the reason

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_valid_message_type \
    or not info.text.startswith('@') \
    or info.text.find(' ') != -1:  # the type is NOT supported
        info.bot.send_message(
            chat_id=info.chat_id,
            text="Questo tipo di messaggio non è supportato\n"\
                "È consentito solo username telegram. Puoi annullare il processo con /cancel")
        return STATE['reporting_user']

    context.user_data['current_report_target'] = info.text

    info.bot.send_message(
        chat_id=info.chat_id,
        text="Scrivi il motivo della tua segnalazione.\n"\
            "Cerca di essere esaustivo, potrai inviare un altro report "\
            f"dopo {config_map['meme']['report_wait_mins']} minuti.\n"\
            "Puoi annullare il processo con /cancel")

    return STATE['sending_user_report']


def report_user_sent_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /report command after sent the reason.
    Checks the the user wants to report, and goes to final step

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_valid_message_type:  # the type is NOT supported
        info.bot.send_message(chat_id=info.chat_id, text=INVALID_MESSAGE_TYPE_ERROR)
        return STATE['sending_user_report']

    target_username = context.user_data['current_report_target']

    chat_id = config_map['meme']['group_id']  # should be admin group
    admin_message = info.bot.sendMessage(chat_id=chat_id,
                                         text="🚨🚨 SEGNALAZIONE 🚨🚨\n\n" + "Username: " + target_username + "\n\n" + info.text)

    info.bot.send_message(chat_id=info.chat_id,
                          text="Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!")

    Report.create_user_report(user_id=info.user_id, target_username=target_username, admin_message=admin_message)

    return STATE['end']


# endregion
