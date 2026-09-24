from datetime import datetime

from pydantic import BaseModel

from app.schemas.domain import DomainOut


class TeamMemberOut(BaseModel):
    id: int
    name: str
    email: str | None

    model_config = {"from_attributes": True}


class TeamOut(BaseModel):
    id: int
    name: str
    college: str
    domain: DomainOut
    members: list[TeamMemberOut]
    leader_name: str
    leader_email: str
    leader_phone: str
    registered_at: datetime

    model_config = {"from_attributes": True}
