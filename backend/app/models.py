# app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from enum import Enum as PyEnum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    boards = relationship("Board", back_populates="owner")
    activities = relationship("Activity", back_populates="user")
    templates = relationship("BoardTemplate", back_populates="creator")

class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="boards")
    lists = relationship("List", back_populates="board", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="board")

class List(Base):
    __tablename__ = "lists"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    board_id = Column(Integer, ForeignKey("boards.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    board = relationship("Board", back_populates="lists")
    cards = relationship("Card", back_populates="list", cascade="all, delete-orphan")

class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    list_id = Column(Integer, ForeignKey("lists.id"))
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    list = relationship("List", back_populates="cards")
    labels = relationship("Label", back_populates="card")
    attachments = relationship("Attachment", back_populates="card")

class ActivityType(str, PyEnum):
    CARD_CREATED = "card_created"
    CARD_MOVED = "card_moved"
    CARD_ARCHIVED = "card_archived"

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String)  
    details = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    board = relationship("Board", back_populates="activities")
    user = relationship("User", back_populates="activities")

class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    color = Column(String)
    card_id = Column(Integer, ForeignKey("cards.id"))

    card = relationship("Card", back_populates="labels")

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    card_id = Column(Integer, ForeignKey("cards.id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    card = relationship("Card", back_populates="attachments")

class BoardTemplate(Base):
    __tablename__ = "board_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", back_populates="templates")
    lists = relationship("ListTemplate", back_populates="board_template")

class ListTemplate(Base):
    __tablename__ = "list_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    board_template_id = Column(Integer, ForeignKey("board_templates.id"))

    board_template = relationship("BoardTemplate", back_populates="lists")