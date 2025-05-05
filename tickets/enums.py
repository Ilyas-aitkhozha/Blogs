from enum import Enum

class TeamRole(str, Enum):
    admin  = "admin"   # supadmin
    member = "member"  # just a member

class ProjectRole(str, Enum):
    admin   = "admin"   # admin project
    member  = "member"
    worker  = "worker"

class TicketStatus(str, Enum):
    open        = "open"
    in_progress = "in_progress"
    closed      = "closed"

class TicketPriority(str, Enum):
    low         = "low"
    medium      = "medium"
    high        = "high"