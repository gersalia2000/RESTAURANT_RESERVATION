import pymysql
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "dev-plate-chill-secret"  # CHANGE in production!

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "restaurant_db"

ALLOWED_START_TIMES = [
    "08:00am-10:00am", "11:00am-01:00pm", "02:00pm-04:00pm",
    "05:00pm-07:00pm", "07:00pm-09:00pm", "10:00pm-12:00am"
]

MENU_ITEMS = [
    {"id": 1, "name": "Herb-Roasted Chicken & Veggies", "category": "Food", "price": 300},
    {"id": 2, "name": "Smoked Beef Brisket with Slaw", "category": "Food", "price": 320},
    {"id": 3, "name": "Garlic Butter Shrimp Linguine", "category": "Food", "price": 280},
    {"id": 4, "name": "Teriyaki Chicken Rice Bowl", "category": "Food", "price": 240},
    {"id": 5, "name": "Crispy Pork Sisig Platter", "category": "Food", "price": 260},
    {"id": 6, "name": "BBQ Baby Back Ribs & Mash", "category": "Food", "price": 350},
    {"id": 7, "name": "Baked Mac & Cheese Supreme", "category": "Food", "price": 200},
    {"id": 8, "name": "Margherita Wood-Fired Pizza", "category": "Food", "price": 330},
    {"id": 9, "name": "Beef Tapa with Garlic Rice & Egg", "category": "Food", "price": 220},
    {"id": 10, "name": "Crispy Pata Filipino Style", "category": "Food", "price": 420},
    {"id": 11, "name": "Adobo Flakes Rice Bowl", "category": "Food", "price": 190},
    {"id": 12, "name": "Creamy Mushroom Soup & Bread", "category": "Food", "price": 150},
    {"id": 13, "name": "Spicy Korean Fried Chicken", "category": "Food", "price": 290},
    {"id": 14, "name": "Salmon Teriyaki with Salad", "category": "Food", "price": 360},
    {"id": 15, "name": "Vegetarian Buddha Bowl", "category": "Food", "price": 210},

    {"id": 16, "name": "Caramel Iced Macchiato", "category": "Drink", "price": 140},
    {"id": 17, "name": "Mango Tropical Shake", "category": "Drink", "price": 120},
    {"id": 18, "name": "Wintermelon Milk Tea", "category": "Drink", "price": 100},
    {"id": 19, "name": "Iced Mocha Latte", "category": "Drink", "price": 150},
    {"id": 20, "name": "Fresh Lemonade Splash", "category": "Drink", "price": 90},
    {"id": 21, "name": "Classic Iced Tea", "category": "Drink", "price": 80},
    {"id": 22, "name": "Bacardi Cocktail (Mockable)", "category": "Drink", "price": 180},
    {"id": 23, "name": "Sparkling Water", "category": "Drink", "price": 70},

    {"id": 24, "name": "Chocolate Lava Cake", "category": "Dessert", "price": 160},
    {"id": 25, "name": "Classic Cheesecake Slice", "category": "Dessert", "price": 150},
    {"id": 26, "name": "Halo-halo Sundae", "category": "Dessert", "price": 140},
    {"id": 27, "name": "Leche Flan Caramel", "category": "Dessert", "price": 130},
    {"id": 28, "name": "Fruit Tart", "category": "Dessert", "price": 120},
]

def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        try:
            db.close()
        except Exception:
            pass

def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            number VARCHAR(50),
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            time DATETIME,
            people INT,
            items JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reservation_id INT,
            user_id INT,
            items JSON,
            total DECIMAL(10,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    db.commit()

with app.app_context():
    init_db()

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
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    return render_template("reservations.html", times=ALLOWED_START_TIMES, menu_items=MENU_ITEMS)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        number = request.form.get("number", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password or not number:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                flash("Email already exists. Please login.", "error")
                return redirect(url_for("login"))

            pw_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, email, number, password_hash) VALUES (%s, %s, %s, %s)",
                (username, email, number, pw_hash)
            )
            db.commit()

            cursor.execute("SELECT id, username FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            if user:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                flash(f"Welcome {user['username']}! Your account was created and you're now logged in.", "success")
                return redirect(url_for("reservations"))
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception:
            db.rollback()
            flash("An error occurred during registration. Please try again.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_identifier = request.form.get("username", "").strip() or request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not login_identifier or not password:
            flash("Please provide your name/email and password.", "error")
            return redirect(url_for("login"))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s OR email=%s", (login_identifier, login_identifier))
        user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("reservations"))
        else:
            flash("Invalid name/email or password.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

def parse_reservation_datetime(date_part: str, time_part: str):
    if not date_part or not time_part:
        raise ValueError("Missing date or time")
    if "-" in time_part:
        time_part = time_part.split("-")[0].strip()

    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M%p", "%Y-%m-%d %I:%M %p"]
    for fmt in formats:
        try:
            return datetime.strptime(f"{date_part} {time_part}", fmt)
        except Exception:
            continue

    manual_formats = ["%H:%M", "%I:%M%p", "%I:%M %p"]
    for tf in manual_formats:
        try:
            t = datetime.strptime(time_part, tf).time()
            return datetime.strptime(date_part, "%Y-%m-%d").replace(hour=t.hour, minute=t.minute)
        except Exception:
            continue

    raise ValueError("Invalid time format")

@app.route("/create_reservation", methods=["POST"])
def create_reservation():
    if "user_id" not in session:
        flash("You must log in first.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    date_part = request.form.get("date", "")
    time_part = request.form.get("time", "")
    people_raw = request.form.get("people", "1")
    items = request.form.get("items", "[]")

    try:
        people = int(people_raw)
        if people < 1:
            people = 1
    except Exception:
        people = 1

    try:
        dt = parse_reservation_datetime(date_part, time_part)
    except Exception:
        flash("Invalid date or time format.", "error")
        return redirect(url_for("reservations"))

    db = get_db()
    cursor = db.cursor()
    try:
        json_items = json.loads(items) if items else []
        cursor.execute(
            "INSERT INTO reservations (user_id, time, people, items) VALUES (%s,%s,%s,%s)",
            (user_id, dt, people, json.dumps(json_items))
        )
        db.commit()
        flash("Reservation successfully created!", "success")
        return redirect(url_for("reservations"))
    except Exception:
        db.rollback()
        flash("Could not create reservation. Please try again.", "error")
        return redirect(url_for("reservations"))

if __name__ == "__main__":
    app.run(debug=True)
