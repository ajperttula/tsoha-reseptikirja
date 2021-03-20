from flask import Flask
from flask import render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")

db = SQLAlchemy(app)

@app.route("/")
def index():
    recipe_count = db.session.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    return render_template("index.html", recipe_count=recipe_count)

@app.route("/new-recipe")
def new_recipe():
    return render_template("new-recipe.html")

@app.route("/add", methods=["POST"])
def add():
    title = request.form["title"]
    description = request.form["description"]
    ingredients = request.form.getlist("ingredient")
    instruction = request.form["instruction"]
    sql = """INSERT INTO recipes (title, description, instruction) 
             VALUES (:title, :description, :instruction) RETURNING id"""
    recipe_id = db.session.execute(sql, {"title":title, "description":description, "instruction":instruction}).fetchone()[0]
    for i in ingredients:
        if i != "":
            sql = "INSERT INTO ingredients (recipe_id, name) VALUES (:recipe_id, :i)"
            db.session.execute(sql, {"recipe_id":recipe_id, "i":i})
    db.session.commit()
    return redirect("/")