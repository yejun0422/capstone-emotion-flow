from typing import Literal
from pydantic import BaseModel

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