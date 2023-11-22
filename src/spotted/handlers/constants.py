"""Constants used by the bot handlers"""
from enum import Enum, auto, unique

CHAT_PRIVATE_ERROR = "Non puoi usare quest comando ora\nMandami un messaggio in privato"
INVALID_MESSAGE_TYPE_ERROR = (
    "Questo tipo di messaggio non è supportato\n"
    "È consentito solo testo, stickers, immagini, audio, video o poll\n"
    "Invia il post che vuoi pubblicare\n"
    "Puoi annullare il processo con /cancel"
)


@unique
class ConversationState(Enum):
    """Enum for the states of the conversation.
    The end state must have value -1, since it is the convention used by the ConversationHandler
    to terminate the conversation.
    """

    POSTING = auto()  # the user is sending a new post
    POSTING_PREVIEW = auto()  # the user can choose whether to disable the post's link preview
    POSTING_CONFIRM = auto()  # the user is confirming that they want to send the post to the admins
    REPORTING_SPOT = auto()  # the user is reporting a post
    REPORTING_USER = auto()  # the user is reporting a user
    REPORTING_USER_REASON = auto()  # the user reports a user and has to specify the reason
    SENDING_USER_REPORT = auto()  # the user has to confirm the report of a user
    END = -1  # the conversation has ended
