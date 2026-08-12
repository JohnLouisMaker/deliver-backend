# from fastapi.testclient import TestClient
# from sqlalchemy.orm import Session
# from app.main import app
# from app.dependencies import make_session

# client = TestClient(app)

# def test_orders():
#     with make_session() as Session:
#         response = client.get("/pedidos/")
#         assert response.status_code == 200