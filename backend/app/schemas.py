from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import List, Optional

class BoardBase(BaseModel):
    title: str

class BoardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)

class BoardUpdate(BoardBase):
    title: Optional[str] = None

class Board(BoardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ListBase(BaseModel):
    title: str
    board_id: int

class ListCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    board_id: int = Field(..., gt=0)

class ListUpdate(BaseModel):
    title: Optional[str] = None
    board_id: Optional[int] = None

class List(ListBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CardBase(BaseModel):
    title: str
    description: Optional[str] = None
    list_id: int

class CardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    list_id: int = Field(..., gt=0)

class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    list_id: Optional[int] = None

class Card(CardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
class CardMove(BaseModel):
    new_list_id: int
            
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None        