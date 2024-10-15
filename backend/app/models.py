# app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lists = relationship("List", back_populates="board", cascade="all, delete-orphan")

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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    list = relationship("List", back_populates="cards")