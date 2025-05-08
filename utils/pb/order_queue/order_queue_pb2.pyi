from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class VectorClock(_message.Message):
    __slots__ = ("clock",)
    class ClockEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    CLOCK_FIELD_NUMBER: _ClassVar[int]
    clock: _containers.ScalarMap[str, int]
    def __init__(self, clock: _Optional[_Mapping[str, int]] = ...) -> None: ...

class Order(_message.Message):
    __slots__ = ("orderId", "userId", "user", "items", "billingAddress", "shippingMethod", "giftWrapping", "totalAmount")
    ORDERID_FIELD_NUMBER: _ClassVar[int]
    USERID_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    BILLINGADDRESS_FIELD_NUMBER: _ClassVar[int]
    SHIPPINGMETHOD_FIELD_NUMBER: _ClassVar[int]
    GIFTWRAPPING_FIELD_NUMBER: _ClassVar[int]
    TOTALAMOUNT_FIELD_NUMBER: _ClassVar[int]
    orderId: str
    userId: str
    user: UserInfo
    items: _containers.RepeatedCompositeFieldContainer[OrderItem]
    billingAddress: BillingAddress
    shippingMethod: str
    giftWrapping: bool
    totalAmount: float
    def __init__(self, orderId: _Optional[str] = ..., userId: _Optional[str] = ..., user: _Optional[_Union[UserInfo, _Mapping]] = ..., items: _Optional[_Iterable[_Union[OrderItem, _Mapping]]] = ..., billingAddress: _Optional[_Union[BillingAddress, _Mapping]] = ..., shippingMethod: _Optional[str] = ..., giftWrapping: bool = ..., totalAmount: _Optional[float] = ...) -> None: ...

class UserInfo(_message.Message):
    __slots__ = ("name", "contact")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONTACT_FIELD_NUMBER: _ClassVar[int]
    name: str
    contact: str
    def __init__(self, name: _Optional[str] = ..., contact: _Optional[str] = ...) -> None: ...

class OrderItem(_message.Message):
    __slots__ = ("name", "quantity")
    NAME_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    name: str
    quantity: int
    def __init__(self, name: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...

class BillingAddress(_message.Message):
    __slots__ = ("street", "city", "state", "zip", "country")
    STREET_FIELD_NUMBER: _ClassVar[int]
    CITY_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ZIP_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    street: str
    city: str
    state: str
    zip: str
    country: str
    def __init__(self, street: _Optional[str] = ..., city: _Optional[str] = ..., state: _Optional[str] = ..., zip: _Optional[str] = ..., country: _Optional[str] = ...) -> None: ...

class EnqueueRequest(_message.Message):
    __slots__ = ("order", "vectorClock")
    ORDER_FIELD_NUMBER: _ClassVar[int]
    VECTORCLOCK_FIELD_NUMBER: _ClassVar[int]
    order: Order
    vectorClock: VectorClock
    def __init__(self, order: _Optional[_Union[Order, _Mapping]] = ..., vectorClock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...

class EnqueueResponse(_message.Message):
    __slots__ = ("success", "message", "queuePosition", "vectorClock")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    QUEUEPOSITION_FIELD_NUMBER: _ClassVar[int]
    VECTORCLOCK_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    queuePosition: int
    vectorClock: VectorClock
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., queuePosition: _Optional[int] = ..., vectorClock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...

class DequeueRequest(_message.Message):
    __slots__ = ("executorId", "vectorClock")
    EXECUTORID_FIELD_NUMBER: _ClassVar[int]
    VECTORCLOCK_FIELD_NUMBER: _ClassVar[int]
    executorId: str
    vectorClock: VectorClock
    def __init__(self, executorId: _Optional[str] = ..., vectorClock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...

class DequeueResponse(_message.Message):
    __slots__ = ("success", "message", "order", "vectorClock")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    VECTORCLOCK_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    order: Order
    vectorClock: VectorClock
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., order: _Optional[_Union[Order, _Mapping]] = ..., vectorClock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...

class QueueStatusRequest(_message.Message):
    __slots__ = ("vectorClock",)
    VECTORCLOCK_FIELD_NUMBER: _ClassVar[int]
    vectorClock: VectorClock
    def __init__(self, vectorClock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...

class QueueStatusResponse(_message.Message):
    __slots__ = ("queueSize", "orderIds", "vectorClock")
    QUEUESIZE_FIELD_NUMBER: _ClassVar[int]
    ORDERIDS_FIELD_NUMBER: _ClassVar[int]
    VECTORCLOCK_FIELD_NUMBER: _ClassVar[int]
    queueSize: int
    orderIds: _containers.RepeatedScalarFieldContainer[str]
    vectorClock: VectorClock
    def __init__(self, queueSize: _Optional[int] = ..., orderIds: _Optional[_Iterable[str]] = ..., vectorClock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...
