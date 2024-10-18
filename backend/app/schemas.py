from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import List as PyList, Optional
from enum import Enum
from pydantic.config import ConfigDict

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

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

class CardBase(BaseModel):
    title: str
    description: Optional[str] = None
    list_id: int
    due_date: Optional[datetime] = None

class CardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    list_id: int = Field(..., gt=0)
    due_date: Optional[datetime] = None

class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    list_id: Optional[int] = None
    due_date: Optional[datetime] = None

class Card(CardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
        
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

class ActivityType(str, Enum):
    CARD_CREATED = "card_created"
    CARD_MOVED = "card_moved"
    CARD_ARCHIVED = "card_archived"

class Activity(BaseModel):
    id: int
    board_id: int
    user_id: int
    activity_type: ActivityType
    details: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  
    
class SearchResult(BaseModel):
    type: str
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)
    
class Attachment(BaseModel):
    id: int
    filename: str
    file_path: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BoardTemplateCreate(BaseModel):
    name: str
    description: str
    lists: PyList[str]

class BoardTemplate(BoardTemplateCreate):
    id: int
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)    

class ListStatistics(BaseModel):
    name: str
    card_count: int

class BoardStatistics(BaseModel):
    total_lists: int
    total_cards: int
    lists_statistics: PyList[ListStatistics]

    model_config = ConfigDict(from_attributes=True)    
    
class LabelCreate(BaseModel):
    name: str
    color: str

class Label(LabelCreate):
    id: int
    card_id: int

    model_config = ConfigDict(from_attributes=True)   
    
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)     