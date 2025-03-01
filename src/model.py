import os
from datetime import date, datetime
from typing import List, Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
DB_PATH = "sqlite:///" + \
    os.path.join(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__))), "database.db")


def init_db(app: Flask) -> SQLAlchemy:
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_PATH
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

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.hashed_password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.hashed_password, password)

    @classmethod
    def authenticate(cls, email, password):
        user = cls.query.filter_by(email=email).first()
        if user and user.verify_password(password):
            return user
        return None

    @staticmethod
    def get_by_id(id: int) -> 'User':
        return User.query.filter(User.id == id).first()

    def get_listings(self) -> List['Listing']:
        return Listing.query.filter(Listing.seller_id == self.id).all()

    @property
    def is_active(self):
        return True  # All users are active by default

    @property
    def is_authenticated(self):
        return True  # All users are authenticated when they exist

    @property
    def is_anonymous(self):
        return False  # Real users are not anonymous

    def get_id(self):
        return str(self.id)  # Convert to string as Flask-Login expects


class Listing(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    name: Mapped[str]
    description: Mapped[str]
    price: Mapped[float]
    post_date: Mapped[date]
    duration: Mapped[Optional[int]]

    @staticmethod
    # Condition isn't actually a type, but is of the form
    # MyClass.field == "value"
    def get_next(n: int, conditions: List['Condition'], orderings: List['Ordering']) -> List['Self']:
        return Listing.query.filter(*conditions).order_by(*orderings).limit(n).all()


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


def insert_test_data(db):
    """
    Insert predefined test data into the database.
    """
    users = [
        User(email="drew@example.com", first_name="drew",
             last_name="Jepsen", school="MIT"),
        User(email="jordan@example.com", first_name="jordan",
             last_name="Bourdeau", school="Harvard"),
        User(email="Levi@example.com", first_name="Levi",
             last_name="Pare", school="Stanford"),
        User(email="caroline@example.com", first_name="Caroline",
             last_name="Palecek", school=None),
        User(email="river@example.com", first_name="River",
             last_name="Bumpas", school="Berkeley"),
        User(email="surya@example.com", first_name="Surya",
             last_name="Malik", school="University of Vermont")
    ]

    for user in users:
        user.password = "password123"
        db.session.add(user)

    db.session.commit()

    listings = [
        Listing(
            seller_id=users[0].id,
            name="MacBook Pro 2022",
            description="Slightly used MacBook Pro, great condition",
            price=899.99,
            post_date=datetime.now().date(),
            duration=30
        ),
        Listing(
            seller_id=users[1].id,
            name="Calculus Textbook",
            description="Calculus: Early Transcendentals, 8th Edition",
            price=45.00,
            post_date=datetime.now().date(),
            duration=14
        ),
        Listing(
            seller_id=users[2].id,
            name="Desk Chair",
            description="Ergonomic office chair, black",
            price=75.50,
            post_date=datetime.now().date(),
            duration=7
        ),
        Listing(
            seller_id=users[0].id,
            name="iPhone 13",
            description="Like new iPhone 13, 128GB",
            price=550.00,
            post_date=datetime.now().date(),
            duration=14
        ),
        Listing(
            seller_id=users[3].id,
            name="Physics Notes",
            description="Complete Physics 101 notes",
            price=15.00,
            post_date=datetime.now().date(),
            duration=None
        ),
        Listing(
            seller_id=users[4].id,
            name="Mini Fridge",
            description="Perfect for dorm room",
            price=80.00,
            post_date=datetime.now().date(),
            duration=30
        ),
        Listing(
            seller_id=users[2].id,
            name="Scientific Calculator",
            description="TI-84 Plus, barely used",
            price=50.00,
            post_date=datetime.now().date(),
            duration=None
        ),
        Listing(
            seller_id=users[1].id,
            name="Desk Lamp",
            description="LED desk lamp with USB port",
            price=25.99,
            post_date=datetime.now().date(),
            duration=14
        ),
        Listing(
            seller_id=users[3].id,
            name="Chemistry Lab Coat",
            description="Size M, white lab coat",
            price=20.00,
            post_date=datetime.now().date(),
            duration=7
        ),
        Listing(
            seller_id=users[4].id,
            name="Laptop Stand",
            description="Adjustable aluminum laptop stand",
            price=35.50,
            post_date=datetime.now().date(),
            duration=None
        )
    ]

    for listing in listings:
        db.session.add(listing)

    db.session.commit()

