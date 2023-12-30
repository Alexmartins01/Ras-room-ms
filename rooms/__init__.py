from flask import Flask
from rooms.endpoints import bp
from dotenv import load_dotenv
from sqlalchemy import create_engine 

import os


def create_app():
    load_dotenv()

    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "default")

    DATABASE_URL = f'mysql+mysqldb://{db_user}:{db_password}@{db_host}:3306/{db_name}'

    # Create an engine
    engine = create_engine(DATABASE_URL, echo=True)

    app = Flask(__name__)
    app.engine = engine

    app.register_blueprint(bp)
    return app