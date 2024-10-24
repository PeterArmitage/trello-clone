# test_main.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI, Depends, HTTPException
from app.main import app, lifespan
from app.database import Base, get_db
from app.auth import create_access_token
from app import models, auth
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_user(test_db):
    user = models.User(username="testuser", email="testuser@example.com", hashed_password="testpassword")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_token(test_user):
    return create_access_token(data={"sub": test_user.username})

@pytest.fixture(scope="function")
def authorized_client(test_token):
    client = TestClient(app)
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_token}"
    }
    return client

@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

async def override_get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401)
        return user
    except JWTError:
        raise HTTPException(status_code=401)

app.dependency_overrides[auth.get_current_user] = override_get_current_user

app.state.use_redis = False

async def override_lifespan(app: FastAPI):
    async with lifespan(app):
        yield

app.router.lifespan_context = override_lifespan

client = TestClient(app)

def create_test_user(username, email, password):
    user_data = {"username": username, "email": email, "password": password}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    user = response.json()
    user['password'] = password  
    return user

def create_test_board(user_or_client, title):
    if isinstance(user_or_client, dict):
        # It's a user object
        headers = get_auth_header(user_or_client)
        response = client.post("/boards/", json={"title": title}, headers=headers)
    else:
        # It's an authorized client
        response = user_or_client.post("/boards/", json={"title": title})
    
    assert response.status_code == 200, f"Failed to create board: {response.text}"
    return response.json()

def create_test_list(board_id, title, authorized_client):
    response = authorized_client.post("/lists/", json={"title": title, "board_id": board_id})
    assert response.status_code == 200
    return response.json()

def create_test_card(list_id, title, authorized_client):
    response = authorized_client.post("/cards/", json={"title": title, "list_id": list_id, "description": "Test card"})
    assert response.status_code == 200, f"Failed to create card: {response.text}"
    return response.json()

def get_auth_header(user):
    response = client.post("/token", data={"username": user["username"], "password": user["password"]})
    assert response.status_code == 200, f"Failed to get token: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_board(authorized_client, test_db):
    response = authorized_client.post(
        "/boards/",
        json={"title": "Test Board"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Board"
    assert "id" in data

def test_read_boards(authorized_client, test_db):
    response = authorized_client.get("/boards/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "title" in data[0]

def test_create_list(authorized_client, test_db):
    board_response = authorized_client.post("/boards/", json={"title": "Test Board for List"})
    board_id = board_response.json()["id"]

    list_data = {"title": "Test List", "board_id": board_id}
    response = authorized_client.post("/lists/", json=list_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test List"
    assert data["board_id"] == board_id
    assert "id" in data

def test_create_card(authorized_client, test_db):
    board_response = authorized_client.post("/boards/", json={"title": "Test Board for Card"})
    board_id = board_response.json()["id"]
    list_response = authorized_client.post("/lists/", json={"title": "Test List for Card", "board_id": board_id})
    list_id = list_response.json()["id"]

    card_data = {"title": "Test Card", "description": "This is a test card", "list_id": list_id}
    response = authorized_client.post("/cards/", json=card_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Card"
    assert data["description"] == "This is a test card"
    assert data["list_id"] == list_id
    assert "id" in data

def test_move_card(authorized_client, test_db):
    user = create_test_user("moveuser", "moveuser@example.com", "movepassword")
    board = create_test_board(user, "Test Board for Moving Card")
    list1 = create_test_list(board["id"], "List 1", authorized_client)
    list2 = create_test_list(board["id"], "List 2", authorized_client)
    card = create_test_card(list1["id"], "Card to Move", authorized_client)

    headers = get_auth_header(user)
    move_response = authorized_client.put(f"/cards/{card['id']}/move?new_list_id={list2['id']}", headers=headers)
    assert move_response.status_code == 200
    moved_card = move_response.json()
    assert moved_card["list_id"] == list2["id"]

def test_search(authorized_client, test_db):
    user = create_test_user("searchuser", "searchuser@example.com", "searchpassword")
    board = create_test_board(user, "Search Test Board")
    list = create_test_list(board["id"], "Search Test List", authorized_client)
    card = create_test_card(list["id"], "Search Test Card", authorized_client)

    headers = get_auth_header(user)
    response = authorized_client.get("/search?query=Test", headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert any(result["title"] == "Search Test Board" for result in results)
    assert any(result["title"] == "Search Test List" for result in results)
    assert any(result["title"] == "Search Test Card" for result in results)

def test_board_permissions(authorized_client, test_db):
    user1 = create_test_user("user1", "user1@example.com", "password1")
    user2 = create_test_user("user2", "user2@example.com", "password2")
    board = create_test_board(user1, "Test Board")

    print(f"User1: {user1}")
    print(f"User2: {user2}")
    print(f"Board: {board}")

    # User1 (owner) should be able to update the board
    response = authorized_client.put(
        f"/boards/{board['id']}",
        json={"title": "Updated Board by Owner"},
        headers=get_auth_header(user1)
    )
    assert response.status_code == 200

    # Add user2 as a member with view permission
    response = authorized_client.post(
        f"/boards/{board['id']}/members",
        json={"user_id": user2['id'], "permission_level": "view"},
        headers=get_auth_header(user1)
    )
    assert response.status_code == 200
    print(f"Add member response: {response.json()}")

    # Verify that user2 was actually added with VIEW permission
    member = test_db.query(models.BoardMember).filter(
        models.BoardMember.board_id == board['id'],
        models.BoardMember.user_id == user2['id']
    ).first()
    assert member is not None, "Board member not found"
    assert member.permission_level == models.PermissionLevel.VIEW, f"Expected VIEW permission, got {member.permission_level}"

    # User2 (view permission) should not be able to update the board
    response = authorized_client.put(
        f"/boards/{board['id']}",
        json={"title": "Updated Board by Viewer"},
        headers=get_auth_header(user2)
    )
    print(f"Update board response: {response.json()}")
    assert response.status_code == 403, f"Expected 403, got {response.status_code}. Response: {response.text}"

def test_board_activity(authorized_client, test_db):
    board = create_test_board(authorized_client, "Activity Board")
    list = create_test_list(board['id'], "List 1", authorized_client)
    create_test_card(list['id'], "Card 1", authorized_client)

    response = authorized_client.get(f"/boards/{board['id']}/activity")
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) > 0

def test_board_statistics(authorized_client, test_db):
    user = create_test_user("statsuser", "stats@example.com", "password")
    board = create_test_board(user, "Stats Board")
    list1 = create_test_list(board['id'], "List 1", authorized_client)
    list2 = create_test_list(board['id'], "List 2", authorized_client)
    create_test_card(list1['id'], "Card 1", authorized_client)
    create_test_card(list1['id'], "Card 2", authorized_client)
    create_test_card(list2['id'], "Card 3", authorized_client)

    response = authorized_client.get(f"/boards/{board['id']}/statistics", headers=get_auth_header(user))
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_lists"] == 2
    assert stats["total_cards"] == 3

def test_board_cards(authorized_client, test_db):
    user = create_test_user("cardsuser", "cards@example.com", "password")
    board = create_test_board(user, "Cards Board")
    list1 = create_test_list(board['id'], "List 1", authorized_client)
    list2 = create_test_list(board['id'], "List 2", authorized_client)
    create_test_card(list1['id'], "Card 1", authorized_client)
    create_test_card(list1['id'], "Card 2", authorized_client)
    create_test_card(list2['id'], "Card 3", authorized_client)

    response = authorized_client.get(f"/boards/{board['id']}/cards", headers=get_auth_header(user))
    assert response.status_code == 200
    cards = response.json()
    assert len(cards) == 3
    assert any(card["title"] == "Card 1" for card in cards)
    assert any(card["title"] == "Card 2" for card in cards)
    assert any(card["title"] == "Card 3" for card in cards)

def test_create_board_invalid_data(authorized_client):
    response = authorized_client.post(
        "/boards/",
        json={"title": ""}  # Invalid empty title
    )
    assert response.status_code == 422  # Unprocessable Entity

def test_read_non_existent_board(authorized_client):
    response = authorized_client.get("/boards/999999")  # Non-existent board ID
    assert response.status_code == 404

def test_update_board(authorized_client, test_db):
    create_response = authorized_client.post(
        "/boards/",
        json={"title": "Original Title"}
    )
    assert create_response.status_code == 200
    board_id = create_response.json()["id"]

    update_response = authorized_client.put(
        f"/boards/{board_id}",
        json={"title": "Updated Title"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated Title"

def test_delete_board(authorized_client, test_db):
    create_response = authorized_client.post(
        "/boards/",
        json={"title": "Board to Delete"}
    )
    assert create_response.status_code == 200
    board_id = create_response.json()["id"]

    delete_response = authorized_client.delete(f"/boards/{board_id}")
    assert delete_response.status_code == 200

    get_response = authorized_client.get(f"/boards/{board_id}")
    assert get_response.status_code == 404

