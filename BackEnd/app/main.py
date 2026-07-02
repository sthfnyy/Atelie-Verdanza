from fastapi import FastAPI, APIRouter, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from app.seed import create_admin_user, seed_products

from app.database import create_tables, get_db, SessionLocal, User, Product, Order, OrderItem


from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    ClientResponse,
)
from app.security import (
    hash_password,
    verify_password,
    create_session,
    get_user_id_by_session,
    delete_session,
    generate_csrf_token,
)

app = FastAPI(title="API Ateliê Verdanza")

api = APIRouter(prefix="/api")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()

    db = SessionLocal()
    try:
        create_admin_user(db)
        seed_products(db)
    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "Backend FastAPI funcionando"}


@api.get("/status")
def status():
    return {"status": "API funcionando"}


@api.get("/auth/csrf")
def get_csrf(response: Response):
    csrf_token = generate_csrf_token()

    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="lax",
    )

    return {"csrfToken": csrf_token}


@api.post("/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        is_admin=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@api.post("/auth/login")
def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    session_token = create_session(user.id)

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        samesite="lax",
    )

    return {
        "message": "Login realizado com sucesso",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
        },
    }


def get_current_user(request: Request, db: Session):
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Usuário não autenticado")

    user_id = get_user_id_by_session(session_token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Sessão inválida")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return user


def require_admin(request: Request, db: Session):
    user = get_current_user(request, db)

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para administradores")

    return user

@api.get("/auth/profile", response_model=UserResponse)
def profile(request: Request, db: Session = Depends(get_db)):
    return get_current_user(request, db)


@api.post("/auth/logout")
def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")

    if session_token:
        delete_session(session_token)

    response.delete_cookie("session_token")

    return {"message": "Logout realizado com sucesso"}

@api.get("/products", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products


@api.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    return product


@api.post("/products", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    require_admin(request, db)

    product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        image=product_data.image,
        category=product_data.category,
        stock=product_data.stock,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@api.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    require_admin(request, db)

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    update_data = product_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


@api.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    require_admin(request, db)

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    product_has_orders = db.query(OrderItem).filter(
        OrderItem.product_id == product_id
    ).first()

    if product_has_orders:
        raise HTTPException(
            status_code=400,
            detail="Produto não pode ser removido porque já está vinculado a um pedido"
        )

    db.delete(product)
    db.commit()

    return {"message": "Produto removido com sucesso"}


@api.post("/orders", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)

    # 1. Verify items & stock, calculate totals
    new_order = Order(
        user_id=current_user.id,
        total_price=order_data.total_price,
        discount=order_data.discount,
        status="pendente",
    )
    db.add(new_order)
    db.flush()  # gets new_order.id

    total_qty = 0
    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Produto ID {item.product_id} não encontrado")

        if product.stock < item.quantity:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente para o produto {product.name}")

        # Deduct stock
        product.stock -= item.quantity
        total_qty += item.quantity

        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=item.quantity,
            price=item.price
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)

    return {
        "id": new_order.id,
        "user_id": new_order.user_id,
        "client_name": current_user.name,
        "total_price": new_order.total_price,
        "discount": new_order.discount,
        "status": new_order.status,
        "created_at": new_order.created_at.strftime("%d/%m/%Y %H:%M"),
        "items_count": total_qty,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "product_name": item.product.name if item.product else "Produto não encontrado"
            } for item in new_order.items
        ]
    }


@api.get("/orders", response_model=list[OrderResponse])
def get_orders(
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)

    if current_user.is_admin:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()
    else:
        orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()

    response = []
    for order in orders:
        items_count = sum(item.quantity for item in order.items)
        response.append({
            "id": order.id,
            "user_id": order.user_id,
            "client_name": order.user.name,
            "total_price": order.total_price,
            "discount": order.discount,
            "status": order.status,
            "created_at": order.created_at.strftime("%d/%m/%Y %H:%M"),
            "items_count": items_count,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price,
                    "product_name": item.product.name if item.product else "Produto não encontrado"
                } for item in order.items
            ]
        })
    return response


@api.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    require_admin(request, db)

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    order.status = status_data.status
    db.commit()
    db.refresh(order)

    items_count = sum(item.quantity for item in order.items)
    return {
        "id": order.id,
        "user_id": order.user_id,
        "client_name": order.user.name,
        "total_price": order.total_price,
        "discount": order.discount,
        "status": order.status,
        "created_at": order.created_at.strftime("%d/%m/%Y %H:%M"),
        "items_count": items_count,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "product_name": item.product.name if item.product else "Produto não encontrado"
            } for item in order.items
        ]
    }


@api.get("/clients", response_model=list[ClientResponse])
def get_clients(
    request: Request,
    db: Session = Depends(get_db)
):
    require_admin(request, db)

    # Get users who are not admins
    clients = db.query(User).filter(User.is_admin == False).all()

    response = []
    for client in clients:
        # Calculate stats
        client_orders = db.query(Order).filter(Order.user_id == client.id).all()
        orders_count = len(client_orders)
        total_spent = sum(order.total_price for order in client_orders)

        last_purchase_str = None
        if client_orders:
            # Get latest order
            latest_order = max(client_orders, key=lambda o: o.created_at)
            last_purchase_str = latest_order.created_at.strftime("%d/%m/%Y")

        response.append({
            "name": client.name,
            "email": client.email,
            "orders_count": orders_count,
            "total_spent": total_spent,
            "last_purchase": last_purchase_str
        })

    return response


@api.get("/admin/db/tables")
def get_db_tables(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    
    result = []
    for table in tables:
        count_res = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = count_res.scalar()
        result.append({
            "name": table,
            "rows": count
        })
    return result


@api.get("/admin/db/tables/{table_name}/schema")
def get_table_schema(table_name: str, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    inspector = inspect(db.bind)
    
    if table_name not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail="Tabela não encontrada")
        
    columns = inspector.get_columns(table_name)
    fks = inspector.get_foreign_keys(table_name)
    pks = inspector.get_pk_constraint(table_name)
    
    schema_cols = []
    for col in columns:
        schema_cols.append({
            "name": col["name"],
            "type": str(col["type"]),
            "nullable": col["nullable"],
            "primary_key": col["name"] in pks.get("constrained_columns", []),
            "default": str(col["default"]) if col.get("default") is not None else None
        })
        
    return {
        "columns": schema_cols,
        "foreign_keys": fks,
        "primary_keys": pks.get("constrained_columns", [])
    }


@api.get("/admin/db/tables/{table_name}/data")
def get_table_data(
    table_name: str, 
    request: Request, 
    page: int = 1, 
    limit: int = 50, 
    search_col: str = None, 
    search_val: str = None,
    sort_by: str = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db)
):
    require_admin(request, db)
    inspector = inspect(db.bind)
    
    if table_name not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail="Tabela não encontrada")
        
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    
    # Safely build query
    query_str = f"SELECT * FROM {table_name}"
    params = {}
    
    if search_col and search_val and search_col in columns:
        # Simple case-insensitive search if text, otherwise exact
        is_postgres = "postgresql" in str(db.bind.url)
        if is_postgres:
            query_str += f" WHERE CAST({search_col} AS TEXT) ILIKE :search_val"
        else:
            query_str += f" WHERE CAST({search_col} AS TEXT) LIKE :search_val"
        params["search_val"] = f"%{search_val}%"
        
    # Get total count with filters
    count_query = f"SELECT COUNT(*) FROM ({query_str}) AS sub"
    total_count = db.execute(text(count_query), params).scalar()
    
    if sort_by and sort_by in columns:
        order = "DESC" if sort_order.lower() == "desc" else "ASC"
        query_str += f" ORDER BY {sort_by} {order}"
        
    query_str += f" LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = (page - 1) * limit
    
    rows = db.execute(text(query_str), params).fetchall()
    
    data_rows = []
    for row in rows:
        row_dict = {}
        # Convert row to dict
        for col_idx, col_name in enumerate(columns):
            val = row[col_idx]
            # Convert datetime or non-serializable objects to string
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            elif isinstance(val, (bytes, bytearray)):
                val = "<binary data>"
            row_dict[col_name] = val
        data_rows.append(row_dict)
        
    return {
        "columns": columns,
        "rows": data_rows,
        "total": total_count,
        "page": page,
        "limit": limit
    }


@api.post("/admin/db/query")
def execute_custom_query(query_data: dict, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    query_str = query_data.get("query", "").strip()
    
    if not query_str:
        raise HTTPException(status_code=400, detail="Consulta vazia")
        
    # Simple check for read-only query
    lower_query = query_str.lower()
    if not lower_query.startswith("select") and not lower_query.startswith("explain") and not lower_query.startswith("show"):
        raise HTTPException(status_code=403, detail="Apenas consultas de leitura (SELECT) são permitidas por segurança.")
        
    # Check if there's any modifying keyword
    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate", "create", "grant", "revoke"]
    for keyword in forbidden:
        words = lower_query.replace(";", " ").replace("(", " ").replace(")", " ").split()
        if keyword in words:
            raise HTTPException(status_code=403, detail=f"A palavra-chave '{keyword.upper()}' é proibida por segurança.")
            
    try:
        res = db.execute(text(query_str))
        if res.returns_rows:
            columns = list(res.keys())
            rows = res.fetchall()
            
            data_rows = []
            for row in rows:
                row_dict = {}
                for col_name in columns:
                    val = getattr(row, col_name)
                    if hasattr(val, "isoformat"):
                        val = val.isoformat()
                    elif isinstance(val, (bytes, bytearray)):
                        val = "<binary data>"
                    row_dict[col_name] = val
                data_rows.append(row_dict)
                
            return {
                "success": True,
                "columns": columns,
                "rows": data_rows,
                "count": len(data_rows)
            }
        else:
            return {
                "success": True,
                "message": "Comando executado com sucesso, mas não retornou linhas.",
                "count": res.rowcount
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


app.include_router(api)