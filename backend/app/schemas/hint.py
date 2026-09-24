from datetime import datetime

from pydantic import BaseModel


class HintOut(BaseModel):
    id: int
    week_number: int
    title: str
    content: str
    scope: str
    domain_id: int | None
    publish_at: datetime
    status: str

    model_config = {"from_attributes": True}


class HintCreate(BaseModel):
    week_number: int
    title: str
    content: str
    scope: str = "global"
    domain_id: int | None = None
    publish_at: datetime
    status: str = "draft"


class HintUpdate(BaseModel):
    week_number: int | None = None
    title: str | None = None
    content: str | None = None
    scope: str | None = None
    domain_id: int | None = None
    publish_at: datetime | None = None
    status: str | None = None
