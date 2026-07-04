"""SQLAlchemy ORM models.

Importing this package registers every model on ``Base.metadata`` so that
``init_db`` can create the full schema.
"""

from app.models.base import Base, TimestampMixin, new_id, utcnow
from app.models.conversation import Conversation, Message, MessageRole
from app.models.events import ActionStatus, AssistantAction, SystemEvent
from app.models.user import Preference, UserProfile

__all__ = [
    "ActionStatus",
    "AssistantAction",
    "Base",
    "Conversation",
    "Message",
    "MessageRole",
    "Preference",
    "SystemEvent",
    "TimestampMixin",
    "UserProfile",
    "new_id",
    "utcnow",
]
