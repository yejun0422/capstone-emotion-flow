from typing import Literal
from pydantic import BaseModel, Field

Emotion = Literal["불안", "분노", "상처", "슬픔", "당황", "기쁨"]
Speaker = Literal["상담자", "내담자"]
SessionStatus = Literal["processing", "done", "failed"]

class Utterance(BaseModel):
    index: int
    speaker: Speaker
    text: str
    scores: dict[Emotion, float] | None
    top: Emotion | None
    topSub: str | None
    confidence: float | None


class Summary(BaseModel):
    dominant: Emotion
    volatility: float
    lowConfidenceRatio: float


class Session(BaseModel):
    sessionId: str
    fileName: str
    speakers: list[Speaker]
    emotions: list[Emotion]
    utterances: list[Utterance]
    turningPoints: list[int]
    summary: Summary


class SessionStatusResponse(BaseModel):
    """화면 2의 진행률용"""
    sessionId: str
    status: SessionStatus
    done: int
    total: int


class SessionListItem(BaseModel):
    """화면 5의 목록용"""
    sessionId: str
    fileName: str
    status: SessionStatus
    createdAt: str
    utteranceCount: int
    turningCount: int
    tops: list[Emotion | None]   # 색 띠 축소판용


class SignupRequest(BaseModel):
    """회원가입 요청"""
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """로그인 요청 — 형식 검사는 하지 않고 맞는지만 본다"""
    username: str
    password: str


class User(BaseModel):
    """로그인한 사용자 정보"""
    id: int
    username: str