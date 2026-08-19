from enum import Enum

from pydantic import BaseModel, ConfigDict


# --- USUÁRIO ---
class UserSchema(BaseModel):
    nome: str
    email: str
    senha: str
    ativo: bool | None = True
    admin: bool | None = False


# --- LOGIN ---
class LoginSchema(BaseModel):
    email: str
    senha: str


class ForgetPasswordSchema(BaseModel):
    email: str


class ResetPasswordSchema(BaseModel):
    email: str
    code: str
    reset_token: str
    new_password: str


class VerifyResetCodeSchema(BaseModel):
    email: str
    code: str
    reset_token: str


# --- ITENS DE PEDIDO ---
class ItemPedidoSchema(BaseModel):
    item_id: int
    quantidade: int
    sabor: str | None = None
    tamanho: str | None = None


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
    itens: list[ItemPedidoSchemaResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- CARDÁPIO --
class ItemCardapioCreate(BaseModel):
    nome: str
    descricao: str | None = None
    preco: float
    categoria: str
