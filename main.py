# -*- coding: utf-8 -*-
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from functions import TOKEN, start_cmd, spot_cmd, help_cmd, rules_cmd, ban_cmd,\
    message_handle, comment_msg, callback_spot

#Function: main
#Main function that run the bot.
def main():
    updater = Updater(TOKEN, request_kwargs={'read_timeout': 20, 'connect_timeout': 20}, use_context=True)
    dp = updater.dispatcher

    #Bot commands
    dp.add_handler(CommandHandler('start', start_cmd))
    dp.add_handler(CommandHandler('spot', spot_cmd))
    dp.add_handler(CommandHandler('help', help_cmd))
    dp.add_handler(CommandHandler('rules', rules_cmd))
    dp.add_handler(CommandHandler('ban', ban_cmd))
    dp.add_handler(MessageHandler(Filters.reply , message_handle))
    dp.add_handler(MessageHandler(Filters.forwarded, comment_msg))
    dp.add_handler(CallbackQueryHandler(callback_spot))


    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
