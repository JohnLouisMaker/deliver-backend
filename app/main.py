from app.routes.auth_routes import auth_router
from app.routes.order_routes import order_router
from app.routes.product_routes import product_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="API Python com FastAPI")

#  CONFIG CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://deliver-frontend-three.vercel.app",
        "https://deliver-frontend-git-main-john-louis-projects-2eeb8231.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# INCLUINDO ROTAS
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(order_router, prefix="/pedidos", tags=["orders"])
app.include_router(product_router, prefix="/cardapio", tags=["cardapio"])


# ROTA RAIZ
@app.get("/")
async def root():
    return {"message": "API Python com FastAPI!"}
