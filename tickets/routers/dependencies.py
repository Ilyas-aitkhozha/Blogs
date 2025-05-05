from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from tickets.database import get_db
from tickets.oauth2 import get_current_user
from tickets.models import User, UserTeam, ProjectUser
from tickets.enums import TeamRole, ProjectRole


async def require_authenticated(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


async def require_team_member(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
) -> User:
    link = (
        db.query(UserTeam)
          .filter(team_id=team_id, user_id=current_user.id)
          .first()
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )
    return current_user


async def require_team_admin(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_team_member),
) -> User:
    link = (
        db.query(UserTeam)
          .filter(team_id=team_id, user_id=current_user.id)
          .first()
    )
    if link.role != TeamRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires team admin role",
        )
    return current_user


async def require_project_member(
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated),
) -> User:
    link = (
        db.query(ProjectUser)
          .filter(project_id=project_id, user_id=current_user.id)
          .first()
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )
    return current_user


async def require_project_admin(
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_member),
) -> User:
    link = (
        db.query(ProjectUser)
          .filter(project_id=project_id, user_id=current_user.id)
          .first()
    )
    if link.role != ProjectRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires project admin role",
        )
    return current_user


async def require_project_worker(
    project_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_member),
) -> User:
    link = (
        db.query(ProjectUser)
          .filter(project_id=project_id, user_id=current_user.id)
          .first()
    )
    if link.role != ProjectRole.worker.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires project worker role",
        )
    return current_user
