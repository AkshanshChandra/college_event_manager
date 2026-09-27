from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import Domain, Hint, ProblemStatement, User
from app.schemas.domain import DomainCreate, DomainOut, DomainUpdate
from app.schemas.hint import HintCreate, HintOut, HintUpdate
from app.schemas.problem_statement import ProblemStatementCreate, ProblemStatementOut, ProblemStatementUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/admin", tags=["admin"])


# --- Domains -----------------------------------------------------------

@router.get("/domains", response_model=list[DomainOut])
def list_domains(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[Domain]:
    return db.query(Domain).order_by(Domain.id.asc()).all()


@router.post("/domains", response_model=DomainOut)
def create_domain(payload: DomainCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> Domain:
    if db.query(Domain).filter(Domain.slug == payload.slug).one_or_none():
        raise HTTPException(status_code=409, detail="A domain with this slug already exists.")
    domain = Domain(**payload.model_dump())
    db.add(domain)
    db.commit()
    db.refresh(domain)
    log_action(db, admin, "create_domain", "domain", domain.id, {"name": domain.name})
    return domain


@router.put("/domains/{domain_id}", response_model=DomainOut)
def update_domain(
    domain_id: int, payload: DomainUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> Domain:
    domain = db.get(Domain, domain_id)
    if domain is None:
        raise HTTPException(status_code=404, detail="Domain not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(domain, field, value)
    db.commit()
    db.refresh(domain)
    log_action(db, admin, "update_domain", "domain", domain.id)
    return domain


# --- Problem statements --------------------------------------------------
# A domain has several problem statements (ADAPPT ships exactly three per
# domain), ordered by order_index.

@router.get("/problem-statements", response_model=list[ProblemStatementOut])
def list_problem_statements(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[ProblemStatement]:
    return db.query(ProblemStatement).order_by(ProblemStatement.domain_id, ProblemStatement.order_index).all()


@router.post("/problem-statements", response_model=ProblemStatementOut)
def create_problem_statement(
    payload: ProblemStatementCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> ProblemStatement:
    ps = ProblemStatement(**payload.model_dump())
    db.add(ps)
    db.commit()
    db.refresh(ps)
    log_action(db, admin, "create_problem_statement", "problem_statement", ps.id, {"title": ps.title})
    return ps


@router.put("/problem-statements/{ps_id}", response_model=ProblemStatementOut)
def update_problem_statement(
    ps_id: int, payload: ProblemStatementUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> ProblemStatement:
    ps = db.get(ProblemStatement, ps_id)
    if ps is None:
        raise HTTPException(status_code=404, detail="Problem statement not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ps, field, value)
    db.commit()
    db.refresh(ps)
    log_action(db, admin, "update_problem_statement", "problem_statement", ps.id)
    return ps


@router.delete("/problem-statements/{ps_id}", status_code=204)
def delete_problem_statement(
    ps_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> None:
    ps = db.get(ProblemStatement, ps_id)
    if ps is None:
        raise HTTPException(status_code=404, detail="Problem statement not found.")
    db.delete(ps)
    db.commit()
    log_action(db, admin, "delete_problem_statement", "problem_statement", ps_id)


@router.put("/problem-statements/{ps_id}/publish", response_model=ProblemStatementOut)
def set_problem_statement_status(
    ps_id: int, status: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> ProblemStatement:
    ps = db.get(ProblemStatement, ps_id)
    if ps is None:
        raise HTTPException(status_code=404, detail="Problem statement not found.")
    ps.status = status
    db.commit()
    db.refresh(ps)
    log_action(db, admin, f"set_problem_statement_status:{status}", "problem_statement", ps.id)
    return ps


# --- Hints -----------------------------------------------------------------

@router.get("/hints", response_model=list[HintOut])
def list_hints(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[Hint]:
    return db.query(Hint).order_by(Hint.week_number.asc()).all()


@router.post("/hints", response_model=HintOut)
def create_hint(payload: HintCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> Hint:
    hint = Hint(**payload.model_dump())
    db.add(hint)
    db.commit()
    db.refresh(hint)
    log_action(db, admin, "create_hint", "hint", hint.id, {"title": hint.title})
    return hint


@router.put("/hints/{hint_id}", response_model=HintOut)
def update_hint(
    hint_id: int, payload: HintUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> Hint:
    hint = db.get(Hint, hint_id)
    if hint is None:
        raise HTTPException(status_code=404, detail="Hint not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(hint, field, value)
    db.commit()
    db.refresh(hint)
    log_action(db, admin, "update_hint", "hint", hint.id)
    return hint


@router.delete("/hints/{hint_id}", status_code=204)
def delete_hint(hint_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> None:
    hint = db.get(Hint, hint_id)
    if hint is None:
        raise HTTPException(status_code=404, detail="Hint not found.")
    db.delete(hint)
    db.commit()
    log_action(db, admin, "delete_hint", "hint", hint_id)
