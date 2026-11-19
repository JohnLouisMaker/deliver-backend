import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("A variável DATABASE_URL não foi encontrada no arquivo .env")


# pool_pre_ping valida a conexão antes de usar (o pooler do Supabase derruba
# conexões idle); pool_recycle renova conexões antigas antes de o pooler cortá-las.
engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
