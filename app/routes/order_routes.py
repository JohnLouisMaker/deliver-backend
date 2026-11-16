from decimal import Decimal

from app.dependencies import get_current_user, make_session
from app.models.models import (
    FormaPagamentoEnum,
    ItemCardapio,
    ItemPedidoModel,
    PedidoModel,
    StatusEnum,
    UserModel,
)
from app.schemas.schemas import (
    CheckoutResponse,
    CheckoutSchema,
    FinalizarPedidoSchema,
    FormaPagamentoSchema,
    ItemPedidoSchema,
    PedidoSchemaResponse,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

order_router = APIRouter(prefix="/pedidos", tags=["orders"])


def verificar_permissao_pedido(pedido, current_user):
    if current_user.admin or pedido.usuario_id == current_user.id:
        return True
    raise HTTPException(status_code=403, detail="Acesso negado a este pedido.")


def _resolver_preco_item(produto: ItemCardapio, tamanho):
    """Define o preco oficial do item, ignorando qualquer valor do cliente.

    Pizza so tem preco por tamanho (tabela itens_cardapio_precos_tamanho); os
    demais itens usam o preco fixo do cardapio. A ausencia de preco gera erro
    explicito, nunca um valor padrao.
    """
    possui_tamanhos = bool(produto.precos_tamanho)

    if tamanho is None:
        if possui_tamanhos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Selecione o tamanho para '{produto.nome}'.",
            )
        return Decimal(str(produto.preco)), None, None

    if not possui_tamanhos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O item '{produto.nome}' nao possui tamanhos.",
        )

    try:
        preco = produto.preco_para_tamanho(tamanho)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tamanho '{tamanho.value}' sem preco para '{produto.nome}'.",
        )

    return Decimal(preco), tamanho.value, produto.nome


def _buscar_produto_disponivel(db: Session, item_cardapio_id: int) -> ItemCardapio:
    produto = db.get(ItemCardapio, item_cardapio_id)
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto nao encontrado no cardapio.",
        )
    if not produto.disponivel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Produto '{produto.nome}' indisponivel.",
        )
    return produto


@order_router.post("", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
@order_router.post(
    "/criar_pedido",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def criar_pedido(
    dados: CheckoutSchema,
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    """Checkout transacional: cria pedido pendente e todos os itens de uma vez."""
    itens_calculados = []
    total = Decimal("0")

    for item in dados.itens:
        produto = _buscar_produto_disponivel(db, item.item_cardapio_id)
        preco_unitario, tamanho_valor, sabor = _resolver_preco_item(
            produto, item.tamanho
        )
        total += preco_unitario * item.quantidade
        itens_calculados.append(
            (produto, item.quantidade, preco_unitario, tamanho_valor, sabor)
        )

    if dados.forma_pagamento == FormaPagamentoSchema.DINHEIRO:
        if dados.troco_para is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Informe o valor de troco para pagamento em dinheiro.",
            )
        if Decimal(str(dados.troco_para)) < total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O valor de troco deve ser maior ou igual ao total do pedido.",
            )
        troco_para = dados.troco_para
    else:
        troco_para = None

    pedido = PedidoModel(
        usuario_id=current_user.id,
        status=StatusEnum.PENDENTE,
        preco=float(total),
        endereco_entrega=dados.endereco_entrega,
        forma_pagamento=FormaPagamentoEnum[dados.forma_pagamento.name],
        troco_para=troco_para,
        observacao=dados.observacao,
        telefone_contato=dados.telefone_contato,
    )

    try:
        db.add(pedido)
        db.flush()

        for produto, quantidade, preco_unitario, tamanho_valor, sabor in itens_calculados:
            db.add(
                ItemPedidoModel(
                    pedido_id=pedido.id,
                    item_cardapio_id=produto.id,
                    nome_snapshot=produto.nome,
                    sabor=sabor,
                    tamanho=tamanho_valor,
                    quantidade=quantidade,
                    preco_unitario=float(preco_unitario),
                    imagem_url_snapshot=produto.imagem_url,
                )
            )

        db.commit()
        db.refresh(pedido)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel concluir o pedido.",
        )

    return {
        "pedido": {
            "id": pedido.id,
            "status": pedido.status.name,
            "itens": [
                {
                    "item_cardapio_id": produto.id,
                    "nome_snapshot": produto.nome,
                    "tamanho": tamanho_valor,
                    "quantidade": quantidade,
                    "preco_unitario": float(preco_unitario),
                }
                for produto, quantidade, preco_unitario, tamanho_valor, _ in itens_calculados
            ],
            "total": float(pedido.preco),
        }
    }


@order_router.post("/adicionar_item/{pedido_id}")
async def adicionar_item(
    pedido_id: int,
    dados: ItemPedidoSchema,
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    """Adiciona um item a um pedido pendente existente (fluxo incremental)."""
    pedido = db.get(PedidoModel, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado."
        )

    verificar_permissao_pedido(pedido, current_user)

    if pedido.status != StatusEnum.PENDENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao e possivel alterar um pedido ja finalizado ou cancelado.",
        )

    produto = _buscar_produto_disponivel(db, dados.item_cardapio_id)
    preco_unitario, tamanho_valor, sabor = _resolver_preco_item(produto, dados.tamanho)

    novo_item = ItemPedidoModel(
        pedido_id=pedido.id,
        item_cardapio_id=produto.id,
        nome_snapshot=produto.nome,
        sabor=sabor,
        tamanho=tamanho_valor,
        quantidade=dados.quantidade,
        preco_unitario=float(preco_unitario),
        imagem_url_snapshot=produto.imagem_url,
    )

    try:
        db.add(novo_item)
        pedido.adicionar_item_do_total(dados.quantidade, float(preco_unitario))
        db.commit()
        db.refresh(pedido)
        db.refresh(novo_item)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel adicionar o item ao pedido.",
        )

    return {
        "message": "Item adicionado!",
        "item": {
            "item_cardapio_id": produto.id,
            "nome_snapshot": produto.nome,
            "tamanho": tamanho_valor,
            "quantidade": dados.quantidade,
            "preco_unitario": float(preco_unitario),
        },
        "total_atual": pedido.preco,
    }


@order_router.delete("/remover_item/{pedido_id}/{item_id}")
async def remover_item(
    pedido_id: int,
    item_id: int,
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    pedido = db.get(PedidoModel, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado."
        )
    verificar_permissao_pedido(pedido, current_user)

    item = (
        db.query(ItemPedidoModel)
        .filter(
            ItemPedidoModel.id == item_id,
            ItemPedidoModel.pedido_id == pedido_id,
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item nao encontrado no pedido.",
        )

    pedido.subtrair_item_do_total(item.quantidade, item.preco_unitario)
    db.delete(item)
    db.commit()
    return {"message": "Item removido.", "total_atual": pedido.preco}


@order_router.post("/finalizar/{pedido_id}")
async def finalizar_pedido(
    pedido_id: int,
    dados: FinalizarPedidoSchema,
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    pedido = db.get(PedidoModel, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado."
        )
    verificar_permissao_pedido(pedido, current_user)

    if pedido.status != StatusEnum.PENDENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pedido ja foi finalizado ou cancelado.",
        )
    if not pedido.itens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pedido vazio. Adicione itens antes de finalizar.",
        )

    pedido.endereco_entrega = dados.endereco_entrega
    pedido.forma_pagamento = dados.forma_pagamento
    pedido.troco_para = dados.troco_para
    pedido.observacao = dados.observacao
    pedido.telefone_contato = dados.telefone_contato
    pedido.status = StatusEnum.FINALIZADO
    db.commit()
    return {"message": "Pedido enviado para a cozinha!", "pedido_id": pedido.id}


@order_router.get("/meus_pedidos", response_model=list[PedidoSchemaResponse])
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


@order_router.get("/{pedido_id}", response_model=PedidoSchemaResponse)
async def detalhe_pedido(
    pedido_id: int,
    db: Session = Depends(make_session),
    current_user: UserModel = Depends(get_current_user),
):
    pedido = (
        db.query(PedidoModel)
        .options(joinedload(PedidoModel.itens))
        .filter(PedidoModel.id == pedido_id)
        .first()
    )
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado."
        )
    verificar_permissao_pedido(pedido, current_user)
    return pedido
