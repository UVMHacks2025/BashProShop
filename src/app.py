
from flask import Flask

from model import init_db

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello, World!"


if __name__ == "__main__":
    db = init_db(app)
    app.run(debug=True)
