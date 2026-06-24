from fastapi import FastAPI, APIRouter, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.seed import create_admin_user

from app.database import create_tables, get_db, SessionLocal, User, Product
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
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

    db.delete(product)
    db.commit()

    return {"message": "Produto removido com sucesso"}
app.include_router(api)