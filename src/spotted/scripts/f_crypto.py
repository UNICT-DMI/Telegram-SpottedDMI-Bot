import argparse
from base64 import b64decode, b64encode
from typing import TYPE_CHECKING

from cryptography.fernet import Fernet

if TYPE_CHECKING:
    from typing import Literal

    class DecryptArgs(argparse.Namespace):
        """Type hinting for the command line arguments"""

        command: Literal["encrypt", "decrypt", "generate_key"]
        encrypted_file: str
        decrypted_file: str
        key: bytes


def parse_args() -> "DecryptArgs":
    """Parse the command line arguments

    Returns:
        data structure containing the command line arguments
    """

    def base64(s: str) -> bytes:
        return b64decode(s)

    parser = argparse.ArgumentParser()
    # subparsers = crypt, decrypt, generate_key
    subparsers = parser.add_subparsers(dest="command", required=True)

    # crypt
    encrypt_parser = subparsers.add_parser("encrypt")
    encrypt_parser.add_argument("decrypted_file", type=str, help="Path to the decrypted file")
    encrypt_parser.add_argument("encrypted_file", type=str, help="Path to the encrypted file")
    encrypt_parser.add_argument("-k", "--key", required=True, type=base64, help="Base64 encoded key")

    # decrypt
    decrypt_parser = subparsers.add_parser("decrypt")
    decrypt_parser.add_argument("encrypted_file", type=str, help="Path to the encrypted file")
    decrypt_parser.add_argument("decrypted_file", type=str, help="Path to the decrypted file")
    decrypt_parser.add_argument("-k", "--key", required=True, type=base64, help="Base64 encoded key")

    # generate_key
    subparsers.add_parser("generate_key")

    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()
    if args.command == "generate_key":
        print(b64encode(Fernet.generate_key()).decode("utf-8"))
    elif args.command == "encrypt":
        with open(args.decrypted_file, "rb") as database_file:
            decrypted = database_file.read()
        f = Fernet(args.key)
        encrypted = f.encrypt(decrypted)
        with open(args.encrypted_file, "wb") as database_file:
            database_file.write(encrypted)
    elif args.command == "decrypt":
        with open(args.encrypted_file, "rb") as database_file:
            encrypted = database_file.read()
        f = Fernet(args.key)
        decrypted = f.decrypt(encrypted)
        with open(args.decrypted_file, "wb") as database_file:
            database_file.write(decrypted)


if __name__ == "__main__":
    main()
