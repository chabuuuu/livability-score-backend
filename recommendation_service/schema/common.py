from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class ResponseData(BaseModel, Generic[T]):
    items: List[T]

class APIResponse(BaseModel, Generic[T]):
    status: str
    result: str
    error: Optional[str] = None
    data: Optional[ResponseData[T]] = None