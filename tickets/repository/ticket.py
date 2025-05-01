from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from tickets import models
from tickets.schemas.ticket import TicketCreate, TicketUpdate, TicketOut


# ────────────────────────── CREATE ──────────────────────────
def create_ticket(
    db: Session,
    ticket_in: TicketCreate,
    user_id: int,
    team_id: int,
) -> TicketOut:
    """Создать тикет в выбранной команде."""
    # 1. Проверяем назначаемого админа (если указан) — только из этой команды
    assigned_user_id = None
    if ticket_in.assigned_to_name:
        assigned_user = (
            db.query(models.User)
            .filter(
                models.User.name == ticket_in.assigned_to_name,
                models.User.teams.any(models.Team.id == team_id)
            )
            .first()
        )
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found in this team")
        if not assigned_user.is_available:
            raise HTTPException(status_code=400, detail="Assigned user not available")
        assigned_user_id = assigned_user.id

    new_ticket = models.Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        created_by=user_id,
        assigned_to=assigned_user_id,
        team_id=team_id,
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return _load_ticket_with_users(db, new_ticket.id)


# ────────────────────────── READ ──────────────────────────
def get_ticket_by_id(db: Session, ticket_id: int, team_id: int) -> TicketOut:
    """Вернуть тикет по id в пределах команды."""
    ticket = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(models.Ticket.id == ticket_id, models.Ticket.team_id == team_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return TicketOut.model_validate(ticket)


def get_all_tickets(db: Session, team_id: int) -> List[TicketOut]:
    """Все тикеты команды."""
    tickets = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(models.Ticket.team_id == team_id)
        .all()
    )
    return [TicketOut.model_validate(t) for t in tickets]


def get_user_tickets(db: Session, user_id: int, team_id: int) -> List[TicketOut]:
    """Тикеты, созданные пользователем в этой команде."""
    tickets = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(models.Ticket.created_by == user_id, models.Ticket.team_id == team_id)
        .all()
    )
    return [TicketOut.model_validate(t) for t in tickets]


def get_tickets_assigned_to_user(
    db: Session,
    current_user: models.User,
    team_id: int,
) -> List[TicketOut]:
    """Открытые тикеты, назначенные на текущего админа в этой команде."""
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins can view assigned tickets.")

    tickets = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(
            models.Ticket.assigned_to == current_user.id,
            models.Ticket.team_id == team_id,
            models.Ticket.status.in_(["open", "in_progress"]),
        )
        .all()
    )
    return [TicketOut.model_validate(t) for t in tickets]


ALLOWED_STATUS_TRANSITIONS = {
    "open": ["in_progress"],
    "in_progress": ["closed"],
    "closed": [],
}


def update_ticket(
    db: Session,
    ticket_id: int,
    ticket_upd: TicketUpdate,
    current_user: models.User,
    team_id: int,
) -> TicketOut:
    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.id == ticket_id, models.Ticket.team_id == team_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    # 1. Изменение статуса — только админ, назначенный на тикет
    if ticket_upd.status is not None:
        if current_user.role != models.UserRole.admin:
            raise HTTPException(status_code=403, detail="Only admins can update status.")
        if ticket.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="You can update only your own tickets.")

        curr = ticket.status.value
        nxt = ticket_upd.status.value
        if nxt not in ALLOWED_STATUS_TRANSITIONS[curr]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {curr} to {nxt}. Allowed: {ALLOWED_STATUS_TRANSITIONS[curr]}",
            )
        ticket.status = ticket_upd.status

    # 2. Переназначение — только автор юзер
    if ticket_upd.assigned_to is not None:
        if current_user.role != models.UserRole.user:
            raise HTTPException(status_code=403, detail="Only users can assign tickets.")
        if ticket.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Only creator can reassign the ticket.")

        new_admin = (
            db.query(models.User)
            .filter(
                models.User.id == ticket_upd.assigned_to,
                models.User.teams.any(models.Team.id == team_id),
            )
            .first()
        )
        if not new_admin:
            raise HTTPException(status_code=404, detail="Assigned user not found in this team")
        if not new_admin.is_available:
            raise HTTPException(status_code=400, detail="Assigned user is not available")

        ticket.assigned_to = ticket_upd.assigned_to

    db.commit()
    return _load_ticket_with_users(db, ticket.id)


def delete_ticket(
    db: Session,
    ticket_id: int,
    team_id: int,
    current_user: models.User,
) -> None:
    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.id == ticket_id, models.Ticket.team_id == team_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    if ticket.created_by != current_user.id and current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Not permitted to delete this ticket.")

    db.delete(ticket)
    db.commit()

def _load_ticket_with_users(db: Session, ticket_id: int) -> TicketOut:
    ticket = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.creator), joinedload(models.Ticket.assignee))
        .filter(models.Ticket.id == ticket_id)
        .first()
    )
    return TicketOut.model_validate(ticket)