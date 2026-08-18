import hashlib
import random
from datetime import datetime, timedelta, timezone

from app.core.config import (
    ACCESS_TOKEN_EXPIRE,
    ALGORITHM,
    EMAIL_FROM,
    EMAIL_HOST,
    EMAIL_PASSWORD,
    EMAIL_PORT,
    EMAIL_USER,
    REFRESH_TOKEN_EXPIRE,
    SECRET_KEY,
)
from app.dependencies import get_current_user, make_session, verify_token
from app.models.models import UserModel
from app.schemas.schemas import (
    ForgetPasswordSchema,
    LoginSchema,
    ResetPasswordSchema,
    UserSchema,
)
from app.security import bcrypt_context
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jose import jwt
from sqlalchemy.orm import Session

mail_config = ConnectionConfig(
    MAIL_USERNAME=EMAIL_USER,
    MAIL_PASSWORD=EMAIL_PASSWORD,
    MAIL_FROM=EMAIL_FROM,
    MAIL_PORT=EMAIL_PORT,
    MAIL_SERVER=EMAIL_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

auth_router = APIRouter(prefix="/auth", tags=["Autenticação"])


# CRIAÇÃO DE TOKEN
def create_token(id: int, token_type: str, duration: timedelta):
    expire = datetime.now(timezone.utc) + duration
    payload = {
        "sub": id,
        "type": token_type,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# GERAÇÃO DE TOKENS DE AUTENTICAÇÃO (ACCESS E REFRESH)
def generate_auth_tokens(user_id: int):
    access_token = create_token(
        user_id,
        token_type="access",
        duration=timedelta(minutes=ACCESS_TOKEN_EXPIRE),
    )
    refresh_token = create_token(
        user_id,
        token_type="refresh",
        duration=timedelta(days=REFRESH_TOKEN_EXPIRE),
    )
    return access_token, refresh_token


# AUTENTICAÇÃO
def authenticate(username: str, password: str, db: Session):
    user = db.query(UserModel).filter(UserModel.email == username).first()
    if not user:
        return None
    if not bcrypt_context.verify(password, user.senha):
        return None
    if not user.ativo:
        return None
    return user


# FUNÇÃO PARA ENVIAR EMAIL COM CÓDIGO DE RECUPERAÇÃO
async def send_reset_code_email(destinatario: str, codigo: str):
    mensagem = MessageSchema(
        subject="Código de recuperação de senha",
        recipients=[destinatario],
        body=f"Seu código de recuperação é: {codigo}\nEle expira em 15 minutos.",
        subtype=MessageType.plain,
    )

    fm = FastMail(mail_config)
    await fm.send_message(mensagem)


# FUNÇÃO PARA HASH DO CÓDIGO (SHA-256)
def hash_code(codigo: str) -> str:
    return hashlib.sha256(codigo.encode()).hexdigest()


# --- ROTAS
# LOGIN
@auth_router.post("/login")
async def login(schema: LoginSchema, db: Session = Depends(make_session)):
    user = authenticate(schema.email, schema.senha, db)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token, refresh_token = generate_auth_tokens(user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "nome": user.nome,
    }


# LOGIN VIA FORM
@auth_router.post("/loginform")
async def loginform(
    schema: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(make_session)
):
    user = authenticate(schema.username, schema.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token, refresh_token = generate_auth_tokens(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


# CADASTRO
@auth_router.post("/register")
async def register(schema: UserSchema, db: Session = Depends(make_session)):
    existing_user = db.query(UserModel).filter(UserModel.email == schema.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado.")

    hashed_password = bcrypt_context.hash(schema.senha)
    new_user = UserModel(
        nome=schema.nome,
        email=schema.email,
        senha=hashed_password,
        ativo=schema.ativo,
        admin=schema.admin,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token, refresh_token = generate_auth_tokens(new_user.id)
    return {
        "message": f"Cadastro realizado com sucesso! Bem-vindo {new_user.nome}",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


# ESQUECEU SENHA
@auth_router.post("/forgot-password")
async def forgotpassword(
    schema: ForgetPasswordSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(make_session),
):
    user = db.query(UserModel).filter(UserModel.email == schema.email).first()
    if not user:
        raise HTTPException(
            status_code=404, detail="Email informado não está cadastrado"
        )

    now = datetime.now(timezone.utc)

    if user.reset_code_expires_at and user.reset_code_expires_at > (
        now + timedelta(minutes=14)
    ):
        raise HTTPException(
            status_code=429,
            detail="Aguarde 1 minuto antes de solicitar outro código.",
        )

    codigo = f"{random.randint(0, 999999):06d}"
    user.reset_code_hash = hash_code(codigo)
    user.reset_code_expires_at = now + timedelta(minutes=15)
    user.reset_code_attempts = 0

    background_tasks.add_task(send_reset_code_email, user.email, codigo)

    reset_token = create_token(
        id=user.id, token_type="reset", duration=timedelta(minutes=15)
    )

    db.commit()
    return {
        "message": "Um código foi enviado para seu email",
        "reset_token": reset_token,
    }


# REDEFINIR SENHA
@auth_router.post("/reset-password")
async def reset_password(
    schema: ResetPasswordSchema, db: Session = Depends(make_session)
):
    user = db.query(UserModel).filter(UserModel.email == schema.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    try:
        payload = jwt.decode(schema.reset_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            raise HTTPException(
                status_code=400, detail="Token inválido para redefinição."
            )
        if payload.get("sub") != user.id:
            raise HTTPException(
                status_code=400, detail="Token não corresponde a este usuário."
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token de redefinição expirado.")
    except jwt.JWTError:
        raise HTTPException(status_code=400, detail="Token de redefinição inválido.")

        if not user.reset_code_hash or not user.reset_code_expires_at:
            raise HTTPException(
                status_code=400, detail="Nenhum código de recuperação ativo."
            )
    if user.reset_code_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Código de recuperação expirado.")

    if user.reset_code_attempts >= 5:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas. Solicite um novo código.",
        )

    if user.reset_code_hash != hash_code(schema.code):
        user.reset_code_attempts = (user.reset_code_attempts or 0) + 1
        db.commit()
        raise HTTPException(status_code=400, detail="Código de recuperação inválido.")

    user.senha = bcrypt_context.hash(schema.new_password)
    user.reset_code_hash = None
    user.reset_code_expires_at = None
    user.reset_code_attempts = 0
    db.commit()

    return {"message": "Senha redefinida com sucesso!"}


# REFRESH TOKEN
@auth_router.post("/refresh")
async def refresh_token(
    data: dict = Depends(verify_token), db: Session = Depends(make_session)
):

    token_type = data.get("type")
    user_id = data.get("sub")

    if not token_type == "refresh":
        raise HTTPException(status_code=401, detail="Token de refresh exigido.")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")

    access_token, refresh_token = generate_auth_tokens(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "nome": user.nome,
    }


# MEUS DADOS
@auth_router.get("/me")
async def me(user: UserModel = Depends(get_current_user)):
    return {
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "admin": user.admin,
        "ativo": user.ativo,
    }
