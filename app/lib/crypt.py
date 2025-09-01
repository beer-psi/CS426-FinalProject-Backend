import anyio.to_thread
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#argon2id
_ph = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1)


async def verify_password(hash: str | bytes, password: str | bytes):  # noqa: A002
    try:
        return await anyio.to_thread.run_sync(_ph.verify, hash, password)
    except VerifyMismatchError:
        return False


async def hash_password(password: str | bytes):
    return await anyio.to_thread.run_sync(_ph.hash, password)
