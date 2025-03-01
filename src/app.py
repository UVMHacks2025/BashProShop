import os
from datetime import timedelta

import sqlalchemy as sq
from flask import Flask, jsonify, request, session, render_template
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
    if (request.method == 'POST'):
        data = request.get_json()
        print(data)
    if (request.method == 'GET'):
        return render_template("signup.html")

@app.route("/")
def listings():
    return render_template("listings.html")


@app.route("/create-listing")
def createlisting():
    return render_template("create_listing.html")

if __name__ == "__main__":
    db = init_db(app)
    # Comment out after first run
    # insert_test_data()

    with app.app_context():
        user = User.get_by_id(1)
        print(user)
        print(user.get_listings())
        print(Listing.get_next(10, [], [Listing.post_date]))

    app.run(debug=True)
