import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Todos
from models import Users
from routers.auth import bcrypt_context
from main import app
from database import Base
from fastapi.testclient import TestClient
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

client = TestClient(app)

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


@pytest.fixture
def test_user():
    user = Users(id=1, username="megjones", email="megjones@email", first_name="Meg", last_name="Jones", hashed_password=bcrypt_context.hash("password"), role="admin", phone_number="07947298572")
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM users;"))
        connection.commit()
