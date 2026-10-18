from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Message(_message.Message):
    __slots__ = ("message_id", "sender_id", "content", "created_at", "edited_at")
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EDITED_AT_FIELD_NUMBER: _ClassVar[int]
    message_id: int
    sender_id: int
    content: str
    created_at: int
    edited_at: int
    def __init__(self, message_id: _Optional[int] = ..., sender_id: _Optional[int] = ..., content: _Optional[str] = ..., created_at: _Optional[int] = ..., edited_at: _Optional[int] = ...) -> None: ...

class Conversation(_message.Message):
    __slots__ = ("conversation_id", "conversation_type", "last_message_id", "last_message_content", "last_message_sender_id", "last_message_at", "unread_count")
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    CONVERSATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    LAST_MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    LAST_MESSAGE_CONTENT_FIELD_NUMBER: _ClassVar[int]
    LAST_MESSAGE_SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    LAST_MESSAGE_AT_FIELD_NUMBER: _ClassVar[int]
    UNREAD_COUNT_FIELD_NUMBER: _ClassVar[int]
    conversation_id: int
    conversation_type: str
    last_message_id: int
    last_message_content: str
    last_message_sender_id: int
    last_message_at: int
    unread_count: int
    def __init__(self, conversation_id: _Optional[int] = ..., conversation_type: _Optional[str] = ..., last_message_id: _Optional[int] = ..., last_message_content: _Optional[str] = ..., last_message_sender_id: _Optional[int] = ..., last_message_at: _Optional[int] = ..., unread_count: _Optional[int] = ...) -> None: ...

class SendMessageRequest(_message.Message):
    __slots__ = ("conversation_id", "sender_id", "content")
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    conversation_id: int
    sender_id: int
    content: str
    def __init__(self, conversation_id: _Optional[int] = ..., sender_id: _Optional[int] = ..., content: _Optional[str] = ...) -> None: ...

class SendMessageResponse(_message.Message):
    __slots__ = ("success", "err")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    err: str
    def __init__(self, success: _Optional[bool] = ..., err: _Optional[str] = ...) -> None: ...

class GetMessageForUserRequest(_message.Message):
    __slots__ = ("conversation_id", "user_id", "limit", "before_message_id")
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    BEFORE_MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    conversation_id: int
    user_id: int
    limit: int
    before_message_id: int
    def __init__(self, conversation_id: _Optional[int] = ..., user_id: _Optional[int] = ..., limit: _Optional[int] = ..., before_message_id: _Optional[int] = ...) -> None: ...

class GetMessageForUserResponse(_message.Message):
    __slots__ = ("success", "messages", "next_cursor", "err")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    ERR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    messages: _containers.RepeatedCompositeFieldContainer[Message]
    next_cursor: int
    err: str
    def __init__(self, success: _Optional[bool] = ..., messages: _Optional[_Iterable[_Union[Message, _Mapping]]] = ..., next_cursor: _Optional[int] = ..., err: _Optional[str] = ...) -> None: ...

class GetConversationByUserRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    def __init__(self, user_id: _Optional[int] = ...) -> None: ...

class GetConversationByUserResponse(_message.Message):
    __slots__ = ("success", "conversations", "err")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    CONVERSATIONS_FIELD_NUMBER: _ClassVar[int]
    ERR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    conversations: _containers.RepeatedCompositeFieldContainer[Conversation]
    err: str
    def __init__(self, success: _Optional[bool] = ..., conversations: _Optional[_Iterable[_Union[Conversation, _Mapping]]] = ..., err: _Optional[str] = ...) -> None: ...

class DeleteMessageRequest(_message.Message):
    __slots__ = ("conversation_id", "message_id", "user_id")
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    conversation_id: int
    message_id: int
    user_id: int
    def __init__(self, conversation_id: _Optional[int] = ..., message_id: _Optional[int] = ..., user_id: _Optional[int] = ...) -> None: ...

class DeleteMessageResponse(_message.Message):
    __slots__ = ("success", "err")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    err: str
    def __init__(self, success: _Optional[bool] = ..., err: _Optional[str] = ...) -> None: ...

class RecallMessageForSenderReq(_message.Message):
    __slots__ = ("message_id", "conversation_id", "req_id")
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    REQ_ID_FIELD_NUMBER: _ClassVar[int]
    message_id: int
    conversation_id: int
    req_id: int
    def __init__(self, message_id: _Optional[int] = ..., conversation_id: _Optional[int] = ..., req_id: _Optional[int] = ...) -> None: ...

class RecallMessageForSenderResp(_message.Message):
    __slots__ = ("success", "err")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    err: str
    def __init__(self, success: _Optional[bool] = ..., err: _Optional[str] = ...) -> None: ...
