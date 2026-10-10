from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_participant
from app.database import get_db
from app.models import Blog, ProblemStatement, User
from app.models.enums import PublishStatus
from app.schemas.blog import BlogOut
from app.schemas.problem_statement import ProblemStatementOut
from app.schemas.submission import SubmissionOut, TeamSubmissionStateOut
from app.schemas.team import TeamMemberOut, TeamOut
from app.services.submissions import get_round_settings, participant_submission_status, window_status

router = APIRouter(prefix="/team", tags=["team"])


@router.get("", response_model=TeamOut)
def get_my_team(current_user: User = Depends(require_participant)) -> TeamOut:
    team = current_user.team
    registration = team.registration
    return TeamOut(
        id=team.id,
        name=team.name,
        college=team.college,
        domain=team.domain,
        members=[TeamMemberOut.model_validate(m) for m in team.members],
        leader_name=registration.leader_name,
        leader_email=registration.leader_email,
        leader_phone=registration.leader_phone,
        registered_at=registration.registered_at,
    )


@router.get("/problem-statements", response_model=list[ProblemStatementOut])
def get_my_problem_statements(
    current_user: User = Depends(require_participant), db: Session = Depends(get_db)
) -> list[ProblemStatement]:
    return (
        db.query(ProblemStatement)
        .filter(
            ProblemStatement.domain_id == current_user.team.domain_id,
            ProblemStatement.status == PublishStatus.PUBLISHED,
        )
        .order_by(ProblemStatement.order_index)
        .all()
    )


@router.get("/blog", response_model=BlogOut | None)
def get_my_blog(
    current_user: User = Depends(require_participant), db: Session = Depends(get_db)
) -> Blog | None:
    return (
        db.query(Blog)
        .filter(
            Blog.domain_id == current_user.team.domain_id,
            Blog.status == PublishStatus.PUBLISHED,
        )
        .one_or_none()
    )


@router.get("/submission", response_model=TeamSubmissionStateOut)
def get_my_submission_state(
    current_user: User = Depends(require_participant), db: Session = Depends(get_db)
) -> TeamSubmissionStateOut:
    team = current_user.team
    round_settings = get_round_settings(db)
    active = next((s for s in team.submissions if s.is_active_version), None)

    return TeamSubmissionStateOut(
        window_status=window_status(round_settings),
        participant_status=participant_submission_status(team, round_settings),
        submission_start=round_settings.submission_start,
        submission_end=round_settings.submission_end,
        allow_replacement=round_settings.allow_replacement,
        max_document_size_mb=round_settings.max_document_size_mb,
        max_video_size_mb=round_settings.max_video_size_mb,
        allowed_document_extensions=round_settings.allowed_document_extensions.split(","),
        allowed_video_extensions=round_settings.allowed_video_extensions.split(","),
        active_submission=SubmissionOut.model_validate(active) if active else None,
        versions=[SubmissionOut.model_validate(s) for s in sorted(team.submissions, key=lambda s: s.version)],
    )
