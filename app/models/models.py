import enum
import os

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship

load_dotenv()

db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise ValueError("A variável DATABASE_URL não foi encontrada no arquivo .env")

engine = create_engine(db_url)
Base = declarative_base()


# ENUM DE CATEGORIAS
class CategoriaEnum(enum.Enum):
    PIZZA = "Pizza"
    BEBIDA = "Bebida"
    SOBREMESA = "Sobremesa"
    LANCHE = "Lanche"
    ACOMPANHAMENTO = "Acompanhamento"
    OUTROS = "Outros"


# ENUM DE STATUS
class StatusEnum(enum.Enum):
    PENDENTE = "Pendente"
    FINALIZADO = "Finalizado"
    CANCELADO = "Cancelado"


# TABELA DE ITENS DO CARDÁPIO
class ItemCardapio(Base):
    __tablename__ = "itens_cardapio"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    nome = Column(String(120), nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    preco = Column(Float, nullable=False)
    categoria = Column(Enum(CategoriaEnum), nullable=False, index=True)
    disponivel = Column(Boolean, default=True, nullable=False)
    imagem_url = Column(String(255), nullable=True)  # para mostrar foto no front


# TABELA DE USUÁRIOS
class UserModel(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    senha = Column(String(250), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    admin = Column(Boolean, nullable=False, default=False)
    pedidos = relationship("PedidoModel", back_populates="usuario")


# TABELA DE PEDIDOS
class PedidoModel(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.PENDENTE)
    preco = Column(Float, default=0.0, nullable=False)

    usuario = relationship("UserModel", back_populates="pedidos")
    itens = relationship(
        "ItemPedidoModel", cascade="all, delete-orphan", back_populates="pedido"
    )

    def adicionar_item_do_total(self, quantidade, preco_unitario):
        self.preco += quantidade * preco_unitario

    def subtrair_item_do_total(self, quantidade, preco_unitario):
        self.preco -= quantidade * preco_unitario


class ItemPedidoModel(Base):
    __tablename__ = "itens_pedidos"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)

   
    nome_snapshot = Column(String(100), nullable=False)  
    preco_unitario = Column(Float, nullable=False)      
    imagem_url_snapshot = Column(String, nullable=True) 

    quantidade = Column(Integer, nullable=False)
    sabor = Column(String(100), nullable=True) 
    tamanho = Column(String(100), nullable=True) 


    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    pedido = relationship("PedidoModel", back_populates="itens")


    item_cardapio_id = Column(Integer, ForeignKey("itens_cardapio.id"), nullable=True)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Todas as tabelas foram criadas com sucesso!")
    print("Tabelas criadas: usuario, pedidos, itens_pedidos, itens_cardapio")
