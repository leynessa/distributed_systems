from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Order(_message.Message):
    __slots__ = ("orderId", "userName", "bookTitle", "quantity")
    ORDERID_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    BOOKTITLE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    orderId: str
    userName: str
    bookTitle: str
    quantity: int
    def __init__(self, orderId: _Optional[str] = ..., userName: _Optional[str] = ..., bookTitle: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...

class AnnounceRequest(_message.Message):
    __slots__ = ("executor_id",)
    EXECUTOR_ID_FIELD_NUMBER: _ClassVar[int]
    executor_id: int
    def __init__(self, executor_id: _Optional[int] = ...) -> None: ...

class DequeueRequest(_message.Message):
    __slots__ = ("request_data", "order")
    REQUEST_DATA_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    request_data: str
    order: Order
    def __init__(self, request_data: _Optional[str] = ..., order: _Optional[_Union[Order, _Mapping]] = ...) -> None: ...

class DequeueResponse(_message.Message):
    __slots__ = ("message", "executed_by_leader", "order_received")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    EXECUTED_BY_LEADER_FIELD_NUMBER: _ClassVar[int]
    ORDER_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    message: str
    executed_by_leader: bool
    order_received: bool
    def __init__(self, message: _Optional[str] = ..., executed_by_leader: bool = ..., order_received: bool = ...) -> None: ...

class CoordinatorMessage(_message.Message):
    __slots__ = ("leader_id",)
    LEADER_ID_FIELD_NUMBER: _ClassVar[int]
    leader_id: int
    def __init__(self, leader_id: _Optional[int] = ...) -> None: ...

class CoordinatorResponse(_message.Message):
    __slots__ = ("acknowledged",)
    ACKNOWLEDGED_FIELD_NUMBER: _ClassVar[int]
    acknowledged: bool
    def __init__(self, acknowledged: bool = ...) -> None: ...

class Are_You_AvailableRequest(_message.Message):
    __slots__ = ("leader_id", "request_to_id")
    LEADER_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_TO_ID_FIELD_NUMBER: _ClassVar[int]
    leader_id: str
    request_to_id: str
    def __init__(self, leader_id: _Optional[str] = ..., request_to_id: _Optional[str] = ...) -> None: ...

class Are_You_AvailableResponse(_message.Message):
    __slots__ = ("executor_id", "leader_id", "available")
    EXECUTOR_ID_FIELD_NUMBER: _ClassVar[int]
    LEADER_ID_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    executor_id: str
    leader_id: str
    available: bool
    def __init__(self, executor_id: _Optional[str] = ..., leader_id: _Optional[str] = ..., available: bool = ...) -> None: ...

class ElectionRequest(_message.Message):
    __slots__ = ("candidate_id",)
    CANDIDATE_ID_FIELD_NUMBER: _ClassVar[int]
    candidate_id: int
    def __init__(self, candidate_id: _Optional[int] = ...) -> None: ...

class ElectionResponse(_message.Message):
    __slots__ = ("acknowledged",)
    ACKNOWLEDGED_FIELD_NUMBER: _ClassVar[int]
    acknowledged: bool
    def __init__(self, acknowledged: bool = ...) -> None: ...
