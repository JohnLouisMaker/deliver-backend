from decimal import Decimal

from app.database.database import SessionLocal, engine
from app.database.product import CATALOGO_PADRAO, PRECOS_TAMANHO_PADRAO
from app.models.models import (
    Base,
    ItemCardapio,
    ItemTamanhoPreco,
    TamanhoEnum,
)


def _semear_precos_tamanho(db) -> int:
    """Insere os preços por tamanho que ainda não existem (idempotente)."""
    inseridos = 0
    for nome, precos in PRECOS_TAMANHO_PADRAO.items():
        item = db.query(ItemCardapio).filter(ItemCardapio.nome == nome).first()
        if item is None:
            print(f"Item '{nome}' não encontrado - preços de tamanho ignorados.")
            continue

        ja_configurados = {preco_tamanho.tamanho for preco_tamanho in item.precos_tamanho}
        for tamanho, valor in precos.items():
            if tamanho in ja_configurados:
                continue
            db.add(
                ItemTamanhoPreco(
                    item_cardapio_id=item.id,
                    tamanho=TamanhoEnum(tamanho).value,
                    preco=Decimal(valor),
                )
            )
            inseridos += 1
    return inseridos


def seed_db():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        try:
            if db.query(ItemCardapio).count() == 0:
                print("Semeando o cardápio no banco de dados...")
                db.add_all(ItemCardapio(**item) for item in CATALOGO_PADRAO)
                db.flush()
                print(f"{len(CATALOGO_PADRAO)} itens inseridos com sucesso!")
            else:
                print("CARDÁPIO JÁ EXISTENTE - nenhum item alterado.")

            inseridos = _semear_precos_tamanho(db)
            db.commit()
            print(f"{inseridos} preços por tamanho inseridos com sucesso!")
        except Exception as e:
            db.rollback()
            print(f"Erro ao semear banco: {e}")


if __name__ == "__main__":
    seed_db()
