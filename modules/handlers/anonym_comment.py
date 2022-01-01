"""Anonym Comment on a post in the comment group"""
from logging import Logger
from random import choice
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from modules.data import config_map
from modules.data.data_reader import read_md
from modules.utils import EventInfo


def anonymous_comment_msg(update: Update, context: CallbackContext):
    """Handles a new anonym comment on a post in the comment group.
    Deletes the original post and sends a message with the same text, to avoid any abuse.

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    if info.chat_id == config_map['meme']['channel_group_id'] and info.message.via_bot is None:
        message = info.message
        poll = message.poll
        anon_credits = 'by: ' + choice(read_md("anonym_names").split("\n"))
        try:
            if poll or message.sticker:
              if poll:
                sent_message_id = info.bot.send_poll(chat_id=info.chat_id,
                                                  question=f'{poll.question}\n\n{anon_credits}',
                                                  options=[option.text for option in poll.options],
                                                  type=poll.type,
                                                  allows_multiple_answers=poll.allows_multiple_answers,
                                                  reply_to_message_id=info.message.reply_to_message.message_id if info.message.reply_to_message else None,
                                                  correct_option_id=poll.correct_option_id).message_id
              else:
                sent_message_id = info.bot.send_sticker(chat_id=info.chat_id,
                                                      sticker=message.sticker.file_id,
                                                      reply_to_message_id=info.message.reply_to_message.message_id if info.message.reply_to_message else None).message_id

              info.bot.send_message(chat_id=info.chat_id,
                                    text=anon_credits,
                                    reply_to_message_id=sent_message_id)
          
            elif message.text and message.entities:  # mantains the previews, if present
                info.bot.send_message(chat_id=info.chat_id,
                                      text=message.text + f'\n\n{anon_credits}',
                                      entities=message.entities,
                                      reply_to_message_id=info.message.reply_to_message.message_id if info.message.reply_to_message else None)
            else:
                info.bot.copy_message(chat_id=info.chat_id,
                                      from_chat_id=message.chat_id,
                                      message_id=message.message_id,
                                      caption=f'{message.caption}\n\n{anon_credits}' if message.caption else anon_credits,
                                      reply_to_message_id=info.message.reply_to_message.message_id if info.message.reply_to_message else None)
																			
        except (BadRequest) as e:
            Logger.error("Sending the comment on anonymous_comment_msg: %s", e)
            return False

        info.message.delete()
