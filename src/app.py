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


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.authenticate(data.get('email'), data.get('password'))
    if user:
        # Get remember preference from request
        remember = data.get('remember', False)
        login_user(user, remember=remember)
        return jsonify({'message': 'Logged in successfully'})
    return jsonify({'message': 'Invalid email or password'}), 401


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/")
def listings():
    listings = Listing.get_next(10, [], [Listing.post_date])
    return render_template("listings.html", listings=listings)

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    event = None
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET"))
    except ValueError as e:
        # Invalid payload
        return jsonify({"error": "Invalid payload" + str(e)}), 400
    except StripeError as e:
        # Invalid signature
        return jsonify({"error": "Invalid signature" + str(e)}), 400
    
    # Handle the event
    if event.type == "checkout.session.completed":
        session = event["data"]["object"]
        if session is not None and isinstance(session, dict):
            # Fulfill the purchase
            stripe_handler = StripeHandler()
            stripe_handler.handle_payment(session)
            print(f"Payment successful for session: {session["id"]}")
    return jsonify({"status": "success"}), 200
    


@app.route("/create-listing")
def createlisting():
    return render_template("create_listing.html")

if __name__ == "__main__":
    db = init_db(app)
    # Comment out after first run
    with app.app_context():
        db = init_db(app)
        # insert_test_data(db)
        user = User.get_by_id(1)
        print(user)
        print(user.get_listings())
        print(Listing.get_next(0, 5, [], [Listing.post_date]))
        print(Listing.get_next(1, 5, [], [Listing.post_date]))

    app.run(debug=True)
