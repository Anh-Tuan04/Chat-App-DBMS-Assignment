from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from app.modules.repositories.conversations import (
    Conversation,
    ConversationRef,
    ConversationRepository,
    LastMessage,
)

from app.modules.repositories.messages import Message, MessageRepository
from app.modules.repositories.users import UserRepository

# Handle preview
@dataclass(frozen=True, slots=True)
class LastMessagePreview:
    message_id: int
    sender_id: int
    sender_name: str | None
    content: str                    
    sent_at: datetime

@dataclass(frozen=True, slots=True)
class ConversationSummary:
    conversation_id: int
    type: str
    name: str
    avatar_url: str | None
    last_message: LastMessagePreview | None
    unread_count: int





# Handle paging for conversation list of user
@dataclass(frozen=True, slots=True)
class ConversationCursor:
    sort_at: datetime
    conversation_id: int


@dataclass(frozen=True, slots=True)
class ConversationPage:
    items: list[ConversationSummary]
    next_cursor: ConversationCursor | None


class ConversationService:
    DEFAULT_PAGE_SIZE = 30
    MAX_PAGE_SIZE = 100
    PREVIEW_MAX_LEN = 100
    UNREAD_CAP = 99
    MAX_GROUP_NAME_LEN = 100

    def __init__(self, 
                 conversation: ConversationRepository, 
                 users: UserRepository, 
                 messages: MessageRepository):
        self._conversation = conversation
        self._users        = users
        self._messages     = messages


    
        