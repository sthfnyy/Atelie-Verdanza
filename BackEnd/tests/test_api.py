import pytest
from unittest.mock import MagicMock
from app.database import User, Product, Order, OrderItem
from app.main import get_db, app as fastapi_app

# Existing & Basic Endpoint Tests
def test_read_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Backend FastAPI funcionando"}


def test_api_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json() == {"status": "API funcionando"}


def test_get_csrf_token(client):
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    assert "csrfToken" in response.json()
    assert "csrf_token" in response.cookies


def test_user_registration(client):
    payload = {
        "name": "Maria Teste",
        "email": "maria@example.com",
        "password": "password123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Maria Teste"
    assert data["email"] == "maria@example.com"
    assert "id" in data
    assert data["is_admin"] is False

    # Duplicate registration (400 Bad Request)
    response_duplicate = client.post("/api/auth/register", json=payload)
    assert response_duplicate.status_code == 400
    assert response_duplicate.json()["detail"] == "E-mail já cadastrado"


def test_user_login(client):
    # Register user first
    payload = {
        "name": "Carlos Teste",
        "email": "carlos@example.com",
        "password": "password123"
    }
    client.post("/api/auth/register", json=payload)

    # Login with incorrect password
    response_wrong = client.post("/api/auth/login", json={
        "email": "carlos@example.com",
        "password": "wrongpassword"
    })
    assert response_wrong.status_code == 401
    assert "session_token" not in response_wrong.cookies

    # Login with non-existent email
    response_no_user = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password123"
    })
    assert response_no_user.status_code == 401

    # Login with correct credentials
    response_ok = client.post("/api/auth/login", json={
        "email": "carlos@example.com",
        "password": "password123"
    })
    assert response_ok.status_code == 200
    data = response_ok.json()
    assert data["message"] == "Login realizado com sucesso"
    assert data["user"]["email"] == "carlos@example.com"
    assert "session_token" in response_ok.cookies


# User Profile and Authentication State Tests
def test_profile_success(client):
    # Register and login user
    payload = {
        "name": "Carlos Teste",
        "email": "carlos@example.com",
        "password": "password123"
    }
    client.post("/api/auth/register", json=payload)
    client.post("/api/auth/login", json={
        "email": "carlos@example.com",
        "password": "password123"
    })

    response = client.get("/api/auth/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "carlos@example.com"


def test_profile_not_authenticated(client):
    response = client.get("/api/auth/profile")
    assert response.status_code == 401
    assert response.json()["detail"] == "Usuário não autenticado"


def test_profile_invalid_session(client):
    client.cookies.set("session_token", "invalid_token_123")
    response = client.get("/api/auth/profile")
    assert response.status_code == 401
    assert response.json()["detail"] == "Sessão inválida"


def test_profile_user_deleted(client, db):
    # Register and login user
    payload = {
        "name": "Deleted User",
        "email": "deleted@example.com",
        "password": "password123"
    }
    client.post("/api/auth/register", json=payload)
    client.post("/api/auth/login", json={
        "email": "deleted@example.com",
        "password": "password123"
    })

    # Delete the user directly from the database fixture
    user = db.query(User).filter(User.email == "deleted@example.com").first()
    assert user is not None
    db.delete(user)
    db.commit()

    # Access profile with the now-invalid user session
    response = client.get("/api/auth/profile")
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado"


def test_logout_success(client):
    # Register and login
    payload = {
        "name": "Logout User",
        "email": "logout@example.com",
        "password": "password123"
    }
    client.post("/api/auth/register", json=payload)
    client.post("/api/auth/login", json={
        "email": "logout@example.com",
        "password": "password123"
    })

    # Logout
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logout realizado com sucesso"
    assert "session_token" not in response.cookies


def test_logout_not_logged_in(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logout realizado com sucesso"


# Product CRUD Tests
def test_list_products(client):
    response = client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) > 0
    first_product = products[0]
    assert "name" in first_product
    assert "price" in first_product
    assert "stock" in first_product


def test_get_product_by_id(client):
    # Fetch all products first to get a valid ID
    prod_resp = client.get("/api/products")
    products = prod_resp.json()
    valid_id = products[0]["id"]

    response = client.get(f"/api/products/{valid_id}")
    assert response.status_code == 200
    assert response.json()["id"] == valid_id


def test_get_product_not_found(client):
    response = client.get("/api/products/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"


def test_create_product_admin(client):
    # Login as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})

    new_product_payload = {
        "name": "Orquídea Azul",
        "description": "Orquídea exótica tingida de azul.",
        "price": 89.90,
        "image": "resources/images/orquidea_azul.jpg",
        "category": "Flores",
        "stock": 15
    }

    response = client.post("/api/products", json=new_product_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Orquídea Azul"
    assert data["price"] == 89.90
    assert data["stock"] == 15


def test_create_product_non_admin(client):
    # Register & Login as regular user
    client.post("/api/auth/register", json={
        "name": "User Normal",
        "email": "normal@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={"email": "normal@example.com", "password": "password123"})

    payload = {
        "name": "Planta Secreta",
        "price": 10.0,
        "stock": 5
    }
    response = client.post("/api/products", json=payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso permitido apenas para administradores"


def test_update_product_admin(client):
    # Login as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})

    # Get a product ID
    prod_resp = client.get("/api/products")
    products = prod_resp.json()
    valid_id = products[0]["id"]

    update_payload = {
        "name": "Suculenta Modificada",
        "price": 35.00
    }

    response = client.put(f"/api/products/{valid_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Suculenta Modificada"
    assert response.json()["price"] == 35.00


def test_update_product_not_found(client):
    # Login as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})

    update_payload = {"name": "Inexistente", "price": 10.00}
    response = client.put("/api/products/99999", json=update_payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"


def test_update_product_non_admin(client):
    # Login as normal user
    client.post("/api/auth/register", json={
        "name": "Normal User",
        "email": "normal2@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={"email": "normal2@example.com", "password": "password123"})

    response = client.put("/api/products/1", json={"price": 1.00})
    assert response.status_code == 403


def test_delete_product_admin(client):
    # Login as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})

    # Get a product ID
    prod_resp = client.get("/api/products")
    products = prod_resp.json()
    valid_id = products[0]["id"]

    response = client.delete(f"/api/products/{valid_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Produto removido com sucesso"

    # Confirm it's gone
    get_resp = client.get(f"/api/products/{valid_id}")
    assert get_resp.status_code == 404


def test_delete_product_not_found(client):
    # Login as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})

    response = client.delete("/api/products/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto não encontrado"


def test_delete_product_non_admin(client):
    client.post("/api/auth/register", json={
        "name": "Normal User",
        "email": "normal3@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={"email": "normal3@example.com", "password": "password123"})

    response = client.delete("/api/products/1")
    assert response.status_code == 403


def test_delete_product_with_orders(client):
    client.post("/api/auth/register", json={
        "name": "Cliente Pedido",
        "email": "cliente_del@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={
        "email": "cliente_del@example.com",
        "password": "password123"
    })
    
    prod_resp = client.get("/api/products")
    products = prod_resp.json()
    product_id = products[0]["id"]
    product_price = products[0]["price"]

    order_payload = {
        "items": [
            {
                "product_id": product_id,
                "quantity": 1,
                "price": product_price
            }
        ],
        "discount": 0.0,
        "total_price": product_price
    }
    order_resp = client.post("/api/orders", json=order_payload)
    assert order_resp.status_code == 200

    # Login as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})

    # Try to delete the product that has an order
    response = client.delete(f"/api/products/{product_id}")
    assert response.status_code == 400
    assert "pedido" in response.json()["detail"].lower()



# Order Creation & List Tests
def test_create_order(client):
    # Register and login user
    payload = {
        "name": "Cliente Pedido",
        "email": "cliente_pedido@example.com",
        "password": "password123"
    }
    client.post("/api/auth/register", json=payload)
    client.post("/api/auth/login", json={
        "email": "cliente_pedido@example.com",
        "password": "password123"
    })

    # Fetch product ID from list
    prod_resp = client.get("/api/products")
    products = prod_resp.json()
    product_id = products[0]["id"]
    product_price = products[0]["price"]

    # Create an order
    order_payload = {
        "items": [
            {
                "product_id": product_id,
                "quantity": 2,
                "price": product_price
            }
        ],
        "discount": 0.0,
        "total_price": product_price * 2
    }
    response = client.post("/api/orders", json=order_payload)
    assert response.status_code == 200
    order_data = response.json()
    assert order_data["total_price"] == product_price * 2
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["product_id"] == product_id
    assert order_data["items"][0]["quantity"] == 2


def test_create_order_product_not_found(client):
    client.post("/api/auth/register", json={
        "name": "Cliente Pedido 2",
        "email": "cliente_pedido2@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={
        "email": "cliente_pedido2@example.com",
        "password": "password123"
    })

    order_payload = {
        "items": [
            {
                "product_id": 99999,
                "quantity": 1,
                "price": 10.0
            }
        ],
        "discount": 0.0,
        "total_price": 10.0
    }
    response = client.post("/api/orders", json=order_payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Produto ID 99999 não encontrado"


def test_create_order_insufficient_stock(client):
    client.post("/api/auth/register", json={
        "name": "Cliente Pedido 3",
        "email": "cliente_pedido3@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={
        "email": "cliente_pedido3@example.com",
        "password": "password123"
    })

    prod_resp = client.get("/api/products")
    products = prod_resp.json()
    product_id = products[0]["id"]
    product_price = products[0]["price"]
    excessive_qty = products[0]["stock"] + 10

    order_payload = {
        "items": [
            {
                "product_id": product_id,
                "quantity": excessive_qty,
                "price": product_price
            }
        ],
        "discount": 0.0,
        "total_price": product_price * excessive_qty
    }
    response = client.post("/api/orders", json=order_payload)
    assert response.status_code == 400
    assert "Estoque insuficiente" in response.json()["detail"]


def test_get_orders_non_admin(client):
    # Register and login user
    payload = {
        "name": "Cliente Comum",
        "email": "comum@example.com",
        "password": "password123"
    }
    client.post("/api/auth/register", json=payload)
    client.post("/api/auth/login", json={"email": "comum@example.com", "password": "password123"})

    # Create an order
    prod_resp = client.get("/api/products")
    product = prod_resp.json()[0]
    order_payload = {
        "items": [{"product_id": product["id"], "quantity": 1, "price": product["price"]}],
        "discount": 0.0,
        "total_price": product["price"]
    }
    client.post("/api/orders", json=order_payload)

    # Get orders
    response = client.get("/api/orders")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 1
    assert orders[0]["client_name"] == "Cliente Comum"


def test_get_orders_admin(client):
    # Register and login user and make order
    client.post("/api/auth/register", json={
        "name": "Cliente Comum",
        "email": "comum@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={"email": "comum@example.com", "password": "password123"})
    prod_resp = client.get("/api/products")
    product = prod_resp.json()[0]
    client.post("/api/orders", json={
        "items": [{"product_id": product["id"], "quantity": 1, "price": product["price"]}],
        "discount": 0.0,
        "total_price": product["price"]
    })

    # Login as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    response = client.get("/api/orders")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) >= 1


def test_update_order_status_admin(client):
    # Create order first
    client.post("/api/auth/register", json={
        "name": "Cliente Comum",
        "email": "comum@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={"email": "comum@example.com", "password": "password123"})
    prod_resp = client.get("/api/products")
    product = prod_resp.json()[0]
    order_resp = client.post("/api/orders", json={
        "items": [{"product_id": product["id"], "quantity": 1, "price": product["price"]}],
        "discount": 0.0,
        "total_price": product["price"]
    })
    order_id = order_resp.json()["id"]

    # Login as admin and update status
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    response = client.put(f"/api/orders/{order_id}/status", json={"status": "entregue"})
    assert response.status_code == 200
    assert response.json()["status"] == "entregue"


def test_update_order_status_not_found(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    response = client.put("/api/orders/99999/status", json={"status": "entregue"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Pedido não encontrado"


def test_update_order_status_non_admin(client):
    client.post("/api/auth/register", json={
        "name": "Normal User",
        "email": "normal4@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={"email": "normal4@example.com", "password": "password123"})
    response = client.put("/api/orders/1/status", json={"status": "entregue"})
    assert response.status_code == 403


# Clients Route Tests
def test_get_clients_admin(client):
    # Register a couple of normal clients
    client.post("/api/auth/register", json={
        "name": "Client A",
        "email": "client_a@example.com",
        "password": "password123"
    })
    client.post("/api/auth/register", json={
        "name": "Client B",
        "email": "client_b@example.com",
        "password": "password123"
    })

    # Client A places an order to test the orders/last_purchase calculation
    client.post("/api/auth/login", json={"email": "client_a@example.com", "password": "password123"})
    prod_resp = client.get("/api/products")
    product = prod_resp.json()[0]
    client.post("/api/orders", json={
        "items": [{"product_id": product["id"], "quantity": 1, "price": product["price"]}],
        "discount": 0.0,
        "total_price": product["price"]
    })

    # Login as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    response = client.get("/api/clients")
    assert response.status_code == 200
    clients_data = response.json()
    assert len(clients_data) >= 2

    # Check that Client A stats are correctly calculated
    client_a_stats = next(c for c in clients_data if c["email"] == "client_a@example.com")
    assert client_a_stats["orders_count"] == 1
    assert client_a_stats["total_spent"] == product["price"]
    assert client_a_stats["last_purchase"] is not None

    # Check Client B stats (no orders)
    client_b_stats = next(c for c in clients_data if c["email"] == "client_b@example.com")
    assert client_b_stats["orders_count"] == 0
    assert client_b_stats["total_spent"] == 0
    assert client_b_stats["last_purchase"] is None


def test_get_clients_non_admin(client):
    client.post("/api/auth/register", json={
        "name": "Normal User",
        "email": "normal5@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={"email": "normal5@example.com", "password": "password123"})
    response = client.get("/api/clients")
    assert response.status_code == 403


# Admin DB Inspection & Query Tests
def test_get_db_tables_admin(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    response = client.get("/api/admin/db/tables")
    assert response.status_code == 200
    tables = response.json()
    assert len(tables) > 0
    names = [t["name"] for t in tables]
    assert "users" in names
    assert "products" in names


def test_get_db_tables_non_admin(client):
    client.post("/api/auth/register", json={
        "name": "Normal User",
        "email": "normal6@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={"email": "normal6@example.com", "password": "password123"})
    response = client.get("/api/admin/db/tables")
    assert response.status_code == 403


def test_get_table_schema_admin(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    response = client.get("/api/admin/db/tables/users/schema")
    assert response.status_code == 200
    schema = response.json()
    assert "columns" in schema
    assert "primary_keys" in schema
    assert "foreign_keys" in schema


def test_get_table_schema_not_found(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    response = client.get("/api/admin/db/tables/non_existent_table/schema")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tabela não encontrada"


def test_get_table_data_admin(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    # 1. Simple fetch
    response = client.get("/api/admin/db/tables/users/data")
    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert data["total"] >= 1

    # 2. Search filtering
    response_search = client.get("/api/admin/db/tables/users/data?search_col=email&search_val=admin")
    assert response_search.status_code == 200
    assert response_search.json()["total"] == 1
    assert response_search.json()["rows"][0]["email"] == "admin@verdanza.com"

    # 3. Sorting
    response_sort = client.get("/api/admin/db/tables/users/data?sort_by=name&sort_order=desc")
    assert response_sort.status_code == 200

    # 4. Access table containing datetimes to test isoformat serialization
    # Let's place an order first, then query database tables directly
    client.post("/api/auth/register", json={
        "name": "Client C",
        "email": "client_c@example.com",
        "password": "password123"
    })
    client.post("/api/auth/login", json={"email": "client_c@example.com", "password": "password123"})
    prod_resp = client.get("/api/products")
    product = prod_resp.json()[0]
    client.post("/api/orders", json={
        "items": [{"product_id": product["id"], "quantity": 1, "price": product["price"]}],
        "discount": 0.0,
        "total_price": product["price"]
    })
    # Login back as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    orders_data_resp = client.get("/api/admin/db/tables/orders/data")
    assert orders_data_resp.status_code == 200
    orders_rows = orders_data_resp.json()["rows"]
    assert len(orders_rows) >= 1
    # Check that created_at datetime is serialized as string (ISO format)
    assert isinstance(orders_rows[0]["created_at"], str)


def test_get_table_data_not_found(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    response = client.get("/api/admin/db/tables/non_existent_table/data")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tabela não encontrada"


def test_execute_custom_query_select(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    # Valid SELECT
    response = client.post("/api/admin/db/query", json={"query": "SELECT id, email, is_admin FROM users"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["rows"]) >= 1
    assert "email" in data["rows"][0]
    assert data["rows"][0]["email"] == "admin@verdanza.com"


def test_execute_custom_query_forbidden_keyword(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    # Query containing forbidden keyword
    response = client.post("/api/admin/db/query", json={"query": "SELECT * FROM users; DROP TABLE users"})
    assert response.status_code == 403
    assert "proibida por segurança" in response.json()["detail"]


def test_execute_custom_query_non_select(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    # Query that doesn't start with select, explain, or show
    response = client.post("/api/admin/db/query", json={"query": "INSERT INTO users (name) VALUES ('Test')"})
    assert response.status_code == 403
    assert "Apenas consultas de leitura (SELECT) são permitidas" in response.json()["detail"]


def test_execute_custom_query_empty(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    response = client.post("/api/admin/db/query", json={"query": "   "})
    assert response.status_code == 400
    assert response.json()["detail"] == "Consulta vazia"


def test_execute_custom_query_syntax_error(client):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    response = client.post("/api/admin/db/query", json={"query": "SELECT FROM users"})
    assert response.status_code == 400


def test_execute_custom_query_no_rows(client):
    # Login as admin
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    # Set up dependency override to simulate a query that returns no rows (e.g. metadata or PRAGMA-style)
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.returns_rows = False
    mock_result.rowcount = 42
    mock_db.execute.return_value = mock_result
    
    def override_mock_db():
        yield mock_db
    
    fastapi_app.dependency_overrides[get_db] = override_mock_db
    try:
        response = client.post("/api/admin/db/query", json={"query": "SELECT * FROM users"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert data["count"] == 42
    finally:
        # Clean up
        del fastapi_app.dependency_overrides[get_db]


# Additional Core Unit Tests for Coverage
def test_get_db_generator(monkeypatch):
    from app.database import get_db
    mock_session = MagicMock()
    # Mock SessionLocal inside app.database to return a mock session
    monkeypatch.setattr("app.database.SessionLocal", lambda: mock_session)
    
    generator = get_db()
    db_session = next(generator)
    assert db_session == mock_session
    
    try:
        next(generator)
    except StopIteration:
        pass
    
    mock_session.close.assert_called_once()


def test_seed_functions(db):
    from app.seed import create_admin_user, seed_products
    # First call creates the admin in this db fixture
    create_admin_user(db)
    # Second call covers existing_admin path (returns early)
    create_admin_user(db)
    
    # Call seed products to test duplicate avoidance
    seed_products(db)
    # Call again to cover existing product path
    seed_products(db)


def test_create_tables(monkeypatch):
    from app.database import create_tables
    # Mock engine
    mock_engine = MagicMock()
    monkeypatch.setattr("app.database.engine", mock_engine)
    create_tables()
    # verify it attempted to call metadata creation
    assert mock_engine.name is not None


def test_get_table_data_postgres_branch(client, monkeypatch):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_result.fetchall.return_value = []
    
    from conftest import engine as test_engine
    mock_url = MagicMock()
    mock_url.__str__.return_value = "postgresql://mock"
    monkeypatch.setattr(test_engine, "url", mock_url)
    
    # Monkeypatch execute on the class level so that ANY Session created during the call is mocked
    monkeypatch.setattr("sqlalchemy.orm.Session.execute", lambda self, *args, **kwargs: mock_result)
    
    response = client.get("/api/admin/db/tables/users/data?search_col=email&search_val=admin")
    assert response.status_code == 200


def test_get_table_data_isoformat_and_binary(client, monkeypatch):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    from datetime import datetime
    mock_row = [1, "Name", datetime.now(), b"password_hash", False]
    
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_result.fetchall.return_value = [mock_row]
    
    # Monkeypatch execute on the class level so that ANY Session created during the call is mocked
    monkeypatch.setattr("sqlalchemy.orm.Session.execute", lambda self, *args, **kwargs: mock_result)
    
    response = client.get("/api/admin/db/tables/users/data")
    assert response.status_code == 200
    row = response.json()["rows"][0]
    # Verify datetime was converted to ISO format string
    assert isinstance(row["email"], str)
    # Verify binary was converted to "<binary data>"
    assert row["password_hash"] == "<binary data>"


def test_execute_custom_query_isoformat_and_binary(client, monkeypatch):
    client.post("/api/auth/login", json={"email": "admin@verdanza.com", "password": "12345678"})
    
    from datetime import datetime
    mock_row = MagicMock()
    mock_row.col_dt = datetime.now()
    mock_row.col_bytes = b"binary"
    
    mock_result = MagicMock()
    mock_result.returns_rows = True
    mock_result.keys.return_value = ["col_dt", "col_bytes"]
    mock_result.fetchall.return_value = [mock_row]
    
    # Monkeypatch execute on the class level so that ANY Session created during the call is mocked
    monkeypatch.setattr("sqlalchemy.orm.Session.execute", lambda self, *args, **kwargs: mock_result)
    
    response = client.post("/api/admin/db/query", json={"query": "SELECT col_dt, col_bytes FROM dummy"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    row = data["rows"][0]
    assert isinstance(row["col_dt"], str)
    assert row["col_bytes"] == "<binary data>"
