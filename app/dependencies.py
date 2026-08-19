from app.core.config import ALGORITHM, SECRET_KEY
from app.database.database import engine
from app.models.models import UserModel
from app.security import oauth2_schema
from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session, sessionmaker


def make_session():
    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
    finally:
        session.close()


def verify_token(token: str = Depends(oauth2_schema)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")


def get_current_user(
    payload: dict = Depends(verify_token), session: Session = Depends(make_session)
):
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token de acesso exigido.")

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido.")

    user = session.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")
    return user
