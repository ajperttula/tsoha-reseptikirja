from app import app
from flask import render_template, request, redirect, session
from db import db
import users
import recipes
import reviews


@app.route("/")
def index():
    list = recipes.list_recipes()
    return render_template("index.html", recipes=list)


@app.route("/search")
def search():
    keyword = request.args["keyword"]
    results = recipes.search(keyword)
    return render_template("result.html", results=results)


@app.route("/recipe/<int:id>")
def recipe(id):
    recipe, msg = recipes.get_recipe(id)
    if not recipe:
        return render_template("error.html", error=msg)
    creator = users.get_username(recipe[1])
    ingredients = recipes.get_recipe_ingredients(id)
    tags = recipes.get_recipe_tags(id)
    own_recipe = recipes.is_own_recipe(recipe[1])
    favourite = recipes.is_favourite(id)
    average = reviews.get_average(id)
    comments = reviews.get_comments(id)
    return render_template("recipe.html", creator=creator, recipe=recipe, tags=tags,
                           ingredients=ingredients, comments=comments, 
                           own_recipe=own_recipe, average=average, favourite=favourite)


@app.route("/add-recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "GET":
        tags = recipes.list_tags()
        return render_template("new-recipe.html", tags=tags)
    if request.method == "POST":
        csrf_check(request.form["csrf_token"])
        title = request.form["title"]
        description = request.form["description"]
        instruction = request.form["instruction"]
        ingredients = request.form.getlist("ingredient")
        tags = request.form.getlist("tag")
        add_ok, msg, recipe_id = recipes.add_recipe(title, description,
                                                    instruction, ingredients, tags)
        if not add_ok:
            return render_template("error.html", error=msg)
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
    tags = recipes.list_tags()
    return render_template("modify-recipe.html", recipe_id=recipe_id, title=title, description=description,
                           ingredients=ingredients, instruction=instruction, tags=tags, recipetags=recipetags)


@app.route("/execute-modification", methods=["POST"])
def execute_modification():
    csrf_check(request.form["csrf_token"])
    recipe_id = request.form["recipe_id"]
    title = request.form["title"]
    description = request.form["description"]
    instruction = request.form["instruction"]
    ingredients = request.form.getlist("ingredient")
    tags = request.form.getlist("tag")
    modify_ok, msg = recipes.modify_recipe(recipe_id, title, description,
                                           instruction, ingredients, tags)
    if not modify_ok:
        return render_template("error.html", error=msg)
    return redirect(f"/recipe/{recipe_id}")


@app.route("/add-favourite", methods=["POST"])
def add_favourite():
    csrf_check(request.form["csrf_token"])
    recipe_id = request.form["recipe_id"]
    recipes.add_favourite(recipe_id)
    return redirect(f"/recipe/{recipe_id}")


@app.route("/delete-favourite", methods=["POST"])
def delete_favourite():
    csrf_check(request.form["csrf_token"])
    recipe_id = request.form["recipe_id"]
    recipes.delete_favourite(recipe_id)
    return redirect(f"/recipe/{recipe_id}")


@app.route("/grade-recipe", methods=["POST"])
def grade_recipe():
    csrf_check(request.form["csrf_token"])
    recipe_id = request.form["recipe_id"]
    grade = request.form["grade"]
    reviews.grade_recipe(recipe_id, grade)
    return redirect(f"recipe/{recipe_id}")


@app.route("/add-comment", methods=["POST"])
def add_comment():
    csrf_check(request.form["csrf_token"])
    recipe_id = request.form["recipe_id"]
    sender_id = session["user_id"]
    comment = request.form["comment"]
    add_ok, msg = reviews.add_comment(recipe_id, sender_id, comment)
    if not add_ok:
        return render_template("error.html", error=msg)
    return redirect(f"recipe/{recipe_id}")


@app.route("/delete-recipe", methods=["POST"])
def delete_recipe():
    csrf_check(request.form["csrf_token"])
    recipe_id = request.form["recipe_id"]
    recipes.delete_recipe(recipe_id)
    reviews.delete_reviews(recipe_id)
    return redirect("/")


@app.route("/create-user", methods=["GET", "POST"])
def create_user():
    if request.method == "GET":
        return render_template("new-user.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password_2 = request.form["password_check"]
        check_ok, msg = users.check_username_password(
            username,
            password,
            password_2
        )
        if not check_ok:
            return render_template("error.html", error=msg)
        create_ok, msg = users.create_user(username, password)
        if not create_ok:
            return render_template("error.html", error=msg)
        return redirect("/")


@app.route("/profile/<int:id>")
def profile(id):
    check_ok, msg = users.is_own_profile(id)
    if not check_ok:
        return render_template("error.html", error=msg)
    own_recipes = recipes.list_own_recipes(id)
    favourites = recipes.list_favourites(id)
    return render_template("profile.html", recipes=own_recipes, favourites=favourites)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        check_ok, msg = users.check_login(username, password)
        if check_ok:
            return redirect("/")
        return render_template("error.html", error=msg)


@app.route("/logout")
def logout():
    users.logout()
    return redirect("/")


def csrf_check(token):
    if session["csrf_token"] != token:
        return render_template("error.html", error="Toiminto ei ole sallittu.")
