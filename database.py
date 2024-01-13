from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

import os
from dotenv import load_dotenv
BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, 'config.env'))

# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
db_name=os.getenv("DATABASE")
db_user=os.getenv("DBUSER")
db_pass=os.getenv("DBPASS")
SQLALCHEMY_DATABASE_URL = f'mysql+mysqlconnector://{db_user}:{quote_plus(db_pass)}@localhost:3306/{db_name}'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL 
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
