from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_listar_cardapio():
    response = client.get("/cardapio/")

    assert response.status_code == 200


def test_buscar_item_nao_encontrado():
    response = client.get("/cardapio/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado."


def test_adicionar_item_sem_token():
    response = client.post("/cardapio/adicionar")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_editar_item_sem_token():
    response = client.patch("/cardapio/editar/1")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_deletar_item_sem_token():
    response = client.delete("/cardapio/deletar/1")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"