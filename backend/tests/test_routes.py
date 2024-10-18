# tests/test_routes.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.auth import create_access_token
from app import models, schemas


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture(scope="module")
def test_user(client):
    user_data = {"username": "testuser", "email": "test@example.com", "password": "testpassword"}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    return response.json()

@pytest.fixture(scope="module")
def test_user_token(test_user):
    return create_access_token(data={"sub": test_user["username"]})

@pytest.fixture(scope="module")
def authorized_client(client, test_user_token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_user_token}"
    }
    return client

def test_create_user(client):
    response = client.post(
        "/users/",
        json={"username": "newuser", "email": "new@example.com", "password": "newpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data

def test_create_user_duplicate_username(client, test_user):
    response = client.post(
        "/users/",
        json={"username": test_user["username"], "email": "another@example.com", "password": "password"}
    )
    assert response.status_code == 400

def test_login_user(client, test_user):
    response = client.post(
        "/token",
        data={"username": test_user["username"], "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_user_wrong_password(client, test_user):
    response = client.post(
        "/token",
        data={"username": test_user["username"], "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_create_board(authorized_client):
    response = authorized_client.post(
        "/boards/",
        json={"title": "Test Board"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Board"
    assert "id" in data

def test_read_boards(authorized_client):
    response = authorized_client.get("/boards/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_read_board(authorized_client):
    # First, create a board
    create_response = authorized_client.post("/boards/", json={"title": "Board to Read"})
    assert create_response.status_code == 200
    board_id = create_response.json()["id"]

    # Now, read the board
    read_response = authorized_client.get(f"/boards/{board_id}")
    assert read_response.status_code == 200
    data = read_response.json()
    assert data["title"] == "Board to Read"
    assert data["id"] == board_id

def test_update_board(authorized_client):
    # First, create a board
    create_response = authorized_client.post("/boards/", json={"title": "Board to Update"})
    assert create_response.status_code == 200
    board_id = create_response.json()["id"]

    # Now, update the board
    update_response = authorized_client.put(
        f"/boards/{board_id}",
        json={"title": "Updated Board Title"}
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == "Updated Board Title"
    assert data["id"] == board_id

def test_delete_board(authorized_client):
    # First, create a board
    create_response = authorized_client.post("/boards/", json={"title": "Board to Delete"})
    assert create_response.status_code == 200
    board_id = create_response.json()["id"]

    # Now, delete the board
    delete_response = authorized_client.delete(f"/boards/{board_id}")
    assert delete_response.status_code == 200

    # Try to read the deleted board
    read_response = authorized_client.get(f"/boards/{board_id}")
    assert read_response.status_code == 404

# Add more tests for Lists and Cards...