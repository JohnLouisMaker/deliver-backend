from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_forgot_password_email_nao_encontrado():
    response = client.post(
        "/auth/forgot-password", json={"email": "naoexiste@email.com"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Email informado não está cadastrado"


def test_login_senha_invalida():
    response = client.post(
        "/auth/login",
        json={"email": "usuario@exemplo.com", "senha": "senha_errada"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


def test_loginform_senha_invalida():
    response = client.post(
        "/auth/loginform",
        data={"username": "usuario@exemplo.com", "password": "senha_errada"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


def test_me_sem_token():
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_refresh_sem_token():
    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_reset_password_usuario_nao_encontrado():
    response = client.post(
        "/auth/reset-password",
        json={
            "email": "naoexiste@email.com",
            "code": "123456",
            "reset_token": "token_qualquer",
            "new_password": "Nova@123",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado."
