from app.dependencies import get_current_user, make_session
from app.models.models import (
    ItemCardapio,
    ItemPedidoModel,
    PedidoModel,
    StatusEnum,
    UserModel,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

order_router = APIRouter(prefix="/pedidos", tags=["orders"])


def verificar_permissao_pedido(pedido, current_user):
    if current_user.admin or pedido.usuario_id == current_user.id:
        return True
    raise HTTPException(status_code=403, detail="Acesso negado a este pedido.")


@order_router.post("/criar_pedido")
async def criar_pedido(
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    novo_pedido = PedidoModel(usuario_id=current_user.id, status=StatusEnum.PENDENTE)
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)
    return {"message": "Pedido iniciado!", "pedido_id": novo_pedido.id}


@order_router.post("/adicionar_item/{pedido_id}")
async def adicionar_item(
    pedido_id: int,
    item_cardapio_id: int,
    quantidade: int,
    sabor: str | None = None,
    tamanho: str | None = None,
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    verificar_permissao_pedido(pedido, current_user)

    if pedido.status != StatusEnum.PENDENTE:
        raise HTTPException(
            status_code=400,
            detail="Não é possível alterar um pedido já finalizado ou cancelado.",
        )

    # BUSCA O PREÇO REAL NO CARDÁPIO (SEGURANÇA TOTAL)
    produto = db.query(ItemCardapio).filter(ItemCardapio.id == item_cardapio_id).first()
    if not produto or not produto.disponivel:
        raise HTTPException(
            status_code=404, detail="Produto não disponível no cardápio."
        )

    new_item = ItemPedidoModel(
        pedido_id=pedido_id,
        item_cardapio_id=item_cardapio_id,
        quantidade=quantidade,
        sabor=sabor or produto.nome,  # Nome da pizza como snapshot
        tamanho=tamanho or "Padrão",
        preco_unitario=produto.preco,  # PREÇO VEM DO BANCO
    )

    pedido.adicionar_item_do_total(new_item.quantidade, new_item.preco_unitario)
    db.add(new_item)
    db.commit()
    db.refresh(pedido)

    return {"message": "Item adicionado!", "total_atual": pedido.preco}


@order_router.delete("/remover_item/{pedido_id}/{item_id}")
async def remover_item(
    pedido_id: int,
    item_id: int,
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    verificar_permissao_pedido(pedido, current_user)

    item = (
        db.query(ItemPedidoModel)
        .filter(ItemPedidoModel.id == item_id, ItemPedidoModel.pedido_id == pedido_id)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado no pedido.")

    pedido.subtrair_item_do_total(item.quantidade, item.preco_unitario)
    db.delete(item)
    db.commit()
    return {"message": "Item removido.", "total_atual": pedido.preco}


@order_router.post("/finalizar/{pedido_id}")
async def finalizar_pedido(
    pedido_id: int,
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    verificar_permissao_pedido(pedido, current_user)

    pedido.status = StatusEnum.FINALIZADO
    db.commit()
    return {"message": "Pedido enviado para a cozinha!"}


@order_router.get("/meus_pedidos")
async def listar_meus_pedidos(
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    return (
        db.query(PedidoModel)
        .options(joinedload(PedidoModel.itens))
        .filter(PedidoModel.usuario_id == current_user.id)
        .all()
    )
