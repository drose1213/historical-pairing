import random
import string
import time
from threading import Lock

_CAPTCHA_STORE: dict[str, tuple[str, float]] = {}
_LOCK = Lock()
_EXPIRE_SECONDS = 300


def _cleanup_expired() -> None:
    now = time.time()
    expired_keys = [k for k, v in _CAPTCHA_STORE.items() if v[1] < now]
    for k in expired_keys:
        del _CAPTCHA_STORE[k]


def generate_captcha() -> tuple[str, str]:
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    op = random.choice(["+", "-", "×"])
    if op == "+":
        answer = str(a + b)
        question = f"{a} + {b} = ?"
    elif op == "-":
        answer = str(a - b)
        question = f"{a} - {b} = ?"
    else:
        answer = str(a * b)
        question = f"{a} × {b} = ?"

    token = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    with _LOCK:
        _cleanup_expired()
        _CAPTCHA_STORE[token] = (answer, time.time() + _EXPIRE_SECONDS)
    return token, question


def verify_captcha(token: str, user_answer: str) -> bool:
    with _LOCK:
        entry = _CAPTCHA_STORE.pop(token, None)
    if entry is None:
        return False
    answer, expires_at = entry
    if time.time() > expires_at:
        return False
    return user_answer.strip() == answer
