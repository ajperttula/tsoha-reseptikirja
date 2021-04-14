from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
from os import urandom

def check_username_password(username, password, password_2):
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
    return True, ""

def create_user(username, password):
    hash_value = generate_password_hash(password)
    sql = "INSERT INTO users (username, password, role, visible) VALUES (:username, :hash_value, 0, 1)"
    try:
        db.session.execute(sql, {"username":username, "hash_value":hash_value})
    except:
        return False, "Käyttäjätunnus on varattu."
    db.session.commit()
    return True, ""

def check_login(username, password):
    sql = "SELECT password, visible FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username}).fetchone()
    if result == None or result[1] == 0:
        return False, "Käyttäjätunnusta ei löytynyt."
    hash_value = result[0]
    if check_password_hash(hash_value, password):
        session["username"] = username
        session["csrf_token"] = urandom(16).hex()
        return True, ""
    return False, "Väärä salasana."

def logout():
    del session["username"]
    del session["csrf_token"]