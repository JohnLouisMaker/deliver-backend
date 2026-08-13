import os
import shutil
from uuid import uuid4

from app.dependencies import get_current_user, make_session
from app.models.models import CategoriaEnum, ItemCardapio, UserModel
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

product_router = APIRouter(prefix="/cardapio", tags=["cardapio"])

UPLOAD_DIR = "static/uploads"


@product_router.get("", include_in_schema=False)
@product_router.get("/")
async def listar_cardapio(
    categoria: CategoriaEnum | None = None, db: Session = Depends(make_session)
):
    """Lista itens disponíveis no cardápio com filtro opcional."""
    query = db.query(ItemCardapio).filter(ItemCardapio.disponivel)
    if categoria:
        query = query.filter(ItemCardapio.categoria == categoria)
    return query.all()


@product_router.get("/{item_id}")
async def buscar_item(item_id: int, db: Session = Depends(make_session)):
    """Busca detalhes de um item específico."""
    item = db.query(ItemCardapio).filter(ItemCardapio.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return item


@product_router.post("/adicionar", status_code=status.HTTP_201_CREATED)
async def adicionar_item_cardapio(
    nome: str = Form(...),
    descricao: str = Form(None),
    preco: float = Form(...),
    categoria: CategoriaEnum = Form(...),
    imagem: UploadFile = File(...),
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    if not current_user.admin:
        raise HTTPException(
            status_code=403, detail="Acesso negado: apenas administradores."
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(imagem.filename)[1]
    filename = f"{uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(imagem.file, buffer)
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao salvar imagem.")

    novo_item = ItemCardapio(
        nome=nome,
        descricao=descricao,
        preco=preco,
        categoria=categoria,
        imagem_url=f"/static/uploads/{filename}",
        disponivel=True,
    )

    db.add(novo_item)
    db.commit()
    db.refresh(novo_item)
    return {"message": "Item adicionado!", "item": novo_item}


@product_router.patch("/editar/{item_id}")
async def editar_item(
    item_id: int,
    novo_preco: float | None = Form(None),
    novo_nome: str | None = Form(None),
    disponibilidade: bool | None = Form(None),
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    if not current_user.admin:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    item = db.query(ItemCardapio).filter(ItemCardapio.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")

    if novo_preco is not None:
        item.preco = novo_preco
    if novo_nome is not None:
        item.nome = novo_nome
    if disponibilidade is not None:
        item.disponivel = disponibilidade

    db.commit()
    return {"message": "Item atualizado!", "item": item}


@product_router.delete("/deletar/{item_id}")
async def deletar_item(
    item_id: int,
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    if not current_user.admin:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    item = db.query(ItemCardapio).filter(ItemCardapio.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")

    if item.imagem_url:
        path_foto = item.imagem_url.lstrip("/")
        if os.path.exists(path_foto):
            os.remove(path_foto)

    db.delete(item)
    db.commit()
    return {"message": f"Item '{item.nome}' removido."}
