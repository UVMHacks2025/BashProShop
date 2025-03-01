import os
from datetime import timedelta

import sqlalchemy as sq
from flask import Flask, jsonify, render_template, request, session
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from model import DB_PATH, Listing, User, init_db, insert_test_data

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bashproshop'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if (request.method == 'POST'):
        data = request.get_json()
        user = User.authenticate(data.get('email'), data.get('password'))
        if user:
            # Get remember preference from request
            remember = data.get('remember', False)
            login_user(user, remember=remember)
            return jsonify({'message': 'Logged in successfully'})
        return jsonify({'message': 'Invalid email or password'}), 401
    if (request.method == 'GET'):
        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        school = request.form.get('school')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        if password != confirm_password:
            return jsonify({'message': 'Passwords do not match'}), 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'message': 'Email already registered'}), 400

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            school=school
        )
        user.password = password  #hash the password

        db.session.add(user)
        db.session.commit()

        login_user(user)
        return jsonify({'message': 'Signup successful'})

    if request.method == 'GET':
        return render_template("signup.html")


@app.route("/my-listings", methods=["GET"])
@login_required
def my_listings():
    return render_template("listings.html", listings=current_user.get_listings())


@app.route("/")
def listings():
    listings = Listing.get_next(10, [], [Listing.post_date])
    return render_template("listings.html", listings=listings)


@app.route("/create-listing", methods=['GET', 'POST'])
def createlisting():
    if (request.method == 'POST'):
        # retrieve data
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        images = request.files.getlist('images')

    if (request.method == 'GET'):
        return render_template("create_listing.html")


if __name__ == "__main__":

    with app.app_context():
        db = init_db(app)
        # Comment out after first run
        # insert_test_data(db=db)
        user = User.get_by_id(1)
        print(user)
        print(user.get_listings())
        print(Listing.get_next(10, [], [Listing.post_date]))

    app.run(debug=True)
