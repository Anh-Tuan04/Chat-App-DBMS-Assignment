from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AddMessageRequest(_message.Message):
    __slots__ = ("senderID", "receiverID", "content")
    SENDERID_FIELD_NUMBER: _ClassVar[int]
    RECEIVERID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    senderID: int
    receiverID: int
    content: str
    def __init__(self, senderID: _Optional[int] = ..., receiverID: _Optional[int] = ..., content: _Optional[str] = ...) -> None: ...

class AddMessageRespond(_message.Message):
    __slots__ = ("ok", "err")
    OK_FIELD_NUMBER: _ClassVar[int]
    ERR_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    err: str
    def __init__(self, ok: _Optional[bool] = ..., err: _Optional[str] = ...) -> None: ...
