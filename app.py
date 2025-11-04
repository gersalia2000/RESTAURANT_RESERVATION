import os
from datetime import datetime, date, time, timedelta
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "dev-plate-chill-secret"  # change for production

# Business rules
MIN_PEOPLE = 3
MAX_PEOPLE = 20
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
ALLOWED_START_TIMES = ["08:00","10:00","12:00","14:00","16:00","18:00","20:00","21:00"]

# Menu items (food + drinks). Each entry: id, name, category, price(optional), image_url
MENU_ITEMS = [
    # Foods (1..20)
    {"id": 1, "name": "Grilled Chicken Alfredo Pasta", "category":"Food", "price":280, "img":"https://images.unsplash.com/photo-1604908177522-9ffb0b7b6b5b?auto=format&fit=crop&w=800&q=80"},
    {"id": 2, "name": "Classic Beef Burger with Fries", "category":"Food", "price":240, "img":"https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=800&q=80"},
    {"id": 3, "name": "Garlic Butter Shrimp", "category":"Food", "price":300, "img":"https://images.unsplash.com/photo-1553621042-f6e147245754?auto=format&fit=crop&w=800&q=80"},
    {"id": 4, "name": "Chicken Teriyaki Rice Bowl", "category":"Food", "price":220, "img":"https://images.unsplash.com/photo-1562967914-608fb3f1f2fe?auto=format&fit=crop&w=800&q=80"},
    {"id": 5, "name": "Crispy Pork Sisig", "category":"Food", "price":260, "img":"https://images.unsplash.com/photo-1617191511073-6e6b5f1d2c3d?auto=format&fit=crop&w=800&q=80"},
    {"id": 6, "name": "Beef Tapa with Garlic Rice and Egg (Tapsilog)", "category":"Food", "price":200, "img":"https://images.unsplash.com/photo-1611078489734-4d9fcb4a9f2c?auto=format&fit=crop&w=800&q=80"},
    {"id": 7, "name": "BBQ Ribs with Mashed Potato", "category":"Food", "price":350, "img":"https://images.unsplash.com/photo-1555992336-03a23c3bf2c8?auto=format&fit=crop&w=800&q=80"},
    {"id": 8, "name": "Baked Macaroni with Cheese", "category":"Food", "price":180, "img":"https://images.unsplash.com/photo-1604908177222-5c3e30617c4a?auto=format&fit=crop&w=800&q=80"},
    {"id": 9, "name": "Margherita Pizza", "category":"Food", "price":320, "img":"https://images.unsplash.com/photo-1548365328-88f0e58d2b1e?auto=format&fit=crop&w=800&q=80"},
    {"id":10, "name":"Spicy Tuna Sandwich", "category":"Food", "price":170, "img":"https://images.unsplash.com/photo-1562967916-eb82221dfb1f?auto=format&fit=crop&w=800&q=80"},
    {"id":11, "name":"Carbonara with Garlic Bread", "category":"Food", "price":260, "img":"https://images.unsplash.com/photo-1604908177515-0f0b38bfa1cb?auto=format&fit=crop&w=800&q=80"},
    {"id":12, "name":"Chicken Wings (Honey Garlic)", "category":"Food", "price":220, "img":"https://images.unsplash.com/photo-1604908177207-7a2f4b0a8b43?auto=format&fit=crop&w=800&q=80"},
    {"id":13, "name":"Crispy Pata", "category":"Food", "price":420, "img":"https://images.unsplash.com/photo-1551218808-94e220e084d2?auto=format&fit=crop&w=800&q=80"},
    {"id":14, "name":"Adobo Flakes Rice Bowl", "category":"Food", "price":190, "img":"https://images.unsplash.com/photo-1617191511100-4aac8c8b7a8c?auto=format&fit=crop&w=800&q=80"},
    {"id":15, "name":"Creamy Mushroom Soup", "category":"Food", "price":140, "img":"https://images.unsplash.com/photo-1617191511044-96dfe01e0a7d?auto=format&fit=crop&w=800&q=80"},
    {"id":16, "name":"Caesar Salad with Grilled Chicken", "category":"Food", "price":210, "img":"https://images.unsplash.com/photo-1604908177379-6b2c3d6a5f63?auto=format&fit=crop&w=800&q=80"},
    {"id":17, "name":"Fish and Chips", "category":"Food", "price":230, "img":"https://images.unsplash.com/photo-1586190848861-99aa4a171e90?auto=format&fit=crop&w=800&q=80"},
    {"id":18, "name":"Sizzling Tofu", "category":"Food", "price":170, "img":"https://images.unsplash.com/photo-1604908177410-4b9f1b5b2f8b?auto=format&fit=crop&w=800&q=80"},
    {"id":19, "name":"Pancit Canton Special", "category":"Food", "price":150, "img":"https://images.unsplash.com/photo-1542444459-db8d46f3b44d?auto=format&fit=crop&w=800&q=80"},
    {"id":20, "name":"Cheesecake Slice (Blueberry)", "category":"Food", "price":130, "img":"https://images.unsplash.com/photo-1542827638-0f3e3b1c5b1b?auto=format&fit=crop&w=800&q=80"},
    # Drinks (21..40)
    {"id":21, "name":"Iced Caramel Macchiato", "category":"Drink", "price":120, "img":"https://images.unsplash.com/photo-1558980664-10b2a3e9b6f6?auto=format&fit=crop&w=800&q=80"},
    {"id":22, "name":"Classic Brewed Coffee", "category":"Drink", "price":60, "img":"https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=800&q=80"},
    {"id":23, "name":"Iced Mocha Latte", "category":"Drink", "price":130, "img":"https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=800&q=80"},
    {"id":24, "name":"Milk Tea (Wintermelon)", "category":"Drink", "price":90, "img":"https://images.unsplash.com/photo-1551022370-5c522c4e4e0a?auto=format&fit=crop&w=800&q=80"},
    {"id":25, "name":"Mango Shake", "category":"Drink", "price":110, "img":"https://images.unsplash.com/photo-1563306406-2b7f53b2a2c3?auto=format&fit=crop&w=800&q=80"},
    {"id":26, "name":"Chocolate Milkshake", "category":"Drink", "price":120, "img":"https://images.unsplash.com/photo-1584266279973-8d5e7a7bb6e1?auto=format&fit=crop&w=800&q=80"},
    {"id":27, "name":"Fresh Lemonade", "category":"Drink", "price":80, "img":"https://images.unsplash.com/photo-1542444459-1c67b71f2bfc?auto=format&fit=crop&w=800&q=80"},
    {"id":28, "name":"Iced Americano", "category":"Drink", "price":70, "img":"https://images.unsplash.com/photo-1509042239860-2079b6b1f3b6?auto=format&fit=crop&w=800&q=80"},
    {"id":29, "name":"Avocado Shake", "category":"Drink", "price":120, "img":"https://images.unsplash.com/photo-1560493673-3a6b2b5b3d6e?auto=format&fit=crop&w=800&q=80"},
    {"id":30, "name":"Strawberry Smoothie", "category":"Drink", "price":110, "img":"https://images.unsplash.com/photo-1551024709-8f23befc6f87?auto=format&fit=crop&w=800&q=80"},
    {"id":31, "name":"Iced Matcha Latte", "category":"Drink", "price":130, "img":"https://images.unsplash.com/photo-1543168254-480b4b5a0b35?auto=format&fit=crop&w=800&q=80"},
    {"id":32, "name":"Hot Cappuccino", "category":"Drink", "price":100, "img":"https://images.unsplash.com/photo-1511920170033-8b0e17b1bbf7?auto=format&fit=crop&w=800&q=80"},
    {"id":33, "name":"Fruit Iced Tea (Peach)", "category":"Drink", "price":90, "img":"https://images.unsplash.com/photo-1526318472351-c75fcf0706c1?auto=format&fit=crop&w=800&q=80"},
    {"id":34, "name":"Watermelon Juice", "category":"Drink", "price":95, "img":"https://images.unsplash.com/photo-1562440499-64b0a7b1f4b1?auto=format&fit=crop&w=800&q=80"},
    {"id":35, "name":"Hot Chocolate", "category":"Drink", "price":110, "img":"https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80"},
    {"id":36, "name":"Cucumber Lemon Cooler", "category":"Drink", "price":95, "img":"https://images.unsplash.com/photo-1561037404-61f4d67a5f86?auto=format&fit=crop&w=800&q=80"},
    {"id":37, "name":"Café Latte", "category":"Drink", "price":110, "img":"https://images.unsplash.com/photo-1509042239860-9cc2b4a6b2a5?auto=format&fit=crop&w=800&q=80"},
    {"id":38, "name":"Soda Float (Root Beer)", "category":"Drink", "price":120, "img":"https://images.unsplash.com/photo-1505576391880-72d4b0c6e5d0?auto=format&fit=crop&w=800&q=80"},
    {"id":39, "name":"Mineral Water (Cold)", "category":"Drink", "price":50, "img":"https://images.unsplash.com/photo-1544025162-4f9b7f0de4b2?auto=format&fit=crop&w=800&q=80"},
    {"id":40, "name":"House Iced Tea", "category":"Drink", "price":80, "img":"https://images.unsplash.com/photo-1526318472351-5f9c3b1a3a3e?auto=format&fit=crop&w=800&q=80"},
]

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        time TEXT NOT NULL,
        people INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER,
        user_id INTEGER,
        items TEXT NOT NULL,  -- JSON list of selected items
        total REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(reservation_id) REFERENCES reservations(id) ON DELETE SET NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
    )""")
    db.commit()

def seed_admin():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if cur.fetchone() is None:
        pw = generate_password_hash("AdminPass123")
        cur.execute("INSERT INTO users (username,email,password_hash,role) VALUES (?,?,?,?)",
                    ("admin","admin@example.com",pw,"admin"))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def next_weekday_date(target_weekday_index:int, from_date:date=None):
    if from_date is None:
        from_date = date.today()
    python_target = (target_weekday_index + 6) % 7
    days_ahead = (python_target - from_date.weekday()) % 7
    return from_date + timedelta(days=days_ahead)

def find_menu_item_by_id(item_id:int):
    for it in MENU_ITEMS:
        if it["id"] == item_id:
            return it
    return None

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        email = request.form.get("email","").strip()
        password = request.form.get("password","")
        confirm = request.form.get("confirm_password","")
        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for("register"))
        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))
        db = get_db(); cur = db.cursor()
        try:
            cur.execute("INSERT INTO users (username,email,password_hash,role) VALUES (?,?,?,?)",
                        (username,email,generate_password_hash(password),"user"))
            db.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")
            return redirect(url_for("register"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        db = get_db(); cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session["user_id"] = row["id"]
            session["username"] = row["username"]
            session["role"] = row["role"]
            flash(f"Welcome, {session['username']}!", "success")
            return redirect(url_for("dashboard") if row["role"]=="user" else url_for("admin"))
        else:
            flash("Incorrect username or password.", "error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    username = session.get("username")
    if request.method == "POST":
        # reservation creation accepts optional order_items (JSON string)
        day = request.form.get("weekday","").strip()
        start_time = request.form.get("start_time","").strip()
        people = request.form.get("people","").strip()
        items_json = request.form.get("order_items","")  # JSON array string or empty
        if day not in WEEKDAYS:
            flash("Please select a valid day.", "error"); return redirect(url_for("dashboard"))
        if start_time not in ALLOWED_START_TIMES:
            flash("Please select a valid time slot.", "error"); return redirect(url_for("dashboard"))
        try:
            people_int = int(people)
        except Exception:
            flash("Please enter a valid number of people.", "error"); return redirect(url_for("dashboard"))
        if people_int < MIN_PEOPLE or people_int > MAX_PEOPLE:
            flash(f"People must be between {MIN_PEOPLE} and {MAX_PEOPLE}.", "error"); return redirect(url_for("dashboard"))
        # compute next date
        day_index = WEEKDAYS.index(day)
        res_date = next_weekday_date(day_index, from_date=date.today())
        hour, minute = map(int, start_time.split(":"))
        res_dt = datetime.combine(res_date, time(hour=hour, minute=minute))
        if res_dt <= datetime.now():
            res_dt += timedelta(days=7)
        # insert reservation
        db = get_db(); cur = db.cursor()
        cur.execute("INSERT INTO reservations (user_id, time, people) VALUES (?,?,?)",
                    (session["user_id"], res_dt.isoformat(timespec='minutes'), people_int))
        db.commit()
        reservation_id = cur.lastrowid
        # if order_items provided, parse and save in orders table
        if items_json:
            try:
                items = json.loads(items_json)
                # compute total
                total = 0.0
                saved_items = []
                for iid in items:
                    it = find_menu_item_by_id(int(iid))
                    if it:
                        saved_items.append({"id": it["id"], "name": it["name"], "price": it.get("price",0)})
                        total += float(it.get("price",0))
                cur.execute("INSERT INTO orders (reservation_id, user_id, items, total) VALUES (?,?,?,?)",
                            (reservation_id, session["user_id"], json.dumps(saved_items), total))
                db.commit()
            except Exception:
                app.logger.exception("Failed to save attached order")
        flash(f"Reservation created for {res_dt.strftime('%Y-%m-%d %H:%M')} ({day} {start_time}) for {people_int} people.", "success")
        return redirect(url_for("dashboard"))
    # GET render
    return render_template("dashboard.html", username=username, weekdays=WEEKDAYS, times=ALLOWED_START_TIMES,
                           min_people=MIN_PEOPLE, max_people=MAX_PEOPLE, menu_items=MENU_ITEMS)

@app.route("/menu", methods=["GET"])
def menu_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    # show full-menu page
    return render_template("menu.html", menu_items=MENU_ITEMS)

@app.route("/order", methods=["POST"])
def create_order():
    if "user_id" not in session:
        return redirect(url_for("login"))
    # expected: 'items' -> list of item ids (form-encoded repeated or JSON), optional reservation_id
    items = request.form.getlist("items")
    reservation_id = request.form.get("reservation_id") or None
    if not items:
        flash("No menu items selected.", "error")
        return redirect(request.referrer or url_for("menu_page"))
    saved_items = []
    total = 0.0
    for iid in items:
        it = find_menu_item_by_id(int(iid))
        if it:
            saved_items.append({"id": it["id"], "name": it["name"], "price": it.get("price",0)})
            total += float(it.get("price",0))
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO orders (reservation_id, user_id, items, total) VALUES (?,?,?,?)",
                (reservation_id, session["user_id"], json.dumps(saved_items), total))
    db.commit()
    flash(f"Order saved ({len(saved_items)} items). Total ₱{total:.2f}", "success")
    # if request from modal we return to same page
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/admin")
def admin():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("dashboard"))
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT r.id, r.time, r.people, u.username FROM reservations r LEFT JOIN users u ON r.user_id = u.id ORDER BY r.time ASC")
    rows = cur.fetchall()
    # fetch orders too
    cur.execute("SELECT id, reservation_id, user_id, items, total, created_at FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()
    return render_template("admin.html", reservations=rows, orders=orders)

def setup_database():
    with app.app_context():
        init_db()
        seed_admin()

setup_database()

if __name__ == "__main__":
    app.run(debug=True)


