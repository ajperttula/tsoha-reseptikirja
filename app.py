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
    recipes = db.session.execute("SELECT id, title FROM recipes WHERE visible=1 ORDER BY id DESC").fetchall()
    return render_template("index.html", recipes=recipes)

@app.route("/new-recipe")
def new_recipe():
    sql = "SELECT tag FROM tags"
    tags = db.session.execute(sql).fetchall()
    return render_template("new-recipe.html", tags=tags)

@app.route("/add-recipe", methods=["POST"])
def add_recipe():
    title = request.form["title"]
    description = request.form["description"]
    instruction = request.form["instruction"]
    ingredients = request.form.getlist("ingredient")
    tags = request.form.getlist("tag")
    creator_id = get_user_id()
    sql = """INSERT INTO recipes (creator_id, created_at, title, description, instruction, visible) 
             VALUES (:creator_id, NOW(), :title, :description, :instruction, 1) RETURNING id"""
    recipe_id = db.session.execute(sql, {"creator_id":creator_id, "title":title, "description":description, "instruction":instruction}).fetchone()[0]
    for i in ingredients:
        if i != "":
            sql = "INSERT INTO ingredients (recipe_id, ingredient, visible) VALUES (:recipe_id, :i, 1)"
            db.session.execute(sql, {"recipe_id":recipe_id, "i":i})
    for t in tags:
        if t != "":
            sql = "SELECT id FROM tags WHERE tag=:t"
            tag_id = db.session.execute(sql, {"t":t}).fetchone()[0]
            sql = "INSERT INTO recipetags (recipe_id, tag_id, visible) VALUES (:recipe_id, :tag_id, 1)"
            db.session.execute(sql, {"recipe_id":recipe_id, "tag_id":tag_id})
    db.session.commit()
    return redirect(f"/recipe/{recipe_id}")

@app.route("/recipe/<int:id>")
def recipe(id):
    sql = "SELECT visible FROM recipes WHERE id=:id"
    result = db.session.execute(sql, {"id":id}).fetchone()
    if not result or result[0] == 0:
        return render_template("error.html", error="Reseptiä ei löytynyt")
    sql = "SELECT * FROM recipes WHERE id=:id"    # kannattaisko hakea yhtenä hakuna?
    recipe = db.session.execute(sql, {"id":id}).fetchone()
    creator_id = recipe[1]
    sql = "SELECT username FROM users WHERE id=:creator_id"
    creator = db.session.execute(sql, {"creator_id":creator_id}).fetchone()[0]
    sql = "SELECT T.tag FROM tags T, recipetags R WHERE R.recipe_id=:id AND T.id=R.tag_id AND R.visible=1"
    tags = db.session.execute(sql, {"id":id}).fetchall()
    sql = "SELECT ingredient FROM ingredients WHERE recipe_id=:id"
    ingredients = db.session.execute(sql, {"id":id}).fetchall()
    sql = """SELECT U.username, C.comment, C.sent_at FROM users U, comments C 
             WHERE U.id=C.sender_id AND C.recipe_id=:id ORDER BY C.sent_at"""
    comments = db.session.execute(sql, {"id":id}).fetchall()
    if get_user_id() == creator_id:
        own_recipe = True
    else:
        own_recipe = False
    return render_template("recipe.html", creator=creator, recipe=recipe, tags=tags, ingredients=ingredients, comments=comments, own_recipe=own_recipe)

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
    sql = "INSERT INTO users (username, password, role, visible) VALUES (:username, :hash_value, 0, 1)"
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
    sql = "SELECT password, visible FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username}).fetchone()
    if result == None or result[1] == 0:
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

@app.route("/add-comment", methods=["POST"])
def add_comment():
    recipe_id = request.form["recipe_id"]
    sender_id = get_user_id()
    comment = request.form["comment"]
    if len(comment) == 0:
        return render_template("error.html", error="Kommentti on tyhjä.")
    if len(comment) > 1000:
        return render_template("error.html", error="Kommentti on liian pitkä.")
    sql = """INSERT INTO comments (recipe_id, sender_id, comment, sent_at, visible) 
             VALUES (:recipe_id, :sender_id, :comment, NOW(), 1)"""
    db.session.execute(sql, {"recipe_id":recipe_id, "sender_id":sender_id, "comment":comment})
    db.session.commit()
    return redirect(f"recipe/{recipe_id}")

@app.route("/grade-recipe", methods=["POST"])
def grade_recipe():
    recipe_id = request.form["recipe_id"]
    grade = request.form["grade"]
    sql = "INSERT INTO grades (recipe_id, grade, visible) VALUES (:recipe_id, :grade, 1)"
    db.session.execute(sql, {"recipe_id":recipe_id, "grade":grade})
    db.session.commit()
    return redirect(f"recipe/{recipe_id}")

@app.route("/search")
def search():
    keyword = "%" + request.args["keyword"].lower() + "%"
    sql = """SELECT DISTINCT R.id, R.title FROM recipes R, ingredients I WHERE R.id=I.recipe_id AND 
             R.visible=1 AND (LOWER(R.title) LIKE :keyword OR LOWER(R.description) LIKE :keyword OR 
             LOWER(R.instruction) LIKE :keyword OR LOWER(I.ingredient) LIKE :keyword)"""
    results = db.session.execute(sql, {"keyword":keyword}).fetchall()
    return render_template("result.html", results=results)

@app.route("/delete-recipe", methods=["POST"])
def delete_recipe():
    recipe_id = request.form["recipe_id"]
    creator_id = request.form["creator_id"]
    if get_user_id() != int(creator_id):
        return render_template("error.html", error="Toiminto ei ole sallittu.")
    sql = "UPDATE recipes SET visible=0 WHERE id=:recipe_id"
    db.session.execute(sql, {"recipe_id":recipe_id})
    sql = "UPDATE ingredients SET visible=0 WHERE recipe_id=:recipe_id"
    db.session.execute(sql, {"recipe_id":recipe_id})
    sql = "UPDATE recipetags SET visible=0 WHERE recipe_id=:recipe_id"
    db.session.execute(sql, {"recipe_id":recipe_id})
    sql = "UPDATE comments SET visible=0 WHERE recipe_id=:recipe_id"
    db.session.execute(sql, {"recipe_id":recipe_id})
    sql = "UPDATE grades SET visible=0 WHERE recipe_id=:recipe_id"
    db.session.execute(sql, {"recipe_id":recipe_id})
    db.session.commit()
    return redirect("/")

def get_user_id():
    try:
        username = session["username"]
    except:
        return None
    sql = "SELECT id FROM users WHERE username=:username"
    return db.session.execute(sql, {"username":username}).fetchone()[0]