from app.database.database import SessionLocal, engine
from app.database.product import CATALOGO_PADRAO
from app.models.models import Base, ItemCardapio


def seed_db():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if db.query(ItemCardapio).count() > 0:
            print("CARDÁPIO JÁ EXISTENTE - Nenhuma alteração feita.")
            return

        print("Semeando o cardápio no banco de dados...")
        try:
            novos_itens = [ItemCardapio(**item) for item in CATALOGO_PADRAO]
            db.add_all(novos_itens)
            db.commit()
            print(f"{len(novos_itens)} itens inseridos com sucesso!")
        except Exception as e:
            db.rollback()
            print(f"Erro ao semear banco: {e}")


if __name__ == "__main__":
    seed_db()