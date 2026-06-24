from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

sessions = {}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_session(user_id: int) -> str:
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = user_id
    return session_token


def get_user_id_by_session(session_token: str):
    return sessions.get(session_token)


def delete_session(session_token: str):
    if session_token in sessions:
        del sessions[session_token]


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)