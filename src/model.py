import os

import sqlalchemy as sq
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def init_db(app: Flask) -> SQLAlchemy:
    db_path = "sqlite:///" + \
        os.path.join(os.path.dirname(os.path.dirname(
            os.path.realpath(__file__))), "database.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_path
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return db


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    hashed_password: Mapped[str]
