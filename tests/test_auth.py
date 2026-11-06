from uuid import uuid4

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def _criar_usuario_qa():
    email = f"qa_{uuid4().hex[:10]}@exemplo.com"
    senha = "Senha@123"
    nome = "QA Tester"

    resposta_cadastro = client.post(
        "/auth/signup", json={"nome": nome, "email": email, "senha": senha}
    )
    assert resposta_cadastro.status_code == 200

    resposta_login = client.post(
        "/auth/login", json={"email": email, "senha": senha}
    )
    assert resposta_login.status_code == 200

    return {
        "token": resposta_login.json()["access_token"],
        "refresh_token": resposta_login.json().get("refresh_token"),
        "email": email,
        "nome": nome,
        "senha": senha,
    }


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


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


# --- PATCH /auth/me (QA PR feat/perfil -> main) ---


def test_patch_me_sem_token():
    response = client.patch("/auth/me", json={"nome": "Nome Qualquer"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_patch_me_atualiza_so_nome():
    usuario = _criar_usuario_qa()
    response = client.patch(
        "/auth/me",
        json={"nome": "Nome Atualizado QA"},
        headers=_auth_headers(usuario["token"]),
    )

    assert response.status_code == 200
    assert response.json()["nome"] == "Nome Atualizado QA"
    assert response.json()["email"] == usuario["email"]


def test_patch_me_atualiza_so_email():
    usuario = _criar_usuario_qa()
    novo_email = f"novo_{uuid4().hex[:8]}@exemplo.com"

    response = client.patch(
        "/auth/me",
        json={"email": novo_email},
        headers=_auth_headers(usuario["token"]),
    )

    assert response.status_code == 200
    assert response.json()["email"] == novo_email
    assert response.json()["nome"] == usuario["nome"]


def test_patch_me_email_duplicado():
    usuario = _criar_usuario_qa()
    outro_usuario = _criar_usuario_qa()

    response = client.patch(
        "/auth/me",
        json={"email": outro_usuario["email"]},
        headers=_auth_headers(usuario["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Este e-mail já está cadastrado."

    dados_usuario = client.get(
        "/auth/me", headers=_auth_headers(usuario["token"])
    )
    assert dados_usuario.status_code == 200
    assert dados_usuario.json()["email"] == usuario["email"]


def test_patch_me_sem_campos_retorna_dados_inalterados():
    usuario = _criar_usuario_qa()

    response = client.patch(
        "/auth/me",
        json={},
        headers=_auth_headers(usuario["token"]),
    )

    assert response.status_code == 200
    assert response.json()["nome"] == usuario["nome"]
    assert response.json()["email"] == usuario["email"]
