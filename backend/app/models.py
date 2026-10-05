from datetime import datetime
from sqlalchemy import String, Integer, Float, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="processing")
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    turning_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    utterances: Mapped[list["UtteranceRow"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="UtteranceRow.idx",
    )


class UtteranceRow(Base):
    __tablename__ = "utterances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    idx: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(String(2000))
    scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    top: Mapped[str | None] = mapped_column(String(10), nullable=True)
    top_sub: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    session: Mapped["SessionRow"] = relationship(back_populates="utterances")