import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.database import Base, engine


# ENUM DE CATEGORIAS
class CategoriaEnum(str, enum.Enum):
    PIZZA = "Pizza"
    BEBIDA = "Bebida"
    SOBREMESA = "Sobremesa"
    LANCHE = "Lanche"
    ACOMPANHAMENTO = "Acompanhamento"
    OUTROS = "Outros"


# ENUM DE STATUS
class StatusEnum(str, enum.Enum):
    PENDENTE = "Pendente"
    FINALIZADO = "Finalizado"
    CANCELADO = "Cancelado"


# ENUM DE FORMA DE PAGAMENTO
class FormaPagamentoEnum(str, enum.Enum):
    DINHEIRO = "Dinheiro"
    CARTAO_CREDITO = "Cartão de Crédito"
    CARTAO_DEBITO = "Cartão de Débito"
    PIX = "Pix"
    VALE_ALIMENTACAO = "Vale Alimentação"


# ENUM DE TAMANHOS DE PIZZA
class TamanhoEnum(str, enum.Enum):
    PEQUENA = "pequena"
    MEDIA = "media"
    GRANDE = "grande"


# TABELA DE ITENS DO CARDÁPIO
class ItemCardapio(Base):
    __tablename__ = "itens_cardapio"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    nome = Column(String(120), nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    preco = Column(Numeric(10, 2), nullable=False)

    categoria = Column(
        Enum(
            CategoriaEnum,
            name="categoriaenum",
            create_type=False,
            values_callable=lambda x: [e.name for e in x],
        ),
        nullable=False,
        index=True,
    )
    disponivel = Column(Boolean, default=True, nullable=False)
    imagem_url = Column(String(255), nullable=True)

    precos_tamanho = relationship(
        "ItemTamanhoPreco",
        back_populates="item_cardapio",
        cascade="all, delete-orphan",
    )

    def preco_para_tamanho(self, tamanho):
        """Preço oficial da combinação sabor/tamanho.

        Levanta erro explícito quando a combinação não está configurada, em vez
        de recair em preço padrão ou multiplicador presumido.
        """
        tamanho_valor = tamanho.value if isinstance(tamanho, TamanhoEnum) else str(tamanho)
        for preco_tamanho in self.precos_tamanho:
            if preco_tamanho.tamanho == tamanho_valor:
                return preco_tamanho.preco
        raise ValueError(f"Preço não configurado para o item {self.id} no tamanho '{tamanho_valor}'.")


# TABELA DE PREÇOS POR TAMANHO (PIZZA = SABOR x TAMANHO)
class ItemTamanhoPreco(Base):
    """Preço próprio de cada combinação sabor do cardápio x tamanho."""

    __tablename__ = "itens_cardapio_precos_tamanho"
    __table_args__ = (
        UniqueConstraint(
            "item_cardapio_id",
            "tamanho",
            name="uq_itens_cardapio_precos_tamanho_item_tamanho",
        ),
        CheckConstraint(
            "tamanho IN ('pequena', 'media', 'grande')",
            name="ck_itens_cardapio_precos_tamanho_tamanho_valido",
        ),
        CheckConstraint(
            "preco > 0",
            name="ck_itens_cardapio_precos_tamanho_preco_positivo",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    item_cardapio_id = Column(
        Integer,
        ForeignKey("itens_cardapio.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tamanho = Column(String(10), nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)

    item_cardapio = relationship("ItemCardapio", back_populates="precos_tamanho")


# TABELA DE USUÁRIOS
class UserModel(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    senha = Column(String(250), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    admin = Column(Boolean, nullable=False, default=False)
    reset_code_hash = Column(String(64), nullable=True)
    reset_code_expires_at = Column(DateTime, nullable=True)
    reset_code_attempts = Column(Integer, default=0)
    pedidos = relationship("PedidoModel", back_populates="usuario")


# TABELA DE PEDIDOS
class PedidoModel(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)

    status = Column(
        Enum(
            StatusEnum,
            name="statusenum",
            create_type=False,
            values_callable=lambda x: [e.name for e in x],
        ),
        nullable=False,
        default=StatusEnum.PENDENTE,
    )

    preco = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    # Checkout fields
    endereco_entrega = Column(Text, nullable=True)
    forma_pagamento = Column(
        Enum(
            FormaPagamentoEnum,
            name="formapagamentoenum",
            create_type=False,
            values_callable=lambda x: [e.name for e in x],
        ),
        nullable=True,
    )
    troco_para = Column(Numeric(10, 2), nullable=True)
    observacao = Column(Text, nullable=True)
    telefone_contato = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    usuario = relationship("UserModel", back_populates="pedidos")
    itens = relationship("ItemPedidoModel", cascade="all, delete-orphan", back_populates="pedido")

    def adicionar_item_do_total(self, quantidade, preco_unitario):
        self.preco += quantidade * preco_unitario

    def subtrair_item_do_total(self, quantidade, preco_unitario):
        self.preco -= quantidade * preco_unitario


# TABELA DE ITENS DO PEDIDO
class ItemPedidoModel(Base):
    __tablename__ = "itens_pedidos"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)

    nome_snapshot = Column(String(100), nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    imagem_url_snapshot = Column(String, nullable=True)

    quantidade = Column(Integer, nullable=False)
    sabor = Column(String(100), nullable=True)
    tamanho = Column(String(100), nullable=True)

    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    pedido = relationship("PedidoModel", back_populates="itens")

    item_cardapio_id = Column(Integer, ForeignKey("itens_cardapio.id"), nullable=True)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Todas as tabelas foram sincronizadas com sucesso!")
    print("Tabelas verificadas: usuario, pedidos, itens_pedidos, itens_cardapio, itens_cardapio_precos_tamanho")
