import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Users
from models import Todos
from main import app
from routers.auth import get_current_user
from routers.todos import get_db
from database import Base
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy import text

SQLALCHEMY_DATABASE_URL = 'sqlite:///./test.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user():
    return {"username": "megjones", "id": 1, "user_role": 'admin'}

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.fixture
def default_user():
    return Users(id=1, email="meg@email.com", username='megjones', first_name="Meg", last_name="Jones",
                 hashed_password="<PASSWORD>", is_active=True, phone_number="02837473923")

@pytest.fixture
def test_todo():
    todo = Todos(id=1, title="Default todo", description="Description for todo", priority=3, complete=False, owner_id=1)
    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    yield todo
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos;"))
        connection.commit()

def test_read_all_authenticated(test_todo):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"complete": False, "title": "Default todo", "description": "Description for todo",
                                "id": 1, "priority": 3, "owner_id": 1}]

def test_read_one_authenticated(test_todo):
    response = client.get("/todo/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"complete": False, "title": "Default todo", "description": "Description for todo",
                                "id": 1, "priority": 3, "owner_id": 1}

def test_read_one_authenticated_not_found(test_todo):
    response = client.get("/todo/3")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found."}


def test_create_todo(test_todo):
    request_data = {
        "title": "New todo",
        "description": "New description",
        "priority": 3,
        "complete": False,
    }
    response = client.post("/todo/", json=request_data)
    assert response.status_code == status.HTTP_201_CREATED

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 2).first()
    assert model.title == request_data.get("title")
    assert model.description == request_data.get("description")
    assert model.priority == request_data.get("priority")
    assert model.complete == request_data.get("complete")


def test_update_todo(test_todo):
    request_data = {
        "title": "changed todo",
        "description": "changed description",
        "priority": 4,
        "complete": True,
    }
    response = client.put("/todo/1", json=request_data)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()

    assert model.title == request_data.get("title")
    assert model.description == request_data.get("description")
    assert model.priority == request_data.get("priority")
    assert model.complete == request_data.get("complete")

def test_update_not_found_todo(test_todo):
    request_data = {
        "title": "changed todo",
        "description": "changed description",
        "priority": 4,
        "complete": True,
    }
    response = client.put("/todo/3", json=request_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found."}


def test_delete_todo(test_todo):
    response = client.delete("/todo/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()
    assert model is None

def test_delete_todo_not_found():
    response = client.delete("/todo/3")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found."}
