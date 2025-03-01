import sqlalchemy as sq
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from model import init_db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bashproshop'
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
        login_user(user)
        return jsonify({'message': 'Logged in successfully'})
    return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route("/")
def index():
    return "Hello, World!"


if __name__ == "__main__":
    db = init_db(app)
    app.run(debug=True)
