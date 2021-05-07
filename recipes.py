from db import db
from flask import session


def list_recipes():
    sql = """SELECT id, title 
             FROM recipes 
             WHERE visible=1 
             ORDER BY id DESC"""
    recipes = db.session.execute(sql).fetchall()
    return recipes


def list_own_recipes(id):
    sql = """SELECT id, title 
             FROM recipes 
             WHERE creator_id=:id
             AND visible=1
             ORDER BY id DESC"""
    recipes = db.session.execute(sql, {"id": id}).fetchall()
    return recipes


def list_tags():
    sql = """SELECT id, tag 
             FROM tags"""
    tags = db.session.execute(sql).fetchall()
    return tags


def search(keyword, sortby, orderby):
    keyword = "%" + keyword.lower() + "%"
    sql = """SELECT DISTINCT R.id, R.title, R.viewed, COALESCE(AVG(G.grade), 0) AS A 
             FROM recipes R 
             LEFT JOIN (SELECT recipe_id, ingredient FROM ingredients WHERE visible=1) AS I
             ON R.id=I.recipe_id 
             LEFT JOIN grades G 
             ON R.id=G.recipe_id 
             WHERE R.visible=1 
             AND (LOWER(R.title) LIKE :keyword 
             OR LOWER(R.description) LIKE :keyword 
             OR LOWER(R.instruction) LIKE :keyword 
             OR LOWER(I.ingredient) LIKE :keyword) 
             GROUP BY R.id"""
    if sortby == "added":
        sql += " ORDER BY R.id"
    if sortby == "grade":
        sql += " ORDER BY A"
    if sortby == "views":
        sql += " ORDER BY R.viewed"
    if orderby == "desc":
        sql += " DESC"
    results = db.session.execute(sql, {"keyword": keyword}).fetchall()
    return results


def is_favourite(recipe_id):
    try:
        user_id = session["user_id"]
        sql = """SELECT COUNT(*) 
                FROM favourites 
                WHERE user_id=:user_id 
                AND recipe_id=:recipe_id 
                AND visible=1"""
        result = db.session.execute(
            sql, {"user_id": user_id, "recipe_id": recipe_id}).fetchone()[0]
        if result:
            return True
        return False
    except:
        return False


def list_favourites(user_id):
    sql = """SELECT R.id, R.title 
             FROM recipes R, favourites F 
             WHERE F.user_id=:user_id 
             AND F.recipe_id=R.id
             AND F.visible=1
             ORDER BY F.added DESC"""
    recipes = db.session.execute(sql, {"user_id": user_id}).fetchall()
    return recipes

def add_favourite(recipe_id):
    def check_old_favourite():
        sql = """SELECT COUNT(*) 
                 FROM favourites 
                 WHERE user_id=:user_id 
                 AND recipe_id=:recipe_id 
                 AND visible=0"""
        result = db.session.execute(
            sql, {"user_id": user_id, "recipe_id": recipe_id}).fetchone()[0]
        return result

    if recipe_exists(recipe_id):
        user_id = session["user_id"]
        if check_old_favourite():
            sql = """UPDATE favourites 
                    SET visible=1, 
                    added=NOW() 
                    WHERE user_id=:user_id 
                    AND recipe_id=:recipe_id"""
        else:
            sql = """INSERT INTO favourites (user_id, recipe_id, added, visible) 
                    VALUES (:user_id, :recipe_id, NOW(), 1)"""
        db.session.execute(sql, {"user_id": user_id, "recipe_id": recipe_id})
        db.session.commit()
        return True, ""
    return False, "Reseptiä ei löytynyt."


def delete_favourite(recipe_id):
    if recipe_exists(recipe_id):
        user_id = session["user_id"]
        sql = """UPDATE favourites 
                SET visible=0 
                WHERE user_id=:user_id 
                AND recipe_id=:recipe_id"""
        db.session.execute(sql, {"user_id": user_id, "recipe_id": recipe_id})
        db.session.commit()
        return True, ""
    return False, "Reseptiä ei löytynyt."


def get_recipe(recipe_id):
    def add_view():
        sql = """UPDATE recipes 
                 SET viewed=viewed+1 
                 WHERE id=:recipe_id"""
        db.session.execute(sql, {"recipe_id": recipe_id})
        db.session.commit()

    if recipe_exists(recipe_id):
        add_view()
        sql = """SELECT * 
                FROM recipes 
                WHERE id=:recipe_id"""
        recipe = db.session.execute(sql, {"recipe_id": recipe_id}).fetchone()
        return recipe, ""
    return False, "Reseptiä ei löytynyt."

def get_recipe_tags(recipe_id):
    sql = """SELECT T.tag 
             FROM tags T, recipetags R 
             WHERE R.recipe_id=:recipe_id 
             AND T.id=R.tag_id 
             AND R.visible=1"""
    tags = db.session.execute(sql, {"recipe_id": recipe_id}).fetchall()
    return tags


def get_recipe_ingredients(recipe_id):
    sql = """SELECT ingredient 
             FROM ingredients 
             WHERE recipe_id=:recipe_id 
             AND visible=1"""
    ingredients = db.session.execute(sql, {"recipe_id": recipe_id}).fetchall()
    return ingredients


def add_recipe(title, description, instruction, ingredients, tags):
    check_ok, msg = check_recipe_inputs(0,
                                        title,
                                        description,
                                        instruction,
                                        ingredients)
    if not check_ok:
        return False, msg, None
    creator_id = session["user_id"]
    sql = """INSERT INTO recipes (creator_id, created_at, viewed, title, description, instruction, visible) 
             VALUES (:creator_id, NOW(), 0, :title, :description, :instruction, 1) 
             RETURNING id"""
    recipe_id = db.session.execute(sql, {"creator_id": creator_id, "title": title, "description": description,
                                         "instruction": instruction}).fetchone()[0]
    add_ingredients(recipe_id, ingredients)
    add_tags(recipe_id, tags)
    db.session.commit()
    return True, "", recipe_id


def add_ingredients(recipe_id, ingredients):
    for i in ingredients:
        if i != "":
            sql = """INSERT INTO ingredients (recipe_id, ingredient, visible) 
                     VALUES (:recipe_id, :i, 1)"""
            db.session.execute(sql, {"recipe_id": recipe_id, "i": i})


def add_tags(recipe_id, tags):
    for t in tags:
        if t != "":
            sql = """INSERT INTO recipetags (recipe_id, tag_id, visible) 
                     VALUES (:recipe_id, :t, 1)"""
            db.session.execute(sql, {"recipe_id": recipe_id, "t": t})


def modify_recipe(recipe_id, title, description, instruction, ingredients, tags):
    check_ok, msg = check_recipe_inputs(recipe_id, title, description,
                                        instruction, ingredients)
    if not check_ok:
        return False, msg
    sql = """UPDATE recipes 
             SET title=:title, 
             description=:description, 
             instruction=:instruction 
             WHERE id=:recipe_id"""
    db.session.execute(sql, {"title": title, "description": description,
                       "instruction": instruction, "recipe_id": recipe_id})
    modify_ingredients(recipe_id, ingredients)
    modify_tags(recipe_id, tags)
    db.session.commit()
    return True, ""


def modify_ingredients(recipe_id, ingredients):
    sql = """SELECT id 
             FROM ingredients 
             WHERE recipe_id=:recipe_id 
             AND visible=1"""
    old_ingredients = db.session.execute(
        sql, {"recipe_id": recipe_id}).fetchall()
    new_ingredients = [i for i in ingredients if i != ""]
    for i in range(min(len(old_ingredients), len(new_ingredients))):
        id = old_ingredients.pop(0)[0]
        ingredient = new_ingredients.pop(0)
        sql = """UPDATE ingredients 
                 SET ingredient=:ingredient 
                 WHERE id=:id"""
        db.session.execute(sql, {"ingredient": ingredient, "id": id})
    if old_ingredients:
        for i in old_ingredients:
            id = i[0]
            sql = """UPDATE ingredients 
                     SET visible=0 
                     WHERE id=:id"""
            db.session.execute(sql, {"id": id})
    else:
        for i in new_ingredients:
            sql = """INSERT INTO ingredients (recipe_id, ingredient, visible) 
                     VALUES (:recipe_id, :i, 1)"""
            db.session.execute(sql, {"recipe_id": recipe_id, "i": i})


def modify_tags(recipe_id, tags):
    sql = """SELECT tag_id, visible 
             FROM recipetags 
             WHERE recipe_id=:recipe_id"""
    result = db.session.execute(sql, {"recipe_id": recipe_id}).fetchall()
    old_tags = [t[0] for t in result if t[1] == 1]
    removed_tags = [t[0] for t in result if t[1] == 0]
    new_tags = [int(t) for t in tags if t != ""]
    for t in new_tags:
        if t in removed_tags:
            sql = """UPDATE recipetags 
                     SET visible=1 
                     WHERE recipe_id=:recipe_id 
                     AND tag_id=:t"""
            db.session.execute(sql, {"recipe_id": recipe_id, "t": t})
        elif t not in old_tags[:]:
            sql = """INSERT INTO recipetags (recipe_id, tag_id, visible) 
                     VALUES (:recipe_id, :t, 1)"""
            db.session.execute(sql, {"recipe_id": recipe_id, "t": t})
        else:
            old_tags.remove(t)
    if old_tags:
        for t in old_tags:
            sql = """UPDATE recipetags 
                     SET visible=0 
                     WHERE recipe_id=:recipe_id 
                     AND tag_id=:t"""
            db.session.execute(sql, {"recipe_id": recipe_id, "t": t})


def delete_recipe(recipe_id):
    own_recipe, msg = is_own_recipe(recipe_id)
    if not own_recipe:
        return False, msg
    if recipe_exists(recipe_id):
        sql = """UPDATE recipes 
                SET visible=0 
                WHERE id=:recipe_id"""
        db.session.execute(sql, {"recipe_id": recipe_id})

        sql = """UPDATE ingredients 
                SET visible=0 
                WHERE recipe_id=:recipe_id"""
        db.session.execute(sql, {"recipe_id": recipe_id})

        sql = """UPDATE recipetags 
                SET visible=0 
                WHERE recipe_id=:recipe_id"""
        db.session.execute(sql, {"recipe_id": recipe_id})

        sql = """UPDATE favourites 
                SET visible=0 
                WHERE recipe_id=:recipe_id"""
        db.session.execute(sql, {"recipe_id": recipe_id})

        db.session.commit()
        return True, ""
    return False, "Reseptiä ei löytynyt"


def check_recipe_inputs(recipe_id, title, description, instruction, ingredients):
    if len(title) == 0:
        return False, "Reseptillä ei ole otsikkoa."

    if len(title) > 50:
        return False, "Otsikon maksimipituus on 50 merkkiä."

    if title_taken(title, recipe_id):
        return False, "Otsikko on jo käytössä toisessa reseptissä."

    if len(description) > 200:
        return False, "Kuvauksen maksimipituus on 200 merkkiä."

    if len(instruction) > 2000:
        return False, "Ohjeen maksimipituus on 2000 merkkiä."

    for i in ingredients:
        if len(i) > 100:
            return False, "Ainesosan maksimipituus on 100 merkkiä."

    return True, ""


def title_taken(title, recipe_id):
    sql = """SELECT COUNT(*) 
             FROM recipes 
             WHERE title=:title 
             AND visible=1 
             AND id<>:recipe_id"""
    result = db.session.execute(
        sql, {"title": title, "recipe_id": recipe_id}).fetchone()[0]
    return result


def recipe_exists(recipe_id):
    sql = """SELECT COUNT(*) 
             FROM recipes 
             WHERE id=:recipe_id 
             AND visible=1"""
    result = db.session.execute(sql, {"recipe_id": recipe_id}).fetchone()[0]
    return result


def is_own_recipe(recipe_id):
    sql = """SELECT creator_id 
             FROM recipes 
             WHERE id=:recipe_id"""
    creator = db.session.execute(sql, {"recipe_id": recipe_id}).fetchone()
    
    try:
        if not creator or creator[0] != session["user_id"]:
            return False, "Toiminto ei ole sallittu."
        return True, ""
    except:
        return False, "Toiminto ei ole sallittu."
