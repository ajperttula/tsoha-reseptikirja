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
    sql = """INSERT INTO comments (recipe_id, sender_id, comment, sent_at, visible) 
             VALUES (:recipe_id, :sender_id, :comment, NOW(), 1)"""
    db.session.execute(sql, {"recipe_id": recipe_id,
                       "sender_id": sender_id, "comment": comment})
    db.session.commit()
    return True, ""


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
    sql = """UPDATE comments 
             SET visible=0 
             WHERE id=:id"""
    db.session.execute(sql, {"id": id})
    db.session.commit()


def grade_recipe(recipe_id, grade):
    sql = """INSERT INTO grades (recipe_id, grade, visible) 
             VALUES (:recipe_id, :grade, 1)"""
    db.session.execute(sql, {"recipe_id": recipe_id, "grade": grade})
    db.session.commit()


def get_average(recipe_id):
    sql = """SELECT ROUND(AVG(grade), 1) 
             FROM grades 
             WHERE recipe_id=:recipe_id;"""
    average = db.session.execute(sql, {"recipe_id": recipe_id}).fetchone()[0]
    if not average:
        return "Ei arvosteluja"
    return average


def check_comment(comment):
    if len(comment) == 0:
        return False, "Kommentti on tyhjä."
    if len(comment) > 1000:
        return False, "Kommentti on liian pitkä."
    return True, ""
