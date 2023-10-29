"""Constants used by the bot handlers"""
from modules.data import Config

CHAT_PRIVATE_ERROR = f"Non puoi usare quest comando ora\nChatta con {Config.settings_get('bot_tag')} in privato"
INVALID_MESSAGE_TYPE_ERROR = (
    "Questo tipo di messaggio non è supportato\n"
    "È consentito solo testo, stickers, immagini, audio, video o poll\n"
    "Invia il post che vuoi pubblicare\n"
    "Puoi annullare il processo con /cancel"
)
STATE = {
    "posting": 1,
    "confirm": 2,
    "reporting_spot": 3,
    "reporting_user": 4,
    "reporting_user_reason": 6,
    "sending_user_report": 7,
    "end": -1,
}
