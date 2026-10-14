from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Message(_message.Message):
    __slots__ = ("conversation_id", "bucket", "message_id", "sender_id", "content", "created_at", "edited_at")
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EDITED_AT_FIELD_NUMBER: _ClassVar[int]
    conversation_id: int
    bucket: int
    message_id: int
    sender_id: int
    content: str
    created_at: int
    edited_at: int
    def __init__(self, conversation_id: _Optional[int] = ..., bucket: _Optional[int] = ..., message_id: _Optional[int] = ..., sender_id: _Optional[int] = ..., content: _Optional[str] = ..., created_at: _Optional[int] = ..., edited_at: _Optional[int] = ...) -> None: ...

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

class GetMessageRequest(_message.Message):
    __slots__ = ("conversation_id", "limit", "err")
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    ERR_FIELD_NUMBER: _ClassVar[int]
    conversation_id: int
    limit: int
    err: str
    def __init__(self, conversation_id: _Optional[int] = ..., limit: _Optional[int] = ..., err: _Optional[str] = ...) -> None: ...

class GetMessageResponse(_message.Message):
    __slots__ = ("messages", "next_cursor", "err")
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    ERR_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[Message]
    next_cursor: int
    err: str
    def __init__(self, messages: _Optional[_Iterable[_Union[Message, _Mapping]]] = ..., next_cursor: _Optional[int] = ..., err: _Optional[str] = ...) -> None: ...
