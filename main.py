# -*- coding: utf-8 -*-

from functions import *

bot = telegram.Bot(TOKEN)

#Function: main
#Main function that run the bot.
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    #Bot commands
    dp.add_handler(CommandHandler('start', start_cmd))
    dp.add_handler(CommandHandler('spot', spot_cmd))
    dp.add_handler(CommandHandler('help', help_cmd))
    dp.add_handler(CommandHandler('rules', rules_cmd))
    dp.add_handler(MessageHandler(Filters.reply , spot_get))
    dp.add_handler(CallbackQueryHandler( callback_spot))
    

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
