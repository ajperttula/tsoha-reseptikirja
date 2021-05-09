from db import db
from flask import session


def get_comments(recipe_id):
    sql = """SELECT U.username, C.comment, C.sent_at, C.id 
             FROM users U, comments C 
             WHERE U.id=C.sender_id 
             AND C.recipe_id=:recipe_id 
             AND C.visible=1 
             ORDER BY C.sent_at"""
    comments = db.session.execute(sql, {"recipe_id": recipe_id}).fetchall()
    return comments


def add_comment(recipe_id, sender_id, comment):
    check_ok, msg = check_comment(comment)
    if not check_ok:
        return False, msg
    if recipe_exists(recipe_id):
        sql = """INSERT INTO comments (recipe_id, sender_id, comment, sent_at, visible) 
                 VALUES (:recipe_id, :sender_id, :comment, NOW(), 1)"""
        db.session.execute(sql, {"recipe_id": recipe_id,
                                 "sender_id": sender_id, "comment": comment})
        db.session.commit()
        return True, ""
    return False, "Reseptiä ei löytynyt."


def delete_reviews(recipe_id):
    sql = """UPDATE comments 
             SET visible=0 
             WHERE recipe_id=:recipe_id"""
    db.session.execute(sql, {"recipe_id": recipe_id})
    sql = """UPDATE grades 
             SET visible=0 
             WHERE recipe_id=:recipe_id"""
    db.session.execute(sql, {"recipe_id": recipe_id})
    db.session.commit()


def delete_comment(id):
    if is_own_comment(id):
        sql = """UPDATE comments 
                 SET visible=0 
                 WHERE id=:id"""
        db.session.execute(sql, {"id": id})
        db.session.commit()
        return True, ""
    return False, "Toiminto ei ole sallittu."


def grade_recipe(recipe_id, grade):
    if not check_grade(grade):
        return False, "Arvosanan on oltava kokonaisluku väliltä 1-5."
    if recipe_exists(recipe_id):
        sql = """INSERT INTO grades (recipe_id, grade, visible) 
                 VALUES (:recipe_id, :grade, 1)"""
        db.session.execute(sql, {"recipe_id": recipe_id, "grade": grade})
        db.session.commit()
        return True, ""
    return False, "Reseptiä ei löytynyt."


def get_average(recipe_id):
    sql = """SELECT ROUND(AVG(grade), 1) 
             FROM grades 
             WHERE recipe_id=:recipe_id"""
    average = db.session.execute(sql, {"recipe_id": recipe_id}).fetchone()[0]
    return "Ei arvosteluja" if not average else average


def check_grade(grade):
    try:
        grade = int(grade)
        if grade > 0 and grade < 6:
            return True
        return False
    except:
        return False


def recipe_exists(recipe_id):
    try:
        sql = """SELECT COUNT(*) 
                FROM recipes 
                WHERE id=:recipe_id 
                AND visible=1"""
        result = db.session.execute(sql, {"recipe_id": recipe_id}).fetchone()[0]
        return result
    except:
        return False


def check_comment(comment):
    if len(comment) == 0:
        return False, "Kommentti on tyhjä."
    if len(comment) > 1000:
        return False, "Kommentti on liian pitkä."
    return True, ""


def is_own_comment(comment_id):
    sql = """SELECT sender_id 
             FROM comments 
             WHERE id=:comment_id"""
    sender = db.session.execute(sql, {"comment_id": comment_id}).fetchone()
    if not sender or sender[0] != session["user_id"]:
        return False
    return True
