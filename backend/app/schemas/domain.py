from pydantic import BaseModel


class DomainOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None
    status: str

    model_config = {"from_attributes": True}


class DomainCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None


class DomainUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
