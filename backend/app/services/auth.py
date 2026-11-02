import hashlib
import os
import secrets
import threading
import time
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlalchemy import delete
from sqlalchemy.orm import Session as DBSession

from app.db import get_db
from app.models import LoginSessionRow, UserRow

COOKIE_NAME = "sid"
SESSION_DAYS = 7
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

password_hasher = PasswordHash.recommended()   # Argon2
# 없는 아이디로 로그인할 때도 비교 시간을 맞추기 위한 가짜 해시
DUMMY_HASH = password_hasher.hash("dummy-password-for-timing")


# ── 로그인 시도 제한 ─────────────────────────────────
# 같은 아이디로 10분 안에 5번 틀리면 10분 동안 로그인을 막는다. (비밀번호 맞히기 공격 방지)
# 서버 메모리에만 기록하므로 서버를 다시 켜면 초기화된다. 서버 프로세스가 하나라는 전제다.
MAX_LOGIN_FAILS = 5
LOGIN_WINDOW_SECONDS = 600

_login_fails: dict[str, list[float]] = {}
_login_fails_lock = threading.Lock()


def _recent_fails(key: str, now: float) -> list[float]:
    """10분 안의 실패 기록만 남긴다. (잠금 안에서 부른다)"""
    recent = [t for t in _login_fails.get(key, []) if now - t < LOGIN_WINDOW_SECONDS]
    if recent:
        _login_fails[key] = recent
    else:
        _login_fails.pop(key, None)
    return recent


def check_login_allowed(username: str) -> None:
    """실패가 너무 많으면 429로 막는다."""
    with _login_fails_lock:
        if len(_recent_fails(username.lower(), time.time())) >= MAX_LOGIN_FAILS:
            raise HTTPException(
                status_code=429,
                detail="로그인 시도가 너무 많습니다. 10분 뒤에 다시 시도해 주세요.",
            )


def record_login_failure(username: str) -> None:
    now = time.time()
    with _login_fails_lock:
        key = username.lower()
        _login_fails[key] = _recent_fails(key, now) + [now]


def clear_login_failures(username: str) -> None:
    with _login_fails_lock:
        _login_fails.pop(username.lower(), None)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def _hash_token(token: str) -> str:
    """쿠키의 토큰을 DB에 적을 값으로 바꾼다. DB가 유출돼도 이 값으로는 로그인할 수 없다."""
    return hashlib.sha256(token.encode()).hexdigest()


def start_login_session(db: DBSession, response: Response, user: UserRow) -> None:
    """로그인 처리: 토큰을 만들어 장부에 적고 쿠키로 내려준다."""
    now = datetime.now()
    # 이 사용자의 만료된 기록은 이참에 정리
    db.execute(
        delete(LoginSessionRow).where(
            LoginSessionRow.user_id == user.id, LoginSessionRow.expires_at < now
        )
    )
    token = secrets.token_urlsafe(32)
    db.add(
        LoginSessionRow(
            token_hash=_hash_token(token),
            user_id=user.id,
            expires_at=now + timedelta(days=SESSION_DAYS),
        )
    )
    db.commit()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )


def end_login_session(db: DBSession, request: Request, response: Response) -> None:
    """로그아웃 처리: 장부에서 지우고 쿠키도 지운다."""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.execute(delete(LoginSessionRow).where(LoginSessionRow.token_hash == _hash_token(token)))
        db.commit()
    response.delete_cookie(
        key=COOKIE_NAME, httponly=True, samesite="lax", secure=COOKIE_SECURE, path="/"
    )


def get_current_user(request: Request, db: DBSession = Depends(get_db)) -> UserRow:
    """쿠키로 현재 사용자를 찾는다. 로그인이 안 돼 있으면 401."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    row = db.get(LoginSessionRow, _hash_token(token))
    if row is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    if row.expires_at < datetime.now():
        db.delete(row)
        db.commit()
        raise HTTPException(status_code=401, detail="로그인이 만료되었습니다. 다시 로그인해 주세요.")

    user = db.get(UserRow, row.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return user