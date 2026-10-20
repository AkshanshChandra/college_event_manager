from pydantic import BaseModel

from app.schemas.domain import DomainOut


class QualifiedTeamOut(BaseModel):
    id: int
    domain_id: int
    team_name: str
    college: str | None
    order_index: int

    model_config = {"from_attributes": True}


class QualifiedTeamPublicOut(BaseModel):
    id: int
    team_name: str
    college: str | None
    order_index: int
    domain: DomainOut

    model_config = {"from_attributes": True}


class QualifiedTeamCreate(BaseModel):
    domain_id: int
    team_name: str
    college: str | None = None
    order_index: int = 1


class QualifiedTeamUpdate(BaseModel):
    domain_id: int | None = None
    team_name: str | None = None
    college: str | None = None
    order_index: int | None = None


class ResultsSettingsOut(BaseModel):
    is_published: bool
    announcement: str | None

    model_config = {"from_attributes": True}


class ResultsSettingsUpdate(BaseModel):
    is_published: bool | None = None
    announcement: str | None = None


class PublicResultsOut(BaseModel):
    is_published: bool
    announcement: str | None
    teams: list[QualifiedTeamPublicOut]
