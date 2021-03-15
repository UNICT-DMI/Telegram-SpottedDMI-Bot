"""Modules that handle the events the bot recognizes and reacts to"""
from modules.data import config_map

CHAT_PRIVATE_ERROR = f"Non puoi usare quest comando ora\nChatta con {config_map['bot_tag']} in privato"
INVALID_MESSAGE_TYPE_ERROR = "Questo tipo di messaggio non è supportato\n"\
                                "È consentito solo testo, stikers, immagini, audio, video o poll\n"\
                                "Invia il post che vuoi pubblicare\n"\
                                "Puoi annullare il processo con /cancel"
STATE = {
    'posting': 1,
    'confirm': 2,
    'reporting_spot': 3,
    'reporting_user': 4,
    'reporting_user_reason': 6,
    'sending_user_report': 7,
    'end': -1
}
