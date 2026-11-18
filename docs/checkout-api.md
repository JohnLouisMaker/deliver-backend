# Contrato da API de checkout

Documento para o time de frontend (MORPH MOTH). Fonte de verdade do backend:
`app/routes/order_routes.py` e `app/schemas/schemas.py`.

## Autenticação

Todas as rotas abaixo exigem:

```
Authorization: Bearer <access_token>
```

### Renovação de sessão (refresh)

O refresh token **não vai no corpo**. Envie-o no header:

```
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

Resposta: `200` com `access_token`, `refresh_token`, `token_type` e `nome`.
Se o refresh token estiver expirado/inválido: `401` (``Token inválido ou expirado.``).

Fluxo recomendado no frontend: ao receber `401` em qualquer requisição autenticada,
chamar `/auth/refresh` uma vez com o header acima, guardar os novos tokens e repetir
a requisição original. O checkout não deve ser reenviado mais de uma vez.

## Checkout transacional

```
POST /pedidos
```

Alias mantido para compatibilidade (mesmo handler): `POST /pedidos/criar_pedido`.
O alias aparece fora da documentação interativa; use `POST /pedidos`.

Cria o pedido `PENDENTE` e todos os itens em uma única transação. Se qualquer item
ou dado for inválido, nada é persistido.

### Corpo da requisição

```json
{
  "itens": [
    { "item_cardapio_id": 1, "quantidade": 2, "tamanho": "media" },
    { "item_cardapio_id": 11, "quantidade": 1 }
  ],
  "endereco_entrega": "Rua das Pizzas, 123 - Apto 45",
  "forma_pagamento": "DINHEIRO",
  "telefone_contato": "11999998888",
  "troco_para": 200.0,
  "observacao": "Sem cebola"
}
```

Regras:

- `itens`: 1 ou mais itens; `quantidade` deve ser > 0.
- `tamanho`: `pequena`, `media` ou `grande`.
  - Obrigatório para itens que possuem preço por tamanho (pizzas).
  - Deve ser omitido para itens de preço fixo (bebidas, sobremesas etc.).
- `forma_pagamento`: `DINHEIRO`, `CARTAO_CREDITO`, `CARTAO_DEBITO`, `PIX` ou `VALE_ALIMENTACAO`.
- `troco_para`: obrigatório para `DINHEIRO` e deve ser maior ou igual ao total.
  Para as demais formas é ignorado.
- Qualquer campo de preço enviado no item (`preco`, `preco_unitario`, `total`) é
  **ignorado**: o backend recalcula pelos preços oficiais do banco.

### Resposta `201`

```json
{
  "pedido": {
    "id": 42,
    "status": "PENDENTE",
    "itens": [
      {
        "item_cardapio_id": 1,
        "nome_snapshot": "Marguerita Clássica",
        "tamanho": "media",
        "quantidade": 2,
        "preco_unitario": 54.9
      },
      {
        "item_cardapio_id": 11,
        "nome_snapshot": "Refrigerante Lata",
        "tamanho": null,
        "quantidade": 1,
        "preco_unitario": 7.5
      }
    ],
    "total": 117.3
  }
}
```

O identificador usado na tela de sucesso é `pedido.id`.

### Erros

| Código | Situação |
|---|---|
| `400` | Tamanho ausente para pizza, tamanho sem preço, tamanho em item fixo, produto indisponível, `troco_para` ausente/insuficiente para dinheiro |
| `401` | Não autenticado ou token expirado (renovar via `/auth/refresh`) |
| `404` | `item_cardapio_id` inexistente |
| `422` | Payload inválido (ex.: `quantidade` <= 0, `tamanho` fora do enum, campo obrigatório ausente) |
| `500` | Falha interna; transação revertida, nenhum pedido parcial criado |

## Cardápio com preços por tamanho (leitura)

`GET /cardapio/` (lista) e `GET /cardapio/{item_id}` (item individual) continuam
expondo `preco` base. Quando o item possui preços por tamanho cadastrados, a
resposta inclui também `precos_por_tamanho`:

```json
{
  "id": 1,
  "nome": "Marguerita Clássica",
  "preco": 54.9,
  "categoria": "Pizza",
  "disponivel": true,
  "imagem_url": "/static/uploads/marguerita-caseira.jpg",
  "precos_por_tamanho": [
    { "tamanho": "pequena", "preco": 39.9 },
    { "tamanho": "media", "preco": 54.9 },
    { "tamanho": "grande", "preco": 69.9 }
  ]
}
```

Itens sem preço por tamanho (ex.: bebidas) **não** trazem o campo — o frontend
deve exibir "preço a definir". Nenhum valor é inventado pelo backend.

## Adicionar item a um pedido pendente (fluxo incremental)

```
POST /pedidos/adicionar_item/{pedido_id}
Content-Type: application/json

{ "item_cardapio_id": 1, "quantidade": 1, "tamanho": "grande" }
```

As mesmas regras de preço/tamanho do checkout valem aqui. O preço unitário e o
total do pedido são recalculados no backend. Apenas o dono do pedido ou um admin
pode alterar, e somente com status `PENDENTE`.
