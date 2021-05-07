from app import app
from flask import render_template, request, redirect, session
from db import db
import users
import recipes
import reviews


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/all-recipes", methods=["GET", "POST"])
def all_recipes():
    tags = recipes.list_tags()
    if request.method == "GET":
        results = recipes.list_recipes()
        return render_template("all-recipes.html", tags=tags, results=results)
    if request.method == "POST":
        tag_id = request.form["tag"]
        results = recipes.list_recipes(tag_id)
        return render_template("all-recipes.html", tags=tags, results=results)


@app.route("/search")
def search():
    keyword = request.args["keyword"]
    sortby = request.args["sortby"]
    orderby = request.args["orderby"]
    results = recipes.search(keyword, sortby, orderby)
    return render_template("result.html", results=results, keyword=keyword, sortby=sortby, orderby=orderby)


@app.route("/recipe/<int:id>")
def recipe(id):
    recipe, msg = recipes.get_recipe(id)
    if not recipe:
        return render_template("error.html", error=msg)
    creator = users.get_username(recipe[1])
    ingredients = recipes.get_recipe_ingredients(id)
    tags = recipes.get_recipe_tags(id)
    favourite = recipes.is_favourite(id)
    average = reviews.get_average(id)
    comments = reviews.get_comments(id)
    return render_template("recipe.html", creator=creator, recipe=recipe, tags=tags,
                           ingredients=ingredients, comments=comments,
                           average=average, favourite=favourite)


@app.route("/add-recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "GET":
        tags = recipes.list_tags()
        return render_template("new-recipe.html", tags=tags)
    if request.method == "POST":
        if session["csrf_token"] != request.form["csrf_token"]:
            return render_template("error.html", error="Toiminto ei ole sallittu.")
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


@app.route("/modify-recipe/<int:id>")
def modify_recipe(id):
    recipe, msg = recipes.get_recipe(id)
    if not recipe:
        return render_template("error.html", error=msg)
    own_recipe, msg = recipes.is_own_recipe(id)
    if not own_recipe:
        return render_template("error.html", error=msg)
    ingredients = recipes.get_recipe_ingredients(id)
    recipetags = [t[0] for t in recipes.get_recipe_tags(id)]
    tags = recipes.list_tags()
    return render_template("modify-recipe.html", recipe=recipe,
                           ingredients=ingredients, tags=tags, recipetags=recipetags)


@app.route("/execute-modification", methods=["POST"])
def execute_modification():
    if session["csrf_token"] != request.form["csrf_token"]:
        return render_template("error.html", error="Toiminto ei ole sallittu.")
    recipe_id = request.form["recipe_id"]
    own_recipe, msg = recipes.is_own_recipe(recipe_id)
    if not own_recipe:
        return render_template("error.html", error=msg)
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
    if session["csrf_token"] != request.form["csrf_token"]:
        return render_template("error.html", error="Toiminto ei ole sallittu.")
    recipe_id = request.form["recipe_id"]
    add_ok, msg = recipes.add_favourite(recipe_id)
    if not add_ok:
        return render_template("error.html", error=msg)
    return redirect(f"/recipe/{recipe_id}")


@app.route("/delete-favourite", methods=["POST"])
def delete_favourite():
    if session["csrf_token"] != request.form["csrf_token"]:
        return render_template("error.html", error="Toiminto ei ole sallittu.")
    recipe_id = request.form["recipe_id"]
    delete_ok, msg = recipes.delete_favourite(recipe_id)
    if not delete_ok:
        return render_template("error.html", error=msg)
    return redirect(f"/recipe/{recipe_id}")


@app.route("/grade-recipe", methods=["POST"])
def grade_recipe():
    if session["csrf_token"] != request.form["csrf_token"]:
        return render_template("error.html", error="Toiminto ei ole sallittu.")
    recipe_id = request.form["recipe_id"]
    grade = request.form["grade"]
    grade_ok, msg = reviews.grade_recipe(recipe_id, grade)
    if not grade_ok:
        return render_template("error.html", error=msg)
    return redirect(f"recipe/{recipe_id}")


@app.route("/add-comment", methods=["POST"])
def add_comment():
    if session["csrf_token"] != request.form["csrf_token"]:
        return render_template("error.html", error="Toiminto ei ole sallittu.")
    recipe_id = request.form["recipe_id"]
    sender_id = session["user_id"]
    comment = request.form["comment"]
    add_ok, msg = reviews.add_comment(recipe_id, sender_id, comment)
    if not add_ok:
        return render_template("error.html", error=msg)
    return redirect(f"recipe/{recipe_id}")


@app.route("/delete-comment", methods=["POST"])
def delete_comment():
    if session["csrf_token"] != request.form["csrf_token"]:
        return render_template("error.html", error="Toiminto ei ole sallittu.")
    recipe_id = request.form["recipe_id"]
    comment_id = request.form["comment_id"]
    delete_ok, msg = reviews.delete_comment(comment_id)
    if not delete_ok:
        return render_template("error.html", error=msg)
    return redirect(f"recipe/{recipe_id}")


@app.route("/delete-recipe", methods=["POST"])
def delete_recipe():
    if session["csrf_token"] != request.form["csrf_token"]:
        return render_template("error.html", error="Toiminto ei ole sallittu.")
    recipe_id = request.form["recipe_id"]
    delete_ok, msg = recipes.delete_recipe(recipe_id)
    if not delete_ok:
        return render_template("error.html", error=msg)
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
        create_ok, msg = users.create_user(username, password, password_2)
        if not create_ok:
            return render_template("new-user.html", error=msg)
        return render_template("success.html", msg=msg)


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
        return render_template("login.html", error=msg)


@app.route("/logout")
def logout():
    try:
        users.logout()
    except:
        pass
    return redirect("/")
