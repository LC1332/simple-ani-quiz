from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field

Level = Literal["easy", "medium", "hard"]
QuestionType = Literal["image_to_name", "name_to_image"]


class NameOption(BaseModel):
    character_id: int
    name_cn: str
    main_series: str


class ImageOption(BaseModel):
    character_id: int
    cos_image_id: int


class QuestionImageToName(BaseModel):
    id: str
    type: Literal["image_to_name"] = "image_to_name"
    cos_image_id: int
    options: List[NameOption]
    answer_character_id: int


class QuestionNameToImage(BaseModel):
    id: str
    type: Literal["name_to_image"] = "name_to_image"
    character_id: int
    name_cn: str
    main_series: str
    options: List[ImageOption]
    answer_character_id: int


QuizQuestion = Annotated[
    Union[QuestionImageToName, QuestionNameToImage],
    Field(discriminator="type"),
]


class QuizResponse(BaseModel):
    level: Level
    questions: List[QuizQuestion] = Field(default_factory=list)


class BannerResponse(BaseModel):
    cos_image_ids: List[int]


class QuizSubmitBody(BaseModel):
    level: Level
    score: Optional[int] = None
    answers: Optional[List[dict]] = None


class QuizSubmitResponse(BaseModel):
    ok: bool = True
    message: str = "not implemented; client score is authoritative for now"
    received_score: Optional[int] = None


class FeedbackBody(BaseModel):
    message: str = ""
    question_id: Optional[str] = None


class PlaceholderResponse(BaseModel):
    ok: bool = False
    message: str = "not implemented"


class CertificateQrResponse(BaseModel):
    ok: bool = False
    message: str = "not implemented"
