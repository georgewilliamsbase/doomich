from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    document_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)
    lecture_id: uuid.UUID | None = None
    course_id: uuid.UUID | None = None


class ChatPatch(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ChatOut(BaseModel):
    id: uuid.UUID
    title: str | None
    document_ids: list[uuid.UUID]
    lecture_id: uuid.UUID | None = None
    course_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None


class Source(BaseModel):
    n: int
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str
    page: int | None = None
    sheet: str | None = None
    snippet: str
    cited: bool = True
    start: float | None = None


class MessageOut(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    mode: str
    sources: list[Source] = []
    model_version: str | None = None
    created_at: datetime


class ClientContextIn(BaseModel):
    """Данные с устройства для ответа. На сервере не сохраняются."""

    group_id: uuid.UUID | None = None
    subgroup: str | None = Field(default=None, max_length=16)
    teacher_key: str | None = Field(default=None, max_length=128)
    campus_id: uuid.UUID | None = None
    location_node_id: uuid.UUID | None = None


class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    mode: Literal["text", "voice"] = "text"
    document_ids: list[uuid.UUID] | None = Field(default=None, max_length=20)
    context: ClientContextIn = Field(default_factory=ClientContextIn)


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class IncognitoIn(MessageIn):
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)


class FeedbackIn(BaseModel):
    rating: Literal[-1, 1]
    message_id: uuid.UUID | None = None
    comment: str | None = Field(default=None, max_length=1000)
    category: Literal["wrong", "no_source", "voice", "slow", "other"] | None = None
    # Текст вопроса и ответа прикладывается только с явного согласия пользователя
    share_content: bool = False
    question: str | None = Field(default=None, max_length=8000)
    answer: str | None = Field(default=None, max_length=16000)
    model_version: str | None = Field(default=None, max_length=200)
    mode: Literal["text", "voice"] | None = None
