import base64
import os
from datetime import date, datetime, timedelta

import sqlalchemy as sq
import stripe
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from model import DB_PATH, Image, Listing, User, init_db, insert_test_data
from stripe_handler import StripeHandler

app = Flask(__name__)
app.config["SECRET_KEY"] = "bashproshop"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=7)

login_manager = LoginManager()
login_manager.init_app(app)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = (
            request.form.get("remember") == "on"
        )  # Convert checkbox value to boolean

        user = User.authenticate(email, password)
        if user:
            login_user(user, remember=remember)
            return redirect("/")
        return render_template("login.html", message="Invalid email or password")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        email = request.form.get("email")
        school = request.form.get("school")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        if password != confirm_password:
            return render_template("signup.html", message="Passwords do not match")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template("signup.html", message="Email already registered")

        user = User(
            email=email, first_name=first_name, last_name=last_name, school=school
        )
        user.password = password  # hash the password

        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect()
    if request.method == "GET":
        return render_template("signup.html")


@app.route("/my-listings", methods=["GET"])
@login_required
def my_listings():
    listings = Listing.get_next(0, 100, [], [Listing.post_date])
    listings = Listing.get_next(0, 100, [], [Listing.post_date])
    for listing in listings:
        images = Image.get_for(listing)
        if images:
            listing.imgsrc = f"data:image/;base64,{
                images[0].encoded.decode('utf-8')}"
    return render_template("my_listings.html", listings=current_user.get_listings())


@app.route("/")
def listings():
    search = request.args.get("search")
    free = request.args.get("free", "off")
    min_price = request.args.get("min-price")
    max_price = request.args.get("max-price")

    if not min_price:
        min_price = 0

    if not max_price:
        max_price = float("inf")

    filters = [
        Listing.seller_id != current_user.get_id(),
        Listing.price.between(min_price, max_price),
    ]

    if free == "off":
        filters.append(Listing.price != 0)

    if search:
        filters.append(Listing.name.contains(search))

    listings = Listing.get_next(0,
                                100,
                                filters,
                                [Listing.post_date],
                                )

    for listing in listings:
        images = Image.get_for(listing)
        if images:
            listing.imgsrc = f"data:image/;base64,{
                images[0].encoded.decode('utf-8')}"

    return render_template("listings.html", listings=listings)


@app.route("/create_checkout_session", methods=["POST"])
def checkout_session():
    handler = StripeHandler()
    return handler.create_checkout_session()


@app.route("/payment_success", methods=["GET"])
def payment_success():
    return render_template("payment_success.html")


@app.route("/payment_cancel", methods=["GET"])
def payment_cancel():
    return render_template("payment_cancel.html")


@app.route("/create-listing", methods=['GET', 'POST'])
@login_required
def createlisting():
    if request.method == "POST":
        # retrieve data
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        listing_type = request.form.get(
            "listingType")  # "selling" or "renting"
        start_date = (
            request.form.get(
                "startDate") if listing_type == "renting" else None
        )
        duration = request.form.get(
            "duration") if listing_type == "renting" else None
        images = request.files.getlist("images")

        # make sure user entered all fields
        if not name or not description or not price or not images:
            return jsonify({"message": "All fields are required"}), 400

        # validate price
        try:
            price = float(price)
            if price < 0:
                return jsonify({"message": "Price cannot be less than 0"}), 400
        except ValueError:
            return jsonify({"message": "Invalid price"}), 400

        # validate renting information
        if listing_type == "renting":
            if not start_date or not duration:
                return (
                    jsonify(
                        {"message": "Start date and duration are required for rentals"}
                    ),
                    400,
                )
            try:
                duration = int(duration)
                if duration <= 0:
                    return (
                        jsonify(
                            {"message": "Duration must be a positive integer"}),
                        400,
                    )
            except ValueError:
                return jsonify({'message': 'Invalid duration'}), 400

        with app.app_context():
            new_listing = Listing(
                seller_id=current_user.id,
                name=name,
                description=description,
                price=price,
                post_date=date.today(),
                duration=duration if duration else None,
                start_date=datetime.strptime(
                    start_date, '%Y-%m-%d') if start_date else None
            )

            db.session.add(new_listing)
            db.session.commit()

            listing_id = new_listing.id
            for image in images:
                if image:
                    image_string = base64.b64encode(image.read())
                    new_image = Image(
                        listing_id=listing_id,
                        name=image.filename,
                        encoded=image_string
                    )
                    db.session.add(new_image)
            db.session.commit()
            return redirect('/my-listings')

    if request.method == "GET":
        return render_template("create_listing.html")


@app.route("/listing-detail")
def listing_detail():
    listing_id = request.args.get('id')
    listing = Listing.query.get_or_404(listing_id)

    images = Image.query.filter_by(listing_id=listing_id).all()
    return render_template("listing_detail.html", listing=listing, images=images)


@app.route('/checkout')
@login_required
def checkout():
    listing_id = request.args.get('id')
    listing = Listing.query.get_or_404(listing_id)

    if listing.seller_id == current_user.id:
        return render_template('listing_detail.html',
                               listing=listing,
                               message='You cannot purchase your own listing')

    return render_template('checkout.html', listing=listing)


if __name__ == "__main__":

    with app.app_context():
        db = init_db(app)
        # Comment out after first run
        # insert_test_data(db=db)
        user = User.get_by_id(1)
        print(user)
        print(user.get_listings())
        print(Listing.get_next(0, 5, [], [Listing.post_date]))
        print(Listing.get_next(1, 5, [], [Listing.post_date]))

    app.run(debug=True)
