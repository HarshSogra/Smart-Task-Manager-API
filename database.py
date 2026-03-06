from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

#create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

#session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base model
Base = declarative_base()


