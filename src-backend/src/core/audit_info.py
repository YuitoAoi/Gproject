import enum, uuid
from .entity_base import EntityBase


class AuditInfoType(enum.Enum):
    ACCOUNT = "ACCOUNT"
    MODEL = "MODEL"
    DATASET = "DATASET"
    SYSTEM = "SYSTEM"


class AuditInfoLevel(enum.Enum):
    INFO = 0
    SUCCESS = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class AuditInfo(EntityBase):
    id: uuid.UUID
    level: AuditInfoLevel
    owner_id: uuid.UUID
    message: str
    type: AuditInfoType
