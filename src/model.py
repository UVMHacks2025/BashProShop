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


def get_db() -> SQLAlchemy:
    return db


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
        return User.query.filter(User.id == id).first()  # type: ignore

    def get_listings(self) -> List['Listing']:
        return Listing.query.filter(Listing.seller_id == self.id).all()

    def get_cart_items(self) -> List['CartItem']:
        return CartItem.query.filter(CartItem.client_id == self.id).all()

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
    start_date: Mapped[Optional[date]]

    seller = db.relationship('User', backref='listings')
    images = db.relationship('Image', backref='listing')

    @staticmethod
    # Condition isn't actually a type, but is of the form
    # MyClass.field == "value"
    def get_next(
        page: int = 0,
        page_size: int = 20,
        conditions: List['Condition'] = [],  # type: ignore
        orderings: List['Ordering'] = []  # type: ignore
    ) -> List['Self']:  # type: ignore
        return Listing.query \
            .filter(*conditions) \
            .order_by(*orderings) \
            .offset(page * page_size) \
            .limit(page_size) \
            .all()


class Order(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    seller_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    date: Mapped[date]


class CartItem(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id"))


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

    @staticmethod
    def get_for(listing: Listing) -> List['Self']:
        return Image.query \
            .filter(Image.listing_id == listing.id) \
            .all()


def insert_test_data(db):
    """
    Insert predefined test data into the database.
    """
    users = [
        User(email="drew@example.com", first_name="drew",  # type: ignore
             last_name="Jepsen", school="MIT"),  # type: ignore
        User(email="jordan@example.com", first_name="jordan",  # type: ignore
             last_name="Bourdeau", school="Harvard"),  # type: ignore
        User(email="Levi@example.com", first_name="Levi",  # type: ignore
             last_name="Pare", school="Stanford"),  # type: ignore
        User(email="caroline@example.com", first_name="Caroline",  # type: ignore
             last_name="Palecek", school=None),  # type: ignore
        User(email="river@example.com", first_name="River",  # type: ignore
             last_name="Bumpas", school="Berkeley"),  # type: ignore
        User(email="surya@example.com", first_name="Surya",  # type: ignore
             last_name="Malik", school="University of Vermont")  # type: ignore
    ]

    for user in users:
        user.password = "password123"
        db.session.add(user)

    db.session.commit()

    listings = [
        Listing(
            seller_id=users[0].id,  # type: ignore
            name="MacBook Pro 2022",  # type: ignore
            description="Slightly used MacBook Pro, great condition",  # type: ignore
            price=899.99,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=30  # type: ignore
        ),
        Listing(
            seller_id=users[1].id,  # type: ignore
            name="Calculus Textbook",  # type: ignore
            description="Calculus: Early Transcendentals, 8th Edition",  # type: ignore
            price=45.00,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=14  # type: ignore
        ),
        Listing(
            seller_id=users[2].id,  # type: ignore
            name="Desk Chair",  # type: ignore
            description="Ergonomic office chair, black",  # type: ignore
            price=75.50,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=7  # type: ignore
        ),
        Listing(
            seller_id=users[0].id,  # type: ignore
            name="iPhone 13",  # type: ignore
            description="Like new iPhone 13, 128GB",  # type: ignore
            price=550.00,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=14  # type: ignore
        ),
        Listing(
            seller_id=users[3].id,  # type: ignore
            name="Physics Notes",  # type: ignore
            description="Complete Physics 101 notes",  # type: ignore
            price=15.00,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=None  # type: ignore
        ),
        Listing(
            seller_id=users[4].id,  # type: ignore
            name="Mini Fridge",  # type: ignore
            description="Perfect for dorm room",  # type: ignore
            price=80.00,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=30  # type: ignore
        ),
        Listing(
            seller_id=users[2].id,  # type: ignore
            name="Scientific Calculator",  # type: ignore
            description="TI-84 Plus, barely used",  # type: ignore
            price=50.00,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=None  # type: ignore
        ),
        Listing(
            seller_id=users[1].id,  # type: ignore
            name="Desk Lamp",  # type: ignore
            description="LED desk lamp with USB port",  # type: ignore
            price=25.99,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=14  # type: ignore
        ),
        Listing(
            seller_id=users[3].id,  # type: ignore
            name="Chemistry Lab Coat",  # type: ignore
            description="Size M, white lab coat",  # type: ignore
            price=20.00,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=7  # type: ignore
        ),
        Listing(
            seller_id=users[4].id,  # type: ignore
            name="Laptop Stand",  # type: ignore
            description="Adjustable aluminum laptop stand",  # type: ignore
            price=35.50,  # type: ignore
            post_date=datetime.now().date(),  # type: ignore
            duration=None  # type: ignore
        )
    ]

    for listing in listings:
        db.session.add(listing)

    db.session.commit()
