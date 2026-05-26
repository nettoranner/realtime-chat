from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()

class Hash:

    @staticmethod
    def hash_password(password: str):
        return password_hash.hash(password)

    @staticmethod
    def verify_password(
        password: str,
        hashed: str,
    ):
        return password_hash.verify(
            password,
            hashed,
        )
    