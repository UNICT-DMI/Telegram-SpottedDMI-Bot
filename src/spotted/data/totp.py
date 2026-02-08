"""TOTP (Time-based One-Time Password) management"""

from io import BytesIO

import pyotp
import qrcode

from .config import Config
from .db_manager import DbManager


class TotpManager:
    """Manages TOTP secrets and verification for users"""

    @staticmethod
    def is_enabled() -> bool:
        """Whether TOTP is enabled (either mandatory or optional)"""
        return bool(Config.post_get("totp", False)) or bool(Config.post_get("mandatory_totp", False))

    @staticmethod
    def is_required() -> bool:
        """Whether TOTP is mandatory for all users"""
        return bool(Config.post_get("mandatory_totp", False))

    @staticmethod
    def is_optional() -> bool:
        """Whether TOTP is optional (users can opt-in)"""
        return bool(Config.post_get("totp", False)) and not bool(Config.post_get("mandatory_totp", False))

    @staticmethod
    def has_totp(user_id: int) -> bool:
        """Checks if a user has a TOTP secret stored"""
        return DbManager.count_from(table_name="totp_secrets", where="user_id = %s", where_args=(user_id,)) > 0

    @staticmethod
    def get_secret(user_id: int) -> str | None:
        """Fetches the stored TOTP secret for a user"""
        result = DbManager.select_from(
            table_name="totp_secrets", select="secret", where="user_id = %s", where_args=(user_id,)
        )
        return result[0]["secret"] if result else None

    @staticmethod
    def create_secret(user_id: int) -> str:
        """Generates a new TOTP secret, stores it in the database, and returns it"""
        secret = pyotp.random_base32()
        DbManager.insert_into(table_name="totp_secrets", columns=("user_id", "secret"), values=(user_id, secret))
        return secret

    @staticmethod
    def verify(user_id: int, code: str) -> bool:
        """Verifies a TOTP code against the user's stored secret"""
        secret = TotpManager.get_secret(user_id)
        if secret is None:
            return False
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # valid_window=1 to allow for minor clock drift.

    @staticmethod
    def get_provisioning_uri(user_id: int, secret: str) -> str:
        """Returns the provisioning URI for the TOTP secret"""
        bot_tag = Config.settings_get("bot_tag", default="SpottedBot")
        issuer = bot_tag.lstrip("@")
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=str(user_id), issuer_name=issuer)

    @staticmethod
    def generate_qr_image(provisioning_uri: str) -> BytesIO:
        """Generates a QR code image from a provisioning URI and returns it as a BytesIO buffer"""
        img = qrcode.make(provisioning_uri)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @staticmethod
    def setup_user_totp(user_id: int) -> tuple[str, BytesIO]:
        """Creates a TOTP secret for the user and returns the secret and QR code image.

        Args:
            user_id: id of the user

        Returns:
            tuple of (secret, qr_image_buffer)
        """
        secret = TotpManager.create_secret(user_id)
        provisioning_uri = TotpManager.get_provisioning_uri(user_id, secret)
        qr_buffer = TotpManager.generate_qr_image(provisioning_uri)
        return secret, qr_buffer

    @staticmethod
    def user_needs_totp(user_id: int) -> bool:
        """Determines if a user needs to provide TOTP during the /spot flow.
        Returns True if TOTP is mandatory, or if TOTP is optional and the user has opted in.
        """
        if TotpManager.is_required():
            return True
        if TotpManager.is_optional() and TotpManager.has_totp(user_id):
            return True
        return False
