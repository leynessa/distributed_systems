from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreditCard(_message.Message):
    __slots__ = ("number", "expirationDate", "cvv")
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    EXPIRATIONDATE_FIELD_NUMBER: _ClassVar[int]
    CVV_FIELD_NUMBER: _ClassVar[int]
    number: str
    expirationDate: str
    cvv: str
    def __init__(self, number: _Optional[str] = ..., expirationDate: _Optional[str] = ..., cvv: _Optional[str] = ...) -> None: ...

class TransactionRequest(_message.Message):
    __slots__ = ("creditCard",)
    CREDITCARD_FIELD_NUMBER: _ClassVar[int]
    creditCard: CreditCard
    def __init__(self, creditCard: _Optional[_Union[CreditCard, _Mapping]] = ...) -> None: ...

class TransactionResponse(_message.Message):
    __slots__ = ("isValid",)
    ISVALID_FIELD_NUMBER: _ClassVar[int]
    isValid: bool
    def __init__(self, isValid: bool = ...) -> None: ...
