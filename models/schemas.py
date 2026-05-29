from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Modality(str, Enum):
    text = "text"
    image = "image"
    table = "table"
    audio = "audio"
    video = "video"
    document = "document"


class TextChunk(BaseModel):
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ImageAsset(BaseModel):
    uri: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TableAsset(BaseModel):
    markdown: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestionError(BaseModel):
    code: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestionResult(BaseModel):
    source_uri: str
    modality: Modality
    text_chunks: list[TextChunk] = Field(default_factory=list)
    image_assets: list[ImageAsset] = Field(default_factory=list)
    table_assets: list[TableAsset] = Field(default_factory=list)
    transcript: str | None = None
    errors: list[IngestionError] = Field(default_factory=list)


class VectorRecord(BaseModel):
    id: str
    source_uri: str
    modality: Modality
    text: str
    caption: str | None = None
    embedding: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)
    image_uri: str | None = None


class RetrievedRecord(BaseModel):
    id: str
    source_uri: str
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    image_uri: str | None = None


class ChatAnswer(BaseModel):
    text: str
    cited_records: list[RetrievedRecord] = Field(default_factory=list)
    image_uris: list[str] = Field(default_factory=list)
