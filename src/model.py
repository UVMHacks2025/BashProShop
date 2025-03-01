import os
from datetime import date
from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer, LargeBinary, String
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
    school: Mapped[Optional[str]]
    first_name: Mapped[str]
    last_name: Mapped[str]
    hashed_password: Mapped[str]


class Listing(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    name: Mapped[str]
    description: Mapped[str]
    price: Mapped[float]
    post_date: Mapped[date]
    duration: Mapped[Optional[int]]


class Order(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    seller_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    date: Mapped[date]


class Interactions(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id"))
    interaction: Mapped[str]


class Categories(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id"))
    category: Mapped[str]


class Image(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id"))
    name: Mapped[str]
    encoded: Mapped[LargeBinary] = mapped_column(LargeBinary, nullable=False)
