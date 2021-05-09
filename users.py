from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom


def check_username_password(username, password, password_2, role):
    if len(username) < 3:
        return False, "Antamasi käyttäjätunnus on liian lyhyt."
    if len(username) > 20:
        return False, "Antamasi käyttäjätunnus on liian pitkä."
    if password != password_2:
        return False, "Salasanat eivät täsmää."
    if len(password) < 8:
        return False, "Salasana on liian lyhyt."
    if len(password) > 32:
        return False, "Salasana on liian pitkä."
    if password == password.lower() or password == password.upper():
        return False, "Salasanan pitää sisältää pieniä ja suuria kirjaimia."
    if role != "1" and role != "0":
        return False, "Valitse rooliksi käyttäjä tai ylläpitäjä."
    return True, ""


def create_user(username, password, password_2, role):
    check_ok, msg = check_username_password(username, password, password_2, role)
    if not check_ok:
        return False, msg
    hash_value = generate_password_hash(password)
    sql = """INSERT INTO users (username, password, role) 
             VALUES (:username, :hash_value, :role)"""
    try:
        db.session.execute(sql, {"username": username, "hash_value": hash_value, "role": role})
    except:
        return False, "Käyttäjätunnus on varattu."
    db.session.commit()
    return True, f"Tunnus {username} luotu onnistuneesti!"


def check_login(username, password):
    sql = """SELECT password 
             FROM users 
             WHERE username=:username"""
    result = db.session.execute(sql, {"username": username}).fetchone()
    if result == None:
        return False, "Käyttäjätunnus tai salasana väärin."
    hash_value = result[0]
    if check_password_hash(hash_value, password):
        session["username"] = username
        user_id = get_user_id(username)
        session["user_id"] = user_id
        role = get_user_role(user_id)
        session["role"] = role
        session["csrf_token"] = urandom(16).hex()
        return True, ""
    return False, "Käyttäjätunnus tai salasana väärin."


def logout():
    del session["username"]
    del session["user_id"]
    del session["role"]
    del session["csrf_token"]


def get_user_id(username):
    sql = """SELECT id 
             FROM users 
             WHERE username=:username"""
    user_id = db.session.execute(sql, {"username": username}).fetchone()[0]
    return user_id


def get_user_role(user_id):
    sql = """SELECT role 
             FROM users 
             WHERE id=:user_id"""
    role = db.session.execute(sql, {"user_id": user_id}).fetchone()[0]
    return "admin" if role == 1 else "user"


def get_username(user_id):
    sql = """SELECT username 
             FROM users 
             WHERE id=:user_id"""
    username = db.session.execute(sql, {"user_id": user_id}).fetchone()[0]
    return username


def is_own_profile(id):
    try:
        if id == session["user_id"]:
            return True, ""
        else:
            return False, "Pääsy evätty."
    except:
        return False, "Pääsy evätty."
