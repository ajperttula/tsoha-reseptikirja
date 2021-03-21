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
    instruction = request.form["instruction"]
    ingredients = request.form.getlist("ingredient")
    tags = request.form.getlist("tag")
    sql = """INSERT INTO recipes (title, description, instruction) 
             VALUES (:title, :description, :instruction) RETURNING id"""
    recipe_id = db.session.execute(sql, {"title":title, "description":description, "instruction":instruction}).fetchone()[0]
    for i in ingredients:
        if i != "":
            sql = "INSERT INTO ingredients (recipe_id, ingredient) VALUES (:recipe_id, :i)"
            db.session.execute(sql, {"recipe_id":recipe_id, "i":i})
    for t in tags:
        if t != "":
            sql = "SELECT id FROM tags WHERE tag=:t"
            tag_id = db.session.execute(sql, {"t":t}).fetchone()[0]
            sql = "INSERT INTO recipetags (recipe_id, tag_id) VALUES (:recipe_id, :tag_id)"
            db.session.execute(sql, {"recipe_id":recipe_id, "tag_id":tag_id})
    db.session.commit()
    return redirect(f"/recipe/{recipe_id}")

@app.route("/recipe/<int:id>")
def recipe(id):
    sql = "SELECT title, description, instruction FROM recipes WHERE id=:id"    # kannattaisko hakea yhtenä hakuna?
    recipe = db.session.execute(sql, {"id":id}).fetchone()
    sql = "SELECT ingredient FROM ingredients WHERE recipe_id=:id"
    ingredients = db.session.execute(sql, {"id":id}).fetchall()
    return render_template("recipe.html", recipe=recipe, ingredients=ingredients)