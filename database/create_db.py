import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from models import Base   

load_dotenv()  

url = os.getenv("DATABASE_URL")

if(not url):
    raise ValueError("Нет DATABASE_URL в env")
else:
    engine = create_engine(url, echo=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)