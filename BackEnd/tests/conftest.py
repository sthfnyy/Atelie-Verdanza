import os
os.environ["APP_ENV"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main
import app.database
from app.database import Base, User, Product, Order, OrderItem

from app.main import app as fastapi_app

from sqlalchemy import event

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redireciona SessionLocal e criação de tabelas para usar SQLite nos testes
app.main.SessionLocal = TestingSessionLocal
app.main.create_tables = lambda: Base.metadata.create_all(bind=engine)
app.database.SessionLocal = TestingSessionLocal

@pytest.fixture(scope="function")
def db():
    # Cria todas as tabelas no banco SQLite temporário
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        # Remove as tabelas para garantir limpeza entre testes
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.main.get_db = override_get_db
    fastapi_app.dependency_overrides[app.main.get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
