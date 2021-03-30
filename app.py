from flask import Flask
from flask import render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")

db = SQLAlchemy(app)

@app.route("/")
def index():
    recipe_count = db.session.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    return render_template("index.html", recipe_count=recipe_count)

@app.route("/new-recipe")
def new_recipe():
    return render_template("new-recipe.html")

@app.route("/add-recipe", methods=["POST"])
def add_recipe():
    title = request.form["title"]
    description = request.form["description"]
    instruction = request.form["instruction"]
    ingredients = request.form.getlist("ingredient")
    tags = request.form.getlist("tag")
    username = session["username"]
    sql = "SELECT id FROM users WHERE username=:username"
    creator_id = db.session.execute(sql, {"username":username}).fetchone()[0]
    sql = """INSERT INTO recipes (creator_id, title, description, instruction) 
             VALUES (:creator_id, :title, :description, :instruction) RETURNING id"""
    recipe_id = db.session.execute(sql, {"creator_id":creator_id, "title":title, "description":description, "instruction":instruction}).fetchone()[0]
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

@app.route("/new-user")
def new_user():
    return render_template("new-user.html")

@app.route("/create-user", methods=["POST"])
def create_user():
    username = request.form["username"]
    if len(username) < 3:
        return render_template("error.html", error="Antamasi käyttäjätunnus on liian lyhyt.")
    if len(username) > 20:
        return render_template("error.html", error="Antamasi käyttäjätunnus on liian pitkä.")
    password = request.form["password"]
    password_check = request.form["password_check"]
    if password != password_check:
        return render_template("error.html", error="Tarkista salasana.")
    if len(password) < 8:
        return render_template("error.html", error="Antamasi salasana on liian lyhyt.")
    if len(password) > 32:
        return render_template("error.html", error="Antamasi salasana on liian pitkä.")
    if password == password.lower() or password == password.upper():
        return render_template("error.html", error="Salasanan pitää sisältää pieniä ja suuria kirjaimia.")
    hash_value = generate_password_hash(password)
    sql = "INSERT INTO users (username, password, role) VALUES (:username, :hash_value, 0)"
    try:
        db.session.execute(sql, {"username":username, "hash_value":hash_value})
    except:
        return render_template("error.html", error="Käyttäjätunnus varattu.")
    db.session.commit()
    return redirect("/")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/check-login", methods=["POST"])
def check_login():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT password FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username}).fetchone()
    if result == None:
        return render_template("error.html", error="Käyttäjätunnusta ei löytynyt.")
    hash_value = result[0]
    if check_password_hash(hash_value, password):
        session["username"] = username
        return redirect("/")
    return render_template("error.html", error="Väärä salasana.")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")