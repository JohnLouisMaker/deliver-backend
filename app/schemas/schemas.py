from enum import Enum

from app.models.models import FormaPagamentoEnum
from pydantic import BaseModel, ConfigDict


# --- USUÁRIO ---
class UserSchema(BaseModel):
    nome: str
    email: str
    senha: str
    ativo: bool | None = True
    admin: bool | None = False


# --- USUÁRIO SIGNUP ---
class UserSignUpSchema(BaseModel):
    nome: str
    email: str
    senha: str


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
    preco: float
    endereco_entrega: str | None = None
    forma_pagamento: FormaPagamentoEnum | None = None
    troco_para: float | None = None
    observacao: str | None = None
    telefone_contato: str | None = None
    created_at: str | None = None
    itens: list[ItemPedidoSchemaResponse] = []

    model_config = ConfigDict(from_attributes=True)


class FinalizarPedidoSchema(BaseModel):
    endereco_entrega: str
    forma_pagamento: FormaPagamentoEnum
    troco_para: float | None = None
    observacao: str | None = None
    telefone_contato: str | None = None


# --- CARDÁPIO --
class ItemCardapioCreate(BaseModel):
    nome: str
    descricao: str | None = None
    preco: float
    categoria: str
