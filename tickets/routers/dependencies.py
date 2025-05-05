from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from tickets.database import get_db
from tickets.models import User, Project
from tickets.oauth2 import get_current_user

# supadmin
async def require_superadmin(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Requires superadmin privileges")
    return current_user

# proj admin
async def require_project_admin(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "superadmin":
        return current_user
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not project admin")
    return current_user