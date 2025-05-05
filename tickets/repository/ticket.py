from typing import List
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from tickets import models
from tickets.models import UserTeam, ProjectUser
from tickets.schemas.ticket import TicketCreate, TicketOut, TicketStatusUpdate,TicketAssigneeUpdate, TicketFeedbackUpdate
from tickets.enums import ProjectRole

#--------------------------------------- CREATE

def create_ticket(
    db: Session,
    ticket_in: TicketCreate,
    user_id: int,
    team_id: int,
    project_id: int,
) -> TicketOut:#checks for if you are in team
    user_team_links = (
        db.query(UserTeam)
        .filter_by(user_id=user_id)
        .all()
    )
    user_team_ids = {link.team_id for link in user_team_links}
    if team_id not in user_team_ids:
        raise HTTPException(status_code=403, detail="You are not a member of this team")
    #for projects
    user_project_links = (
        db.query(ProjectUser)
        .filter_by(user_id=user_id)
        .all()
    )
    user_project_ids = {link.project_id for link in user_project_links}
    if project_id not in user_project_ids:
        raise HTTPException(status_code=403,detail="You are not a member of this project")

    assigned_user_id = None
    if ticket_in.assigned_to_name:
        assigned = (
            db.query(models.User)
              .filter(
                  models.User.name == ticket_in.assigned_to_name,
                  models.User.teams.any(UserTeam.team_id == team_id)
              )
              .first()
        )
        if not assigned:
            raise HTTPException(status_code=404, detail="Assigned user not found in this team")
        # cheks role in project : member или worker
        role_link = (
            db.query(ProjectUser)
              .filter_by(user_id=assigned.id, project_id=project_id)
              .first()
        )
        if not role_link or role_link.role not in (ProjectRole.member, ProjectRole.worker):
            raise HTTPException(status_code=403, detail="Assigned user not in this project")
        if not assigned.is_available:
            raise HTTPException(status_code=400, detail="Assigned user not available")
        assigned_user_id = assigned.id

    new_ticket = models.Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        created_by=user_id,
        assigned_to=assigned_user_id,
        team_id=team_id,
        project_id=project_id,
        priority=ticket_in.priority
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return _load_ticket_with_users(db, new_ticket.id)

#------------------------------ GET LOGICS

def get_ticket_by_id(db: Session, ticket_id: int, team_id: int) -> TicketOut:
    ticket = (
        db.query(models.Ticket)
          .options(
              joinedload(models.Ticket.creator),
              joinedload(models.Ticket.assignee)
          )
          .filter(
              models.Ticket.id == ticket_id,
              models.Ticket.team_id == team_id
          )
          .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return TicketOut.model_validate(ticket)

def get_all_tickets(db: Session, team_id: int) -> List[TicketOut]:
    tickets = (
        db.query(models.Ticket)
          .options(
              joinedload(models.Ticket.creator),
              joinedload(models.Ticket.assignee)
          )
          .filter(models.Ticket.team_id == team_id)
          .all()
    )
    return [TicketOut.model_validate(t) for t in tickets]

def get_user_tickets(db: Session, user_id: int, team_id: int) -> List[TicketOut]:
    tickets = (
        db.query(models.Ticket)
          .options(
              joinedload(models.Ticket.creator),
              joinedload(models.Ticket.assignee)
          )
          .filter(
              models.Ticket.created_by == user_id,
              models.Ticket.team_id == team_id
          )
          .all()
    )
    return [TicketOut.model_validate(t) for t in tickets]

def get_tickets_assigned_to_user(db: Session,current_user: models.User,team_id: int) -> List[TicketOut]:
    if not any(ut.team_id == team_id for ut in current_user.user_teams):
        raise HTTPException(status_code=403, detail="You are not a member of this team")

    tickets = (
        db.query(models.Ticket)
          .options(
              joinedload(models.Ticket.creator),
              joinedload(models.Ticket.assignee)
          )
          .filter(
              models.Ticket.assigned_to == current_user.id,
              models.Ticket.team_id == team_id,
              models.Ticket.status.in_(["open", "in_progress"])
          )
          .all()
    )
    return [TicketOut.model_validate(t) for t in tickets]

#-------------------------------- UPDATE LOGIC

ALLOWED_STATUS_TRANSITIONS = {
    "open": ["in_progress"],
    "in_progress": ["closed"],
    "closed": [],
}

def update_ticket_status_by_assignee(
    db: Session,
    ticket_id: int,
    team_id: int,
    update: TicketStatusUpdate,
    current_user: models.User
) -> TicketOut:
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id,
        models.Ticket.team_id == team_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assignee can update the status")

    curr = ticket.status.value
    nxt = update.status.value
    if nxt not in ALLOWED_STATUS_TRANSITIONS[curr]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {curr} to {nxt}. Allowed: {ALLOWED_STATUS_TRANSITIONS[curr]}"
        )

    ticket.status = update.status
    if update.status == models.TicketStatus.closed:
        ticket.closed_at = datetime.now(timezone.utc)
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    return _load_ticket_with_users(db, ticket.id)

def leave_feedback_by_creator(
    db: Session,
    ticket_id: int,
    team_id: int,
    update: TicketFeedbackUpdate,
    current_user: models.User
) -> TicketOut:
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id,
        models.Ticket.team_id == team_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can leave feedback")
    if ticket.status != models.TicketStatus.closed:
        raise HTTPException(status_code=400, detail="Feedback only after closure")

    if update.feedback is not None:
        ticket.feedback = update.feedback
    ticket.confirmed = update.confirmed
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    return _load_ticket_with_users(db, ticket.id)

def update_ticket_assignee(db: Session,ticket_id: int,update: TicketAssigneeUpdate,team_id: int) -> TicketOut:
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id,
        models.Ticket.team_id == team_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # checkign if admin?
    is_admin = (
        db.query(ProjectUser)
          .filter_by(
              user_id=update.assigned_to,
              project_id=ticket.project_id,
              role=ProjectRole.admin.value
          )
          .first()
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only project admin can reassign tickets")

    new_user = (
        db.query(models.User)
          .filter(
              models.User.id == update.assigned_to,
              models.User.teams.any(UserTeam.team_id == team_id)
          )
          .first()
    )
    if not new_user:
        raise HTTPException(status_code=404, detail="Assigned user not in this team")
    if not new_user.is_available:
        raise HTTPException(status_code=400, detail="Assigned user not available")

    ticket.assigned_to = update.assigned_to
    db.commit()
    return _load_ticket_with_users(db, ticket.id)

#-------------------------------- DELETE TICKET
def delete_ticket(
    db: Session,
    ticket_id: int,
    team_id: int,
    current_user: models.User,
) -> None:
    ticket = (
        db.query(models.Ticket)
          .filter(
              models.Ticket.id == ticket_id,
              models.Ticket.team_id == team_id
          )
          .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    # only creator or admin can delete
    is_creator = ticket.created_by == current_user.id
    is_proj_admin = any(
        pu.project_id == ticket.project_id and pu.role is ProjectRole.admin
        for pu in current_user.project_users
    )
    if not (is_creator or is_proj_admin):
        raise HTTPException(status_code=403, detail="Not permitted to delete this ticket")

    db.delete(ticket)
    db.commit()

#-------------------------------- HELPER

def _load_ticket_with_users(db: Session, ticket_id: int) -> TicketOut:
    ticket = (
        db.query(models.Ticket)
          .options(
              joinedload(models.Ticket.creator),
              joinedload(models.Ticket.assignee)
          )
          .filter(models.Ticket.id == ticket_id)
          .first()
    )
    return TicketOut.model_validate(ticket)