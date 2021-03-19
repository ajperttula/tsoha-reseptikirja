from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")

db = SQLAlchemy(app)

@app.route("/")
def index():
    recipe_count = db.session.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    return render_template("index.html", recipe_count=recipe_count)