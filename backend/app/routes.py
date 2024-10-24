from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import shutil
import os
from . import models, schemas, auth
from .database import get_db
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import func, desc, or_, asc, and_
from .exceptions import NotFoundException, ForbiddenException, BadRequestException
from .models import PermissionLevel
import logging

logger = logging.getLogger(__name__)
UPLOAD_DIR = "uploads"
# Create an APIRouter instance
router = APIRouter()

# Board routes

# Create a new board
@router.post("/boards/", response_model=schemas.Board)
def create_board(board: schemas.BoardCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_board = models.Board(**board.model_dump(), owner_id=current_user.id)
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    return db_board

# Get all boards with pagination
@router.get("/boards/", response_model=list[schemas.Board])
def read_boards(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    boards = db.query(models.Board).offset(skip).limit(limit).all()
    return boards

# Get a specific board by ID

@router.get("/boards/{board_id}", response_model=schemas.Board)
def read_board(board_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    
    print(f"Board owner_id: {board.owner_id}, Current user id: {current_user.id}")  # Debug print
    
    if board.owner_id != current_user.id:
        member = db.query(models.BoardMember).filter(
            models.BoardMember.board_id == board_id,
            models.BoardMember.user_id == current_user.id
        ).first()
        if not member:
            print(f"User {current_user.id} not authorized to access board {board_id}")  # Debug print
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this board")
    
    return board

# Update a board
@router.put("/boards/{board_id}", response_model=schemas.Board)
def update_board(
    board_id: int, 
    board: schemas.BoardUpdate, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Updating board {board_id} for user {current_user.username} (id: {current_user.id})")
    
    db_board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if db_board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    
    logger.info(f"Board owner_id: {db_board.owner_id}, Current user id: {current_user.id}")
    
    if db_board.owner_id != current_user.id:
        member = db.query(models.BoardMember).filter(
            models.BoardMember.board_id == board_id,
            models.BoardMember.user_id == current_user.id
        ).first()
        
        logger.info(f"Board member found: {member}")
        if member:
            logger.info(f"Member permission level: {member.permission_level}")
            
        if not member or member.permission_level == PermissionLevel.VIEW:
            logger.warning(f"User {current_user.id} not authorized to update board {board_id}")
            raise ForbiddenException(detail="Not authorized to update this board")
    
    for var, value in vars(board).items():
        setattr(db_board, var, value) if value else None
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    logger.info(f"Board {board_id} updated successfully")
    return db_board

@router.get("/boards/{board_id}/members", response_model=List[schemas.BoardMember])
def get_board_members(
    board_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
        
    if board.owner_id != current_user.id:
        member = db.query(models.BoardMember).filter(
            models.BoardMember.board_id == board_id,
            models.BoardMember.user_id == current_user.id
        ).first()
        if not member:
            raise ForbiddenException(detail="Not authorized to view this board's members")
            
    members = db.query(models.BoardMember).filter(models.BoardMember.board_id == board_id).all()
    return members

# Delete a board
@router.delete("/boards/{board_id}", response_model=schemas.Board)
def delete_board(
    board_id: int, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if db_board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if db_board.owner_id != current_user.id:
        raise ForbiddenException(detail="Not authorized to delete this board")
    
    db.delete(db_board)
    db.commit()
    return db_board

# Get all lists for a specific board
@router.get("/boards/{board_id}/lists", response_model=list[schemas.List])
def read_lists_for_board(
    board_id: int, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if board.owner_id != current_user.id:
        member = db.query(models.BoardMember).filter(
            models.BoardMember.board_id == board_id,
            models.BoardMember.user_id == current_user.id
        ).first()
        if not member:
            raise ForbiddenException(detail="Not authorized to access this board")
    
    lists = db.query(models.List).filter(models.List.board_id == board_id).all()
    return lists

# Get board activity
@router.get("/boards/{board_id}/activity", response_model=List[schemas.Activity])
async def get_board_activity(
    board_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if board.owner_id != current_user.id:
        member = db.query(models.BoardMember).filter(
            models.BoardMember.board_id == board_id,
            models.BoardMember.user_id == current_user.id
        ).first()
        if not member:
            raise ForbiddenException(detail="Not authorized to access this board")
    
    activities = db.query(models.Activity).filter(models.Activity.board_id == board_id).order_by(models.Activity.created_at.desc()).limit(50).all()
    return activities

# Get board statistics
@router.get("/boards/{board_id}/statistics", response_model=schemas.BoardStatistics)
async def get_board_statistics(
    board_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    
    if board.owner_id != current_user.id:
        member = db.query(models.BoardMember).filter(
            models.BoardMember.board_id == board_id,
            models.BoardMember.user_id == current_user.id
        ).first()
        if not member:
            raise ForbiddenException(detail="Not authorized to access this board")
    
    list_stats = db.query(
        models.List.title,
        func.count(models.Card.id).label('card_count')
    ).outerjoin(models.Card).filter(models.List.board_id == board_id).group_by(models.List.id).all()
    
    total_cards = sum(stat.card_count for stat in list_stats)
    
    return schemas.BoardStatistics(
        total_lists=len(list_stats),
        total_cards=total_cards,
        lists_statistics=[schemas.ListStatistics(name=stat.title, card_count=stat.card_count) for stat in list_stats]
    )
@router.get("/boards/{board_id}/cards", response_model=List[schemas.Card])
async def get_board_cards(
    board_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise NotFoundException(detail="Board not found")
    
    if board.owner_id != current_user.id:
        member = db.query(models.BoardMember).filter(
            models.BoardMember.board_id == board_id,
            models.BoardMember.user_id == current_user.id
        ).first()
        if not member:
            raise ForbiddenException(detail="Not authorized to access this board")
    
    cards = db.query(models.Card).join(models.List).filter(models.List.board_id == board_id).all()
    return cards

# Get all cards for a specific board
@router.get("/boards/{board_id}", response_model=schemas.Board)
def read_board(board_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if board is None:
        raise NotFoundException(detail="Board not found")
    
    if board.owner_id != current_user.id:
        member = db.query(models.BoardMember).filter(
            models.BoardMember.board_id == board_id,
            models.BoardMember.user_id == current_user.id
        ).first()
        if not member:
            raise ForbiddenException(detail="Not authorized to access this board")
    
    return board

@router.post("/board-templates", response_model=schemas.BoardTemplate)
async def create_board_template(
    template: schemas.BoardTemplateCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_template = models.BoardTemplate(**template.model_dump(), created_by=current_user.id)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.post("/boards/from-template/{template_id}", response_model=schemas.Board)
async def create_board_from_template(
    template_id: int,
    board_name: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    template = db.query(models.BoardTemplate).filter(models.BoardTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    new_board = models.Board(title=board_name, owner_id=current_user.id)
    db.add(new_board)
    db.flush()

    for list_template in template.lists:
        new_list = models.List(title=list_template.name, board_id=new_board.id)
        db.add(new_list)

    db.commit()
    db.refresh(new_board)
    return new_board

@router.post("/boards/{board_id}/members", response_model=schemas.BoardMember)
def add_board_member(
    board_id: int,
    member: schemas.BoardMemberCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    board = db.query(models.Board).filter(models.Board.id == board_id, models.Board.owner_id == current_user.id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found or you don't have permission")
    
    new_member = models.BoardMember(**member.model_dump(), board_id=board_id)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

@router.put("/boards/{board_id}/members/{user_id}", response_model=schemas.BoardMember)
def update_board_member_permission(
    board_id: int,
    user_id: int,
    permission: PermissionLevel,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    board = db.query(models.Board).filter(models.Board.id == board_id, models.Board.owner_id == current_user.id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found or you don't have permission")
    
    member = db.query(models.BoardMember).filter(models.BoardMember.board_id == board_id, models.BoardMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Board member not found")
    
    member.permission_level = permission
    db.commit()
    db.refresh(member)
    return member

@router.delete("/boards/{board_id}/members/{user_id}", status_code=204)
def remove_board_member(
    board_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    board = db.query(models.Board).filter(models.Board.id == board_id, models.Board.owner_id == current_user.id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found or you don't have permission")
    
    member = db.query(models.BoardMember).filter(models.BoardMember.board_id == board_id, models.BoardMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Board member not found")
    
    db.delete(member)
    db.commit()
    return {"detail": "Board member removed successfully"}
   
# List routes
# Create a new list
@router.post("/lists/", response_model=schemas.List)
def create_list(list: schemas.ListCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_list = models.List(**list.model_dump())
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    
    # Log activity
    activity = models.Activity(
        board_id=db_list.board_id,
        user_id=current_user.id,
        activity_type="list_created",
        details=f"List '{db_list.title}' created"
    )
    db.add(activity)
    db.commit()
    
    return db_list

# Get all lists with pagination
@router.get("/lists/", response_model=list[schemas.List])
def read_lists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Query the database for lists, applying offset and limit for pagination
    lists = db.query(models.List).offset(skip).limit(limit).all()
    # Return the retrieved lists
    return lists

# Get a specific list by ID
@router.get("/lists/{list_id}", response_model=schemas.List)
def read_list(list_id: int, db: Session = Depends(get_db)):
    # Query the database for a list with the given ID
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    # If the list is not found, raise a 404 error
    if db_list is None:
        raise HTTPException(status_code=404, detail="List not found")
    # Return the found list
    return db_list

# Update a specific list
@router.put("/lists/{list_id}", response_model=schemas.List)
def update_list(list_id: int, list: schemas.ListUpdate, db: Session = Depends(get_db)):
    # Query the database for a list with the given ID
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    # If the list is not found, raise a 404 error
    if db_list is None:
        raise HTTPException(status_code=404, detail="List not found")
    # Update the list attributes with the provided values, if they are not None
    for var, value in vars(list).items():
        setattr(db_list, var, value) if value is not None else None
    # Add the updated list to the database
    db.add(db_list)
    # Commit the changes to the database
    db.commit()
    # Refresh the list object to ensure it reflects the current state in the database
    db.refresh(db_list)
    # Return the updated list
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
def read_cards_for_list(
    list_id: int,
    due_date: Optional[datetime] = None,
    sort_by: Optional[str] = Query(None, enum=["created_at", "due_date"]),
    sort_order: Optional[str] = Query("asc", enum=["asc", "desc"]),
    db: Session = Depends(get_db)
):
    query = db.query(models.Card).filter(models.Card.list_id == list_id)

    if due_date:
        query = query.filter(models.Card.due_date <= due_date)

    if sort_by:
        order = desc if sort_order == "desc" else asc
        query = query.order_by(order(getattr(models.Card, sort_by)))

    cards = query.all()
    return cards

# Card routes
@router.post("/cards/", response_model=schemas.Card)
def create_card(card: schemas.CardCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    list = db.query(models.List).filter(models.List.id == card.list_id).first()
    if not list:
        raise HTTPException(status_code=404, detail="List not found")
    
    db_card = models.Card(**card.model_dump())
    db.add(db_card)
    db.commit()
    db.refresh(db_card)

    # Log activity
    activity = models.Activity(
        board_id=list.board_id,
        user_id=current_user.id,
        activity_type="card_created",
        details=f"Card '{db_card.title}' created in list '{list.title}'"
    )
    db.add(activity)
    db.commit()

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
    print(f"Moving card {card_id} to list {new_list_id} for user {current_user.id}")
    card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if not card:
        print(f"Card {card_id} not found")
        raise HTTPException(status_code=404, detail="Card not found")

    # Check if the user has permission to move this card
    board = db.query(models.Board).join(models.List).filter(models.List.id == card.list_id).first()
    print(f"Board owner_id: {board.owner_id}, Current user id: {current_user.id}")
    if not board or board.owner_id != current_user.id:
        print(f"User {current_user.id} not authorized to move card {card_id}")
        raise HTTPException(status_code=403, detail="Not authorized to move this card")

    # Check if the new list exists and belongs to the same board
    new_list = db.query(models.List).filter(models.List.id == new_list_id, models.List.board_id == board.id).first()
    if not new_list:
        raise HTTPException(status_code=400, detail="Invalid new list ID")

    # Move the card
    card.list_id = new_list_id
    db.commit()
    db.refresh(card)

    return card

@router.post("/cards/{card_id}/labels", response_model=schemas.Card)
def add_label_to_card(
    card_id: int, 
    label: schemas.LabelCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    card = db.query(models.Card).join(models.List).join(models.Board).filter(
        models.Card.id == card_id,
        models.Board.owner_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    new_label = models.Label(**label.model_dump(), card_id=card_id)
    db.add(new_label)
    db.commit()
    db.refresh(card)
    return card

@router.delete("/cards/{card_id}/labels/{label_id}", response_model=schemas.Card)
def remove_label_from_card(
    card_id: int, 
    label_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    card = db.query(models.Card).join(models.List).join(models.Board).filter(
        models.Card.id == card_id,
        models.Board.owner_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    label = db.query(models.Label).filter(models.Label.id == label_id, models.Label.card_id == card_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    db.delete(label)
    db.commit()
    db.refresh(card)
    return card

@router.post("/cards/batch", response_model=List[schemas.Card])
def create_cards_batch(
    cards: List[schemas.CardCreate],
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    created_cards = []
    for card_data in cards:
        # Verify that the user has access to the list
        list_obj = db.query(models.List).join(models.Board).filter(
            models.List.id == card_data.list_id,
            models.Board.owner_id == current_user.id
        ).first()
        if not list_obj:
            raise HTTPException(status_code=404, detail="List not found or access denied")
        
        db_card = models.Card(**card_data.model_dump())
        db.add(db_card)
        created_cards.append(db_card)
    
    db.commit()
    for card in created_cards:
        db.refresh(card)
    
    return created_cards

@router.post("/cards/{card_id}/attachments", response_model=schemas.Attachment)
async def add_attachment(
    card_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(models.Card).join(models.List).join(models.Board).filter(
        models.Card.id == card_id,
        models.Board.owner_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found or access denied")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_attachment = models.Attachment(filename=file.filename, file_path=file_path, card_id=card.id)
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)

    return db_attachment

@router.get("/cards/{card_id}/attachments", response_model=List[schemas.Attachment])
async def get_attachments(
    card_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(models.Card).join(models.List).join(models.Board).filter(
        models.Card.id == card_id,
        models.Board.owner_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found or access denied")

    return card.attachments

@router.post("/cards/{card_id}/comments", response_model=schemas.Comment)
def add_comment_to_card(
    card_id: int,
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    card = db.query(models.Card).join(models.List).join(models.Board).filter(
        models.Card.id == card_id,
        models.Board.owner_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    new_comment = models.Comment(**comment.model_dump(), card_id=card_id, user_id=current_user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

@router.get("/cards/{card_id}/comments", response_model=List[schemas.Comment])
def get_card_comments(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    card = db.query(models.Card).join(models.List).join(models.Board).filter(
        models.Card.id == card_id,
        models.Board.owner_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return card.comments

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


#search
@router.get("/search", response_model=List[schemas.SearchResult])
async def search(
    query: str,
    due_date_start: Optional[datetime] = None,
    due_date_end: Optional[datetime] = None,
    label: Optional[str] = None,
    board_id: Optional[int] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Base query for boards
    board_query = db.query(models.Board).filter(models.Board.owner_id == current_user.id)
    
    # Apply board_id filter if provided
    if board_id:
        board_query = board_query.filter(models.Board.id == board_id)
    
    # Search in boards
    boards = board_query.filter(models.Board.title.ilike(f"%{query}%")).all()

    # Search in lists
    lists = db.query(models.List).join(models.Board).filter(
        models.Board.owner_id == current_user.id,
        models.List.title.ilike(f"%{query}%")
    ).all()

    # Base query for cards
    card_query = db.query(models.Card).join(models.List).join(models.Board).filter(
        models.Board.owner_id == current_user.id
    )
    
    # Apply filters
    if due_date_start:
        card_query = card_query.filter(models.Card.due_date >= due_date_start)
    if due_date_end:
        card_query = card_query.filter(models.Card.due_date <= due_date_end)
    if label:
        card_query = card_query.join(models.Label).filter(models.Label.name == label)
    if board_id:
        card_query = card_query.filter(models.Board.id == board_id)

    # Full-text search on cards
    cards = card_query.filter(
        or_(
            models.Card.title.ilike(f"%{query}%"),
            models.Card.description.ilike(f"%{query}%")
        )
    ).all()

    results = [
        *[schemas.SearchResult(type="board", id=b.id, title=b.title) for b in boards],
        *[schemas.SearchResult(type="list", id=l.id, title=l.title) for l in lists],
        *[schemas.SearchResult(type="card", id=c.id, title=c.title) for c in cards]
    ]

    return results







