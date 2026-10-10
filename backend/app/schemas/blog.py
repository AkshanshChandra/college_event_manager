from pydantic import BaseModel


class BlogOut(BaseModel):
    id: int
    domain_id: int
    title: str
    content: str
    status: str

    model_config = {"from_attributes": True}


class BlogCreate(BaseModel):
    domain_id: int
    title: str
    content: str
    status: str = "draft"


class BlogUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    status: str | None = None
