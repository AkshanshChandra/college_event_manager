from pydantic import BaseModel


class ProblemStatementOut(BaseModel):
    id: int
    domain_id: int
    title: str
    description: str
    requirements: str | None
    constraints: str | None
    deliverables: str | None
    supporting_material_url: str | None
    status: str

    model_config = {"from_attributes": True}


class ProblemStatementUpsert(BaseModel):
    domain_id: int
    title: str
    description: str
    requirements: str | None = None
    constraints: str | None = None
    deliverables: str | None = None
    supporting_material_url: str | None = None


class ProblemStatementPublishUpdate(BaseModel):
    status: str
