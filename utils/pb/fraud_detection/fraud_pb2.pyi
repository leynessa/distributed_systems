from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class FraudRequest(_message.Message):
    __slots__ = ("orderId",)
    ORDERID_FIELD_NUMBER: _ClassVar[int]
    orderId: str
    def __init__(self, orderId: _Optional[str] = ...) -> None: ...

class FraudResponse(_message.Message):
    __slots__ = ("isFraudulent",)
    ISFRAUDULENT_FIELD_NUMBER: _ClassVar[int]
    isFraudulent: bool
    def __init__(self, isFraudulent: bool = ...) -> None: ...
