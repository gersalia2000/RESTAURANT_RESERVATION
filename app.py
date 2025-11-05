import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "dev-plate-chill-secret"  # change for production

ALLOWED_START_TIMES = ["08:00am-10:00am","11:00am-01:00pm","02:00pm-04-00pm","05:00pm-07:00pm","07:00pm-09:00pm","10:00pm-12:00am",]

MENU_ITEMS = [
    {"id":1,"name":"Grilled Chicken Alfredo Pasta","category":"Food","price":280,"img":"https://images.unsplash.com/photo-1617196035154-4ce5f0b6c6c7?auto=format&fit=crop&w=900&q=80"},
    {"id":2,"name":"Classic Beef Burger with Fries","category":"Food","price":240,"img":"https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=900&q=80"},
    {"id":3,"name":"Garlic Butter Shrimp","category":"Food","price":300,"img":"https://images.unsplash.com/photo-1625944230921-9c1abcb2a5cb?auto=format&fit=crop&w=900&q=80"},
    {"id":4,"name":"Chicken Teriyaki Rice Bowl","category":"Food","price":220,"img":"https://images.unsplash.com/photo-1562967914-608fb3f1f2fe?auto=format&fit=crop&w=900&q=80"},
    {"id":5,"name":"Crispy Pork Sisig","category":"Food","price":260,"img":"https://images.unsplash.com/photo-1617191511073-6e6b5f1d2c3d?auto=format&fit=crop&w=900&q=80"},
    {"id":6,"name":"BBQ Ribs with Mashed Potato","category":"Food","price":350,"img":"https://images.unsplash.com/photo-1555992336-03a23c3bf2c8?auto=format&fit=crop&w=900&q=80"},
    {"id":7,"name":"Baked Macaroni with Cheese","category":"Food","price":180,"img":"https://images.unsplash.com/photo-1599785209796-9cfbfe2b1d4d?auto=format&fit=crop&w=900&q=80"},
    {"id":8,"name":"Margherita Pizza","category":"Food","price":320,"img":"https://images.unsplash.com/photo-1548365328-88f0e58d2b1e?auto=format&fit=crop&w=900&q=80"},
    {"id":9,"name":"Beef Tapa with Garlic Rice and Egg (Tapsilog)","category":"Food","price":200,"img":"https://images.unsplash.com/photo-1611078489734-4d9fcb4a9f2c?auto=format&fit=crop&w=900&q=80"},
    {"id":10,"name":"Crispy Pata","category":"Food","price":420,"img":"https://images.unsplash.com/photo-1551218808-94e220e084d2?auto=format&fit=crop&w=900&q=80"},
    {"id":11,"name":"Adobo Flakes Rice Bowl","category":"Food","price":190,"img":"https://images.unsplash.com/photo-1627308595229-7830a5c91f9f?auto=format&fit=crop&w=900&q=80"},
    {"id":12,"name":"Carbonara with Garlic Bread","category":"Food","price":260,"img":"https://images.unsplash.com/photo-1612438213090-4a4548932e07?auto=format&fit=crop&w=900&q=80"},
    {"id":13,"name":"Chicken Wings (Honey Garlic)","category":"Food","price":220,"img":"https://images.unsplash.com/photo-1604908177207-7a2f4b0a8b43?auto=format&fit=crop&w=900&q=80"},
    {"id":14,"name":"Fish and Chips","category":"Food","price":230,"img":"https://images.unsplash.com/photo-1586190848861-99aa4a171e90?auto=format&fit=crop&w=900&q=80"},
    {"id":15,"name":"Creamy Mushroom Soup","category":"Food","price":140,"img":"https://images.unsplash.com/photo-1603133872878-684f33d2e06e?auto=format&fit=crop&w=900&q=80"},
    {"id":16,"name":"Iced Caramel Macchiato","category":"Drink","price":120,"img":"https://images.unsplash.com/photo-1558980664-10b2a3e9b6f6?auto=format&fit=crop&w=900&q=80"},
    {"id":17,"name":"Mango Shake","category":"Drink","price":110,"img":"https://images.unsplash.com/photo-1563306406-2b7f53b2a2c3?auto=format&fit=crop&w=900&q=80"},
    {"id":18,"name":"Milk Tea (Wintermelon)","category":"Drink","price":90,"img":"https://images.unsplash.com/photo-1551022370-5c522c4e4e0a?auto=format&fit=crop&w=900&q=80"},
    {"id":19,"name":"Iced Mocha Latte","category":"Drink","price":130,"img":"https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=900&q=80"},
    {"id":20,"name":"Fresh Lemonade","category":"Drink","price":80,"img":"https://images.unsplash.com/photo-1505253216365-0a3d71e310da?auto=format&fit=crop&w=900&q=80"},
]

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    c = db.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            time TEXT,
            people INTEGER,
            items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER,
            user_id INTEGER,
            items TEXT,
            total REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    db.commit()

@app.teardown_appcontext
def close_connection(exc):
    db = getattr(g, "_database", None)
    if db:
        db.close()

with app.app_context():
    init_db()

def find_item_by_id(iid):
    for it in MENU_ITEMS:
        if it["id"] == int(iid):
            return it
    return None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/menu")
def menu():
    return render_template("menu.html", menu_items=MENU_ITEMS)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/reservations")
def reservations():
    return render_template("reservations.html", times=ALLOWED_START_TIMES, menu_items=MENU_ITEMS)

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username","").strip()
    email = request.form.get("email","").strip()
    password = request.form.get("password","")
    if not username or not email or not password:
        flash("Please provide name, email and password.", "error")
        return redirect(url_for("reservations"))
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", (email,))
    if cur.fetchone():
        flash("Email already used. Please login or use a different email.", "error")
        return redirect(url_for("reservations"))
    pw = generate_password_hash(password)
    cur.execute("INSERT INTO users (username,email,password_hash) VALUES (?,?,?)", (username,email,pw))
    db.commit()
    user_id = cur.lastrowid
    session["user_id"] = user_id
    session["username"] = username
    flash("Registered and logged in.", "success")
    return redirect(url_for("reservations"))

@app.route("/create_order", methods=["POST"])
def create_order():
    user_id = session.get("user_id")
    items_json = request.form.get("items")
    if not items_json:
        return jsonify({"error":"no items"}), 400
    try:
        items = json.loads(items_json)
    except Exception:
        return jsonify({"error":"bad json"}), 400
    total = 0
    saved = []
    for it in items:
        iid = int(it.get("id"))
        qty = int(it.get("qty",1))
        item = find_item_by_id(iid)
        if item:
            saved.append({"id":item["id"], "name":item["name"], "price":item["price"], "qty":qty})
            total += item["price"] * qty
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO orders (reservation_id, user_id, items, total) VALUES (?,?,?,?)", (None, user_id, json.dumps(saved), total))
    db.commit()
    return jsonify({"ok":True, "total": total})

@app.route("/create_reservation", methods=["POST"])
def create_reservation():
    user_id = session.get("user_id")
    people = request.form.get("people") or 1
    date_part = request.form.get("date")
    time_part = request.form.get("time")
    items_json = request.form.get("items") or request.form.get("reservation_items")
    if not date_part or not time_part:
        flash("Please pick date and time.", "error")
        return redirect(url_for("reservations"))
    try:
        dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
        stored_dt = dt.isoformat(timespec='minutes')
    except Exception:
        stored_dt = f"{date_part} {time_part}"
    try:
        people_int = int(people)
    except:
        people_int = 1
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO reservations (user_id, time, people, items) VALUES (?,?,?,?)", (user_id, stored_dt, people_int, items_json or "[]"))
    db.commit()
    flash("Reservation saved. Thank you!", "success")
    return redirect(url_for("reservations"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
