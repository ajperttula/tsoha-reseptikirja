from app import app
from flask import render_template, request, redirect, session
from os import urandom
from werkzeug.security import check_password_hash, generate_password_hash
from db import db

@app.route("/")
def index():
    recipes = db.session.execute("SELECT id, title FROM recipes WHERE visible=1 ORDER BY id DESC").fetchall()
    return render_template("index.html", recipes=recipes)

@app.route("/add-recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "GET":
        sql = "SELECT id, tag FROM tags"
        tags = db.session.execute(sql).fetchall()
        return render_template("new-recipe.html", tags=tags)
    if request.method == "POST":
        csrf_check(request.form["csrf_token"])
        title = request.form["title"]
        description = request.form["description"]
        instruction = request.form["instruction"]
        ingredients = request.form.getlist("ingredient")
        tags = request.form.getlist("tag")
        check_recipe_inputs(title, description, instruction, ingredients)
        creator_id = get_user_id()
        sql = """INSERT INTO recipes (creator_id, created_at, title, description, instruction, visible) 
                 VALUES (:creator_id, NOW(), :title, :description, :instruction, 1) RETURNING id"""
        try:
            recipe_id = db.session.execute(sql, {"creator_id":creator_id, "title":title, "description":description, "instruction":instruction}).fetchone()[0]
        except:
            return render_template("error.html", error="Otsikko on jo käytössä toisessa reseptissä.")
        for i in ingredients:
            if i != "":
                sql = "INSERT INTO ingredients (recipe_id, ingredient, visible) VALUES (:recipe_id, :i, 1)"
                db.session.execute(sql, {"recipe_id":recipe_id, "i":i})
        for t in tags:
            if t != "":
                sql = "INSERT INTO recipetags (recipe_id, tag_id, visible) VALUES (:recipe_id, :t, 1)"
                db.session.execute(sql, {"recipe_id":recipe_id, "t":t})
        db.session.commit()
        return redirect(f"/recipe/{recipe_id}")

@app.route("/modify-recipe", methods=["POST"])
def modify_recipe():
    csrf_check(request.form["csrf_token"])
    title = request.form["title"]
    recipe_id = request.form["recipe_id"]
    description = request.form["description"]
    instruction = request.form["instruction"]
    ingredients = request.form.getlist("ingredient")
    recipetags = request.form.getlist("recipetag")
    sql = "SELECT id, tag FROM tags"
    tags = db.session.execute(sql).fetchall()
    return render_template("modify-recipe.html", recipe_id=recipe_id, title=title, description=description, ingredients=ingredients, instruction=instruction, tags=tags, recipetags=recipetags)

@app.route("/execute-modification", methods=["POST"])
def execute_modification():
    csrf_check(request.form["csrf_token"])
    recipe_id = request.form["recipe_id"]
    title = request.form["title"]
    description = request.form["description"]
    instruction = request.form["instruction"]
    ingredients = request.form.getlist("ingredient")
    tags = request.form.getlist("tag")
    check_recipe_inputs(title, description, instruction, ingredients)

    sql = "UPDATE recipes SET title=:title, description=:description, instruction=:instruction WHERE id=:recipe_id"
    try:
        db.session.execute(sql, {"title":title, "description":description, "instruction":instruction, "recipe_id":recipe_id})
    except:
        return render_template("error.html", error="Otsikko on jo käytössä toisessa reseptissä.")

    sql = "SELECT id FROM ingredients WHERE recipe_id=:recipe_id AND visible=1"
    old_ingredients = db.session.execute(sql, {"recipe_id":recipe_id}).fetchall()
    new_ingredients = [i for i in ingredients if i != ""]
    for i in range(min(len(old_ingredients), len(new_ingredients))):
        id = old_ingredients.pop(0)[0]
        ingredient = new_ingredients.pop(0)
        sql = "UPDATE ingredients SET ingredient=:ingredient WHERE id=:id"
        db.session.execute(sql, {"ingredient":ingredient, "id":id})
    if old_ingredients:
        for i in old_ingredients:
            id = i[0]
            sql = "UPDATE ingredients SET visible=0 WHERE id=:id"
            db.session.execute(sql, {"id":id})
    else:
        for i in new_ingredients:
            sql = "INSERT INTO ingredients (recipe_id, ingredient, visible) VALUES (:recipe_id, :i, 1)"
            db.session.execute(sql, {"recipe_id":recipe_id, "i":i})

    sql = "SELECT tag_id, visible FROM recipetags WHERE recipe_id=:recipe_id"
    result = db.session.execute(sql, {"recipe_id":recipe_id}).fetchall()
    old_tags = [t[0] for t in result if t[1] == 1]
    removed_tags = [t[0] for t in result if t[1] == 0]
    new_tags = [int(t) for t in tags if t != ""]
    for t in new_tags:
        if t in removed_tags:
            sql = "UPDATE recipetags SET visible=1 WHERE recipe_id=:recipe_id AND tag_id=:t"
            db.session.execute(sql, {"recipe_id":recipe_id, "t":t})
        elif t not in old_tags[:]:
            sql = "INSERT INTO recipetags (recipe_id, tag_id, visible) VALUES (:recipe_id, :t, 1)"
            db.session.execute(sql, {"recipe_id":recipe_id, "t":t})
        else:
            old_tags.remove(t)
    if old_tags:
        for t in old_tags:
            sql = "UPDATE recipetags SET visible=0 WHERE recipe_id=:recipe_id AND tag_id=:t"
            db.session.execute(sql, {"recipe_id":recipe_id, "t":t})

    db.session.commit()
    return redirect(f"/recipe/{recipe_id}")

@app.route("/grade-recipe", methods=["POST"])
def grade_recipe():
    csrf_check(request.form["csrf_token"])
    recipe_id = request.form["recipe_id"]
    grade = request.form["grade"]
    sql = "INSERT INTO grades (recipe_id, grade, visible) VALUES (:recipe_id, :grade, 1)"
    db.session.execute(sql, {"recipe_id":recipe_id, "grade":grade})
    db.session.commit()
    return redirect(f"recipe/{recipe_id}")

@app.route("/add-comment", methods=["POST"])
def add_comment():
    csrf_check(request.form["csrf_token"])
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

@app.route("/search")
def search():
    keyword = "%" + request.args["keyword"].lower() + "%"
    sql = """SELECT DISTINCT R.id, R.title FROM recipes R, ingredients I WHERE R.id=I.recipe_id AND 
             R.visible=1 AND (LOWER(R.title) LIKE :keyword OR LOWER(R.description) LIKE :keyword OR 
             LOWER(R.instruction) LIKE :keyword OR LOWER(I.ingredient) LIKE :keyword)"""
    results = db.session.execute(sql, {"keyword":keyword}).fetchall()
    return render_template("result.html", results=results)

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
    sql = "SELECT ingredient FROM ingredients WHERE recipe_id=:id AND visible=1"
    ingredients = db.session.execute(sql, {"id":id}).fetchall()
    sql = """SELECT U.username, C.comment, C.sent_at FROM users U, comments C 
             WHERE U.id=C.sender_id AND C.recipe_id=:id ORDER BY C.sent_at"""
    comments = db.session.execute(sql, {"id":id}).fetchall()
    if get_user_id() == creator_id:
        own_recipe = True
    else:
        own_recipe = False
    return render_template("recipe.html", creator=creator, recipe=recipe, tags=tags, ingredients=ingredients, comments=comments, own_recipe=own_recipe)

@app.route("/delete-recipe", methods=["POST"])
def delete_recipe():
    csrf_check(request.form["csrf_token"])
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

@app.route("/create-user", methods=["GET", "POST"])
def create_user():
    if request.method == "GET":
        return render_template("new-user.html")
    if request.method == "POST":
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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        sql = "SELECT password, visible FROM users WHERE username=:username"
        result = db.session.execute(sql, {"username":username}).fetchone()
        if result == None or result[1] == 0:
            return render_template("error.html", error="Käyttäjätunnusta ei löytynyt.")
        hash_value = result[0]
        if check_password_hash(hash_value, password):
            session["username"] = username
            session["csrf_token"] = urandom(16).hex()
            return redirect("/")
        return render_template("error.html", error="Väärä salasana.")

@app.route("/logout")
def logout():
    del session["username"]
    del session["csrf_token"]
    return redirect("/")

def get_user_id():
    try:
        username = session["username"]
    except:
        return None
    sql = "SELECT id FROM users WHERE username=:username"
    return db.session.execute(sql, {"username":username}).fetchone()[0]

def csrf_check(token):
    if session["csrf_token"] != token:
        return render_template("error.html", error="Toiminto ei ole sallittu.")

def check_recipe_inputs(title, description, instruction, ingredients):
    if len(title) == 0:
        return render_template("error.html", error="Reseptillä ei ole otsikkoa.")
    if len(title) > 50:
        return render_template("error.html", error="Otsikon maksimipituus on 50 merkkiä.")
    if len(description) > 200:
        return render_template("error.html", error="Kuvauksen maksimipituus on 200 merkkiä.")
    if len(instruction) > 2000:
        return render_template("error.html", error="Ohjeen maksimipituus on 2000 merkkiä.")
    for i in ingredients:
        if len(i) > 100:
            return render_template("error.html", error="Ainesosan maksimipituus on 100 merkkiä.")