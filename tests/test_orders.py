from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_criar_pedido_sem_token():
    response = client.post("/pedidos/criar_pedido")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_adicionar_item_pedido_sem_token():
    response = client.post("/pedidos/adicionar_item/1?item_cardapio_id=1&quantidade=1")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_remover_item_sem_token():
    response = client.delete("/pedidos/remover_item/1/1")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_finalizar_pedido_sem_token():
    response = client.post("/pedidos/finalizar/1")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_listar_meus_pedidos_sem_token():
    response = client.get("/pedidos/meus_pedidos")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"