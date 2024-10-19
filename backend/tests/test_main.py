# test_main.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from app.main import app, lifespan
from app.database import Base, get_db
from app.auth import get_current_user
from app import models, schemas

# Create a test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the test database
Base.metadata.create_all(bind=engine)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the get_current_user dependency for testing
async def override_get_current_user():
    return models.User(id=1, username="testuser", email="testuser@example.com")

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

app.state.use_redis = False  # Set a default value for testing
async def override_lifespan(app: FastAPI):
    async with lifespan(app):
        yield

app.router.lifespan_context = override_lifespan

# Then create the TestClient as before
client = TestClient(app)

# Test cases

def test_read_main():
    """
    Test the root endpoint of the API.
    This test checks if the API responds with a 200 status code and the correct message.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_board():
    """
    Test creating a new board.
    This test checks if a board can be created successfully and if the response contains the correct data.
    """
    response = client.post(
        "/boards/",
        json={"title": "Test Board"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Board"
    assert "id" in data

def test_read_boards():
    """
    Test reading all boards.
    This test checks if the API returns a list of boards and if the response has the correct structure.
    """
    response = client.get("/boards/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "title" in data[0]

# Add these test cases after the existing ones

def test_create_list():
    """
    Test creating a new list.
    This test checks if a list can be created successfully and if the response contains the correct data.
    """
    # First, create a board to associate the list with
    board_response = client.post("/boards/", json={"title": "Test Board for List"})
    board_id = board_response.json()["id"]

    list_data = {"title": "Test List", "board_id": board_id}
    response = client.post("/lists/", json=list_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test List"
    assert data["board_id"] == board_id
    assert "id" in data

def test_create_card():
    """
    Test creating a new card.
    This test checks if a card can be created successfully and if the response contains the correct data.
    """
    # First, create a board and a list to associate the card with
    board_response = client.post("/boards/", json={"title": "Test Board for Card"})
    board_id = board_response.json()["id"]
    list_response = client.post("/lists/", json={"title": "Test List for Card", "board_id": board_id})
    list_id = list_response.json()["id"]

    card_data = {"title": "Test Card", "description": "This is a test card", "list_id": list_id}
    response = client.post("/cards/", json=card_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Card"
    assert data["description"] == "This is a test card"
    assert data["list_id"] == list_id
    assert "id" in data

def test_move_card():
    # Create a test user
    user_response = client.post("/users/", json={
        "username": "moveuser",
        "email": "moveuser@example.com",
        "password": "movepassword"
    })
    assert user_response.status_code == 200

    # Login the test user
    login_response = client.post("/token", data={
        "username": "moveuser",
        "password": "movepassword"
    })
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create a board
    board_response = client.post("/boards/", json={"title": "Test Board for Moving Card"}, headers=headers)
    assert board_response.status_code == 200
    board_id = board_response.json()["id"]

    # Create two lists
    list1_response = client.post("/lists/", json={"title": "List 1", "board_id": board_id}, headers=headers)
    list2_response = client.post("/lists/", json={"title": "List 2", "board_id": board_id}, headers=headers)
    list1_id = list1_response.json()["id"]
    list2_id = list2_response.json()["id"]

    # Create a card in the first list
    card_data = {
        "title": "Card to Move",
        "description": "This is a test card",
        "list_id": list1_id
    }
    card_response = client.post("/cards/", json=card_data, headers=headers)
    card_id = card_response.json()["id"]

    # Move the card to the second list
    move_response = client.put(f"/cards/{card_id}/move?new_list_id={list2_id}", headers=headers)
    assert move_response.status_code == 200
    moved_card = move_response.json()
    assert moved_card["list_id"] == list2_id

def test_search():
    # Create a test user
    user_response = client.post("/users/", json={
        "username": "searchuser",
        "email": "searchuser@example.com",
        "password": "searchpassword"
    })
    assert user_response.status_code == 200

    # Login the test user
    login_response = client.post("/token", data={
        "username": "searchuser",
        "password": "searchpassword"
    })
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create test data
    board_response = client.post("/boards/", json={"title": "Search Test Board"}, headers=headers)
    assert board_response.status_code == 200
    board_id = board_response.json()["id"]

    list_response = client.post("/lists/", json={"title": "Search Test List", "board_id": board_id}, headers=headers)
    assert list_response.status_code == 200
    list_id = list_response.json()["id"]

    card_response = client.post("/cards/", json={
        "title": "Search Test Card",
        "description": "This is a searchable card",
        "list_id": list_id
    }, headers=headers)
    assert card_response.status_code == 200

    # Perform a search
    response = client.get("/search?query=Test", headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert any(result["title"] == "Search Test Board" for result in results)
    assert any(result["title"] == "Search Test List" for result in results)
    assert any(result["title"] == "Search Test Card" for result in results)