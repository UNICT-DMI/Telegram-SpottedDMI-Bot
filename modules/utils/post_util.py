"""Modules that handles how the post shall be sent according to the chat (adming group or channel)"""
from random import choice
from telegram import Message, Bot, InlineKeyboardMarkup
from modules.data.data_reader import config_map
from modules.data.meme_data import MemeData
from modules.utils.keyboard_util import get_approve_kb, get_vote_kb


def send_post_to(message: Message, bot: Bot, destination: str, user_id: int = None) -> Message:
    """Sends the post to the specified destination:

    admin -> to the admin group, so it can be approved

    channel -> to the channel, so it can be ejoyed by the users (and voted, if comments are disabled)

    channel_group -> to the group associated to the channel, so that users can vote the post (if comments are enabled)

    Args:
        message (Message): message that contains the post to send
        bot (Bot): bot
        destination (str): destination of the message (admin | channel | channel_group)
        user_id (int, optional): id of the user that originated the post. Defaults to None.
    Returns:
        Message: message used to send a post to a specific destination
    """
    text = message.text
    photo = message.photo
    voice = message.voice
    audio = message.audio
    video = message.video
    animation = message.animation
    sticker = message.sticker
    caption = message.caption

    reply_markup = None
    post_message = None

    if destination == "admin":  # send the post to the admin group so it can be approved
        chat_id = config_map['meme']['group_id']
        reply_markup = get_approve_kb()
    elif destination == "channel":  # send the post to the channel...
        chat_id = config_map['meme']['channel_id']
        if not config_map['meme']['comments']:  # ... append the voting Inline Keyboard, if comments are not to be supported
            reply_markup = get_vote_kb()
    elif destination == "channel_group":  # sends a support message with the voting Inline Keyboard in the comment session
        post_message = send_helper_message(user_id=user_id,
                                           chat_id=config_map['meme']['channel_group_id'],
                                           reply_message_id=message.message_id,
                                           bot=bot,
                                           reply_markup=get_vote_kb())
    else:
        print("[error] send_message_to: unvalid destination")
        return None

    if post_message is None:
        if text:
            post_message = bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)
        elif photo:
            post_message = bot.sendPhoto(chat_id=chat_id, photo=photo[-1], caption=caption, reply_markup=reply_markup)
        elif voice:
            post_message = bot.sendVoice(chat_id=chat_id, voice=voice, reply_markup=reply_markup)
        elif audio:
            post_message = bot.sendAudio(chat_id=chat_id, audio=audio, reply_markup=reply_markup)
        elif video:
            post_message = bot.sendVideo(chat_id=chat_id, video=video, caption=caption, reply_markup=reply_markup)
        elif animation:
            post_message = bot.sendAnimation(chat_id=chat_id, animation=animation, reply_markup=reply_markup)
        elif sticker:
            post_message = bot.sendSticker(chat_id=chat_id, sticker=sticker, reply_markup=reply_markup)

    if destination == "admin":  # insert the post among the pending ones
        MemeData.insert_pending_post(user_message=message, admin_message=post_message)
    elif destination == "channel":  # insert the post among the published ones and show the credtit...
        if not config_map['meme']['comments']:  # ... but only if the user can vote directly on the post
            MemeData.insert_published_post(post_message)
            send_helper_message(user_id=user_id,
                                chat_id=config_map['meme']['channel_id'],
                                reply_message_id=post_message.message_id,
                                bot=bot)
    elif destination == "channel_group":  # insert the first comment among the published posts, so that votes can be tracked
        MemeData.insert_published_post(post_message)

    return post_message


def send_helper_message(user_id: int,
                        chat_id: int,
                        reply_message_id: int,
                        bot: Bot,
                        reply_markup: InlineKeyboardMarkup = None) -> Message:
    """Sends an helper message to show the author of the post, and to vote on the post if comments are enabled

    Args:
        user_id (int): id of the user that originated the post
        chat_id (int): id of the chat to which send the helper message
        reply_message_id (int): id of the message the helper message will reply to
        bot (Bot): bot
        reply_markup (InlineKeyboardMarkup, optional): voting Inline Keyboard. Defaults to None.

    Returns:
        Message: helper message
    """
    sign = anonym_name()
    if MemeData.is_credited(user_id=user_id):  # the user wants to be credited
        username = bot.getChat(user_id).username
        if username:
            sign = "@" + username

    return bot.send_message(chat_id=chat_id,
                            text=f"by: {sign}",
                            reply_markup=reply_markup,
                            reply_to_message_id=reply_message_id)


def show_admins_votes(chat_id: int, message_id: int, bot: Bot, approve: bool):
    """After a post is been approved or rejected, shows the admins that aproved or rejected it

    Args:
        chat_id (int): id of the admin group
        message_id (int): id of the post in question in the group
        bot (Bot): bot
        approve (bool): whether the vote is approve or reject
    """
    admins = MemeData.get_admin_list_votes(g_message_id=message_id, group_id=chat_id, approve=approve)
    text = "Approvato da:\n" if approve else "Rifiutato da:\n"
    for admin in admins:
        username = bot.get_chat(admin).username
        text += f"@{username}\n" if username else f"{bot.get_chat(admin).first_name}\n"

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    bot.send_message(chat_id=chat_id, text=text, reply_to_message_id=message_id)


def anonym_name() -> str:
    """Generates a name for an anonym user

        Returns:
            str: a name among the ones proposed
        """
    names = ("anonimo", "ciccio", "tizio", "puzzola", "patato", "literally who", "mucro", "topolino", "cribbio", "signorina",
             "pensione a Cuba", "aranciataLover", "hotlena", "darkangelcraft", "I PUFFI", "pippo", "my love", "?",
             "signor nessuno", "V per Vedetta (ops)", "bonk", "foot", "cycle", "impostore", "spook", "gessetto impaurito",
             "shitposter", "weeb")
    return choice(names)
