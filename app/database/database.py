import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("A variável DATABASE_URL não foi encontrada no arquivo .env")


engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()