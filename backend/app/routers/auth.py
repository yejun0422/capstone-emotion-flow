from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.db import get_db
from app.models import UserRow
from app.schemas import LoginRequest, SignupRequest, User
from app.services.auth import (
    DUMMY_HASH,
    end_login_session,
    get_current_user,
    hash_password,
    start_login_session,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=User, status_code=201)
def signup(body: SignupRequest, response: Response, db: DBSession = Depends(get_db)):
    """회원가입. 가입하면 바로 로그인 상태가 된다."""
    exists = db.scalar(select(UserRow).where(UserRow.username == body.username))
    if exists:
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")

    user = UserRow(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    start_login_session(db, response, user)
    return User(id=user.id, username=user.username)


@router.post("/login", response_model=User)
def login(body: LoginRequest, response: Response, db: DBSession = Depends(get_db)):
    """로그인. 성공하면 쿠키가 내려간다."""
    user = db.scalar(select(UserRow).where(UserRow.username == body.username))
    if user is None:
        verify_password(body.password, DUMMY_HASH)   # 없는 아이디여도 같은 시간이 걸리게
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    start_login_session(db, response, user)
    return User(id=user.id, username=user.username)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: DBSession = Depends(get_db)):
    """로그아웃. 로그인 안 된 상태에서 불러도 오류 없이 끝난다."""
    end_login_session(db, request, response)


@router.get("/me", response_model=User)
def me(user: UserRow = Depends(get_current_user)):
    """지금 로그인한 사용자. 로그인 안 돼 있으면 401."""
    return User(id=user.id, username=user.username)