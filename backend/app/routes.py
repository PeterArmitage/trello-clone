
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db

router = APIRouter()

@router.post("/boards/", response_model=schemas.Board)
def create_board(board: schemas.BoardCreate, db: Session = Depends(get_db)):
    db_board = models.Board(title=board.title)
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    return db_board

@router.get("/boards/", response_model=list[schemas.Board])
def read_boards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    boards = db.query(models.Board).offset(skip).limit(limit).all()
    return boards

@router.get("/boards/{board_id}", response_model=schemas.Board)
def read_board(board_id: int, db: Session = Depends(get_db)):
    db_board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if db_board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return db_board

@router.put("/boards/{board_id}", response_model=schemas.Board)
def update_board(board_id: int, board: schemas.BoardUpdate, db: Session = Depends(get_db)):
    db_board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if db_board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    for var, value in vars(board).items():
        setattr(db_board, var, value) if value else None
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    return db_board

@router.delete("/boards/{board_id}", response_model=schemas.Board)
def delete_board(board_id: int, db: Session = Depends(get_db)):
    db_board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if db_board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    db.delete(db_board)
    db.commit()
    return db_board

@router.get("/boards/{board_id}/lists", response_model=list[schemas.List])
def read_lists_for_board(board_id: int, db: Session = Depends(get_db)):
    lists = db.query(models.List).filter(models.List.board_id == board_id).all()
    return lists

# List routes
@router.post("/lists/", response_model=schemas.List)
def create_list(list: schemas.ListCreate, db: Session = Depends(get_db)):
    db_list = models.List(**list.dict())
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    return db_list

@router.get("/lists/", response_model=list[schemas.List])
def read_lists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    lists = db.query(models.List).offset(skip).limit(limit).all()
    return lists

@router.get("/lists/{list_id}", response_model=schemas.List)
def read_list(list_id: int, db: Session = Depends(get_db)):
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="List not found")
    return db_list

@router.put("/lists/{list_id}", response_model=schemas.List)
def update_list(list_id: int, list: schemas.ListUpdate, db: Session = Depends(get_db)):
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="List not found")
    for var, value in vars(list).items():
        setattr(db_list, var, value) if value is not None else None
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    return db_list

@router.delete("/lists/{list_id}", response_model=schemas.List)
def delete_list(list_id: int, db: Session = Depends(get_db)):
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="List not found")
    db.delete(db_list)
    db.commit()
    return db_list

@router.get("/lists/{list_id}/cards", response_model=list[schemas.Card])
def read_cards_for_list(list_id: int, db: Session = Depends(get_db)):
    cards = db.query(models.Card).filter(models.Card.list_id == list_id).all()
    return cards

# Card routes
@router.post("/cards/", response_model=schemas.Card)
def create_card(card: schemas.CardCreate, db: Session = Depends(get_db)):
    db_card = models.Card(**card.dict())
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

@router.get("/cards/", response_model=list[schemas.Card])
def read_cards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cards = db.query(models.Card).offset(skip).limit(limit).all()
    return cards

@router.get("/cards/{card_id}", response_model=schemas.Card)
def read_card(card_id: int, db: Session = Depends(get_db)):
    db_card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return db_card

@router.put("/cards/{card_id}", response_model=schemas.Card)
def update_card(card_id: int, card: schemas.CardUpdate, db: Session = Depends(get_db)):
    db_card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    for var, value in vars(card).items():
        setattr(db_card, var, value) if value is not None else None
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

@router.delete("/cards/{card_id}", response_model=schemas.Card)
def delete_card(card_id: int, db: Session = Depends(get_db)):
    db_card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(db_card)
    db.commit()
    return db_card