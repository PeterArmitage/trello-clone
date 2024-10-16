
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas, auth
from .database import get_db
from datetime import timedelta
from typing import List

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

@router.put("/cards/{card_id}/move", response_model=schemas.Card)
async def move_card(
    card_id: int,
    new_list_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    
 # First, get the card
    card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Check if the user has permission to move this card
    # (You might want to implement a more sophisticated permission system)
    board = db.query(models.Board).join(models.List).filter(models.List.id == card.list_id).first()
    if board.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to move this card")

    # Check if the new list exists and belongs to the same board
    new_list = db.query(models.List).filter(models.List.id == new_list_id).first()
    if not new_list or new_list.board_id != board.id:
        raise HTTPException(status_code=400, detail="Invalid new list ID")

    # Move the card
    card.list_id = new_list_id
    db.commit()
    db.refresh(card)

    return card
#users

@router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.get("/users/me/boards", response_model=List[schemas.Board])
async def read_user_boards(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    boards = db.query(models.Board).filter(models.Board.owner_id == current_user.id).all()
    return boards

#token

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


