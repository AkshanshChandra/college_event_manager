from pydantic import BaseModel


class ProblemStatementOut(BaseModel):
    id: int
    domain_id: int
    order_index: int
    title: str
    description: str
    requirements: str | None
    constraints: str | None
    deliverables: str | None
    supporting_material_url: str | None
    status: str

    model_config = {"from_attributes": True}


class ProblemStatementCreate(BaseModel):
    domain_id: int
    order_index: int = 1
    title: str
    description: str
    requirements: str | None = None
    constraints: str | None = None
    deliverables: str | None = None
    supporting_material_url: str | None = None
    status: str = "draft"


class ProblemStatementUpdate(BaseModel):
    order_index: int | None = None
    title: str | None = None
    description: str | None = None
    requirements: str | None = None
    constraints: str | None = None
    deliverables: str | None = None
    supporting_material_url: str | None = None
    status: str | None = None
