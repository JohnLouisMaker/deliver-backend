from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


# --- USUÁRIO ---
class UserSchema(BaseModel):
    nome: str
    email: str
    senha: str
    ativo: Optional[bool] = True
    admin: Optional[bool] = False


# --- LOGIN ---
class LoginSchema(BaseModel):
    email: str
    senha: str


# --- ITENS DE PEDIDO ---
class ItemPedidoSchema(BaseModel):
    item_id: int
    quantidade: int
    sabor: Optional[str] = None 
    tamanho: Optional[str] = None 


class ItemPedidoSchemaResponse(BaseModel):
    id: int
    item_id: int
    quantidade: int
    sabor: str
    tamanho: str
    preco_unitario: float  

    model_config = ConfigDict(from_attributes=True)


# --- PEDIDO ---
class StatusSchema(str, Enum):
    FINALIZADO = "FINALIZADO"
    PENDENTE = "PENDENTE"
    CANCELADO = "CANCELADO"


class PedidoSchemaResponse(BaseModel):
    id: int
    usuario_id: int
    status: StatusSchema
    preco: float  # Preço total do pedido
    itens: List[ItemPedidoSchemaResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- CARDÁPIO --
class ItemCardapioCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    categoria: str