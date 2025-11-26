import os
import pymysql
import json
from datetime import datetime
from flask import (Flask, render_template, request, redirect, url_for, flash,session, g, jsonify, send_from_directory)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from flask import request, jsonify
import json
from datetime import datetime
from models import db, Reservation
from flask_sqlalchemy import SQLAlchemy
# --------------------------
# Config
# --------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "dev-plate-chill-secret"

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "restaurant_db"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

ALLOWED_START_TIMES = [
    "08:00am-10:00am", "11:00am-01:00pm", "02:00pm-04:00pm",
    "05:00pm-07:00pm", "07:00pm-09:00pm", "10:00pm-12:00am"
]

GCASH_QR_PATH = os.path.join("uploads", "gcash_qr.png")  # place your QR at static/uploads/gcash_qr.png

# small sample MENU_ITEMS — keep expanding with your real list
MENU_ITEMS = [
    # DRINKS
    {"id": 1, "name": "Caramel Iced Macchiato", "category": "Drinks", "price": 140, "image": "macchiato.png"},
    {"id": 2, "name": "Mango Tropical Shake", "category": "Drinks", "price": 120, "image": "mangoshake.png"},
    {"id": 3, "name": "Wintermelon Milk Tea", "category": "Drinks", "price": 100, "image": "melon.png"},
    {"id": 4, "name": "Iced Mocha Latte", "category": "Drinks", "price": 150, "image": "mocha.png"},
    {"id": 5, "name": "Fresh Lemonade Splash", "category": "Drinks", "price": 90, "image": "lemonade.png"},
    {"id": 6, "name": "Classic Iced Tea", "category": "Drinks", "price": 80, "image": "icedtea.png"},
    {"id": 7, "name": "Bacardi Cocktail (Mockable)", "category": "Drinks", "price": 180, "image": "bacardi.png"},
    {"id": 8, "name": "Sparkling Water", "category": "Drinks", "price": 70, "image": "water.png"},

    # MAIN FOOD
    {"id": 9, "name": "Adobo Flakes Rice Bowl", "category": "Main Food", "price": 200, "image": "adoboflakes.png"},
    {"id": 10, "name": "Smoked Beef Brisket with Slaw", "category": "Main Food", "price": 250, "image": "brisket.png"},
    {"id": 11, "name": "Herb-Roasted Chicken & Veggies", "category": "Main Food", "price": 220, "image": "chickenandveggies.png"},
    {"id": 12, "name": "Baked Mac & Cheese Supreme", "category": "Main Food", "price": 180, "image": "mac.png"},
    {"id": 13, "name": "Crispy Pata Filipino Style", "category": "Main Food", "price": 300, "image": "pata.png"},
    {"id": 14, "name": "Margherita Wood-Fired Pizza", "category": "Main Food", "price": 280, "image": "pizza.png"},
    {"id": 15, "name": "BBQ Baby Back Ribs & Mash", "category": "Main Food", "price": 350, "image": "ribs.png"},
    {"id": 16, "name": "Salmon Teriyaki with Salad", "category": "Main Food", "price": 320, "image": "salmon.png"},
    {"id": 17, "name": "Garlic Butter Shrimp Linguine", "category": "Main Food", "price": 270, "image": "shrimp.png"},
    {"id": 18, "name": "Crispy Pork Sisig Platter", "category": "Main Food", "price": 220, "image": "sisig.png"},
    {"id": 19, "name": "Creamy Mushroom Soup & Bread", "category": "Main Food", "price": 150, "image": "soup.png"},
    {"id": 20, "name": "Spicy Korean Fried Chicken", "category": "Main Food", "price": 250, "image": "spicychicken.png"},
    {"id": 21, "name": "Beef Tapa with Garlic Rice & Egg", "category": "Main Food", "price": 200, "image": "tapa.png"},
    {"id": 22, "name": "Teriyaki Chicken Rice Bowl", "category": "Main Food", "price": 230, "image": "teriyaki.png"},
    {"id": 23, "name": "Vegetarian Buddha Bowl", "category": "Main Food", "price": 180, "image": "vege.png"},

    # DESSERTS
    {"id": 24, "name": "Chocolate Lava Cake", "category": "Desserts", "price": 160, "image": "lava.png"},
    {"id": 25, "name": "Classic Cheesecake Slice", "category": "Desserts", "price": 150, "image": "cheesecake.png"},
    {"id": 26, "name": "Halo-halo Sundae", "category": "Desserts", "price": 140, "image": "halohalo.png"},
    {"id": 27, "name": "Leche Flan Caramel", "category": "Desserts", "price": 130, "image": "flan.png"},
    {"id": 28, "name": "Fruit Tart", "category": "Desserts", "price": 120, "image": "tart.png"},
]
MENU_MAP = {int(item["id"]): item for item in MENU_ITEMS}

# Uploads
UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------------
# DB helpers
# --------------------------
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

@app.route("/reservations")
def reservations():
    db = get_db()
    cursor = db.cursor()  # correct for PyMySQL
    cursor.execute("SELECT * FROM reservations ORDER BY time ASC")
    data = cursor.fetchall()
    return render_template("user_dashboard.html", reservations=data)




@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        try: db.close()
        except Exception: pass

def init_db():
    db = get_db()
    cursor = db.cursor()

    # Users - added age and address columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            number VARCHAR(50),
            age INT NULL,
            address VARCHAR(255) NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Reservations (extended)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            table_id INT NULL,
            time DATETIME,
            people INT,
            items JSON,
            status VARCHAR(32) DEFAULT 'pending',
            payment_status VARCHAR(32) DEFAULT 'required',
            payment_method VARCHAR(32),
            payment_details VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # Orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reservation_id INT,
            user_id INT,
            items JSON,
            total DECIMAL(10,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY(reservation_id) REFERENCES reservations(id) ON DELETE SET NULL
        )
    """)

    # Payments (create if missing) — your code referenced payments in multiple places
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            reservation_id INT,
            name VARCHAR(255),
            payment_type VARCHAR(50),
            amount DECIMAL(10,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY(reservation_id) REFERENCES reservations(id) ON DELETE SET NULL
        )
    """)

    # Tables (floor plan)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tables (
            id INT AUTO_INCREMENT PRIMARY KEY,
            table_number INT UNIQUE,
            capacity INT,
            status ENUM('available','reserved') DEFAULT 'available',
            reserved_until DATETIME NULL
        )
    """)

    # Populate tables if empty: 5×4p, 3×6, 8×2 => total 16
    cursor.execute("SELECT COUNT(*) AS cnt FROM tables")
    cnt = cursor.fetchone().get("cnt", 0)
    if cnt == 0:
        tables_data = [
            (1,4,),(2,4),(3,4),(4,4),(5,4),     # 5 tables, 4 chairs
            (6,6),(7,6),(8,6),                 # 3 tables, 6 chairs
            (9,2),(10,2),(11,2),(12,2),(13,2),(14,2),(15,2),(16,2)  # 8 tables, 2 chairs
        ]
        cursor.executemany("INSERT INTO tables (table_number,capacity) VALUES (%s,%s)", tables_data)

    db.commit()


with app.app_context():
    init_db()



# --------------------------
# Routes: public pages
# --------------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/menu")
def menu():
    # reuse the block you provided by rendering menu.html (you can convert your posted block into menu.html)
    return render_template("menu.html", menu_items=MENU_ITEMS)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# -------------
# Auth routes (same as you had)
# -------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        # Collect inputs
        username = request.form.get("name","").strip()
        email = request.form.get("email","").strip()
        number = request.form.get("number","").strip()
        age_raw = request.form.get("age","").strip()
        address = request.form.get("address","").strip()
        password = request.form.get("password","")
        confirm = request.form.get("confirm_password","")

        # Required fields check
        if not username or not email or not number or not age_raw or not address or not password or not confirm:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        # Name validation: letters and spaces only
        import re
        if not re.fullmatch(r"[A-Za-z\s]+", username):
            flash("Name may contain letters and spaces only.", "error")
            return redirect(url_for("register"))

        # Email validation (generic)
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Please provide a valid email address.", "error")
            return redirect(url_for("register"))

        # Number: digits only
        if not number.isdigit():
            flash("Contact number must contain digits only.", "error")
            return redirect(url_for("register"))

        # Age: numeric only
        try:
            age = int(age_raw)
        except:
            flash("Age must be a number.", "error")
            return redirect(url_for("register"))

        # Password validation: match and must contain number or special character
        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))
        if not re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", password):
            flash("Password must contain at least one number or special character.", "error")
            return redirect(url_for("register"))

        # Deny registering as admin username
        if username.lower() == ADMIN_USERNAME.lower():
            flash("Cannot register as admin.", "error")
            return redirect(url_for("register"))

        db = get_db()
        cursor = db.cursor()
        try:
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                flash("Email exists. Try logging in.", "error")
                return redirect(url_for("login"))

            # Hash password and insert into database
            from werkzeug.security import generate_password_hash
            pw_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username,email,number,age,address,password_hash) VALUES (%s,%s,%s,%s,%s,%s)",
                (username, email, number, age, address, pw_hash)
            )
            db.commit()
            flash("Account created. Please login.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            db.rollback()
            flash(f"Error creating account: {e}", "error")
            return redirect(url_for("register"))

    return render_template("register.html")




#------------------------------------
# Login 
#------------------------------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")

        if not name or not email or not password:
            flash("Provide Name, Email, and Password.", "error")
            return redirect(url_for("login"))

        # admin quick-check (unchanged)
        if name == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            session["username"] = ADMIN_USERNAME
            flash("Admin logged in.", "success")
            return redirect(url_for("admin"))

        db = get_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # require both name and email to match the same user
        cursor.execute("SELECT * FROM users WHERE username=%s AND LOWER(email)=%s", (name, email))
        user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("user_dashboard"))

        flash("Invalid credentials. Make sure Name and Email match.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


# ✅ ADD THIS — FIXES YOUR logout BuildError
@app.route("/logout")
def logout():
    session.clear()     # clears all session data (user_id, username, admin flags, etc.)
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# --------------------------
# API: get tables (live)
# --------------------------
@app.route("/get_tables")
def get_tables():
    db=get_db(); cursor=db.cursor()
    cursor.execute("SELECT * FROM tables ORDER BY table_number ASC")
    return jsonify(cursor.fetchall())

#-------------------------------
#OTP
#-------------------------------
import random

def generate_otp():
    return str(random.randint(100000, 999999))

@app.route("/send_otp", methods=["POST"])
def send_otp():
    """Dummy route: just returns the OTP to the browser."""
    otp = generate_otp()
    session["payment_otp"] = otp          # store for later check
    session["otp_expires"] = datetime.now().timestamp() + 300  # 5 min
    # In real life you would email/SMS it; here we simply echo it back
    return jsonify({"success": True, "otp": otp})


@app.route("/check_otp", methods=["POST"])
def check_otp():
    supplied = request.json.get("otp", "").strip()
    stored   = session.get("payment_otp")
    expires  = session.get("otp_expires", 0)

    if not stored or datetime.now().timestamp() > expires:
        return jsonify({"success": False, "error": "OTP expired"})
    if supplied != stored:
        return jsonify({"success": False, "error": "Wrong OTP"})

    # OTP OK – clear it and let the payment proceed
    session.pop("payment_otp", None)
    session.pop("otp_expires", None)
    return jsonify({"success": True})


# --------------------------
# Create reservation (initial creation BEFORE payment)
# We will require user to include items JSON and table_id
# --------------------------
def parse_reservation_datetime(date_part:str, time_part:str):
    if not date_part or not time_part:
        raise ValueError("Missing date/time")
    if "-" in time_part:
        time_part = time_part.split("-")[0].strip()
    formats = ["%Y-%m-%d %H:%M","%Y-%m-%d %I:%M%p","%Y-%m-%d %I:%M %p"]
    for fmt in formats:
        try:
            return datetime.strptime(f"{date_part} {time_part}", fmt)
        except Exception:
            continue
    manual_formats = ["%H:%M","%I:%M%p","%I:%M %p"]
    for tf in manual_formats:
        try:
            t = datetime.strptime(time_part, tf).time()
            return datetime.strptime(date_part, "%Y-%m-%d").replace(hour=t.hour, minute=t.minute)
        except Exception:
            continue
    raise ValueError("Invalid time format")


# --------------------------
# Submit payment (Modal)
# Cash / GCash /
# --------------------------
@app.route("/submit_payment", methods=["POST"])
def submit_payment():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Please login first"}), 401

    reservation_id = request.form.get("reservation_id")
    method = request.form.get("payment_method")

    if not reservation_id or not method:
        return jsonify({"success": False, "error": "Missing reservation_id or method"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # --- GET TOTAL FROM ORDERS TABLE ---
        cursor.execute("SELECT total FROM orders WHERE reservation_id = %s", (reservation_id,))
        order_row = cursor.fetchone()

        if order_row:
            total_amount = float(order_row[0])
        else:
            total_amount = 0.00

        # --- INSERT PAYMENT ---
        cursor.execute("""
            INSERT INTO payments (user_id, reservation_id, name, payment_type, amount, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            session["user_id"],
            reservation_id,
            "Payment",
            method,
            total_amount
        ))

        # --- UPDATE RESERVATION PAYMENT STATUS ---
        cursor.execute("""
            UPDATE reservations
            SET payment_status = 'paid',
                payment_method = %s,
                status = 'Paid'
            WHERE id = %s
        """, (method, reservation_id))

        db.commit()

        return jsonify({
            "success": True,
            "status": "Paid",
            "method": method
        })

    except Exception as e:
        db.rollback()
        print("PAYMENT ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 500



#============================================================
# mark payment 
#=============================================================

@app.route("/mark_payment", methods=["POST"])
def mark_payment():
    if "user_id" not in session:
        flash("Please login.", "warning")
        return redirect(url_for("login"))

    reservation_id = request.form.get("reservation_id", "").strip()
    method = request.form.get("payment_method", "").strip().lower()  # only 'gcash' or 'cash'

    if not reservation_id or method not in ["gcash", "cash"]:
        flash("Invalid reservation or payment method.", "error")
        return redirect(url_for("user_dashboard"))

    db = get_db()
    cursor = db.cursor()

    try:
        # Check reservation exists
        cursor.execute("SELECT * FROM reservations WHERE id=%s", (reservation_id,))
        res = cursor.fetchone()
        if not res:
            flash("Reservation not found.", "error")
            return redirect(url_for("user_dashboard"))

        # Set payment status automatically
        payment_status = "paid" if method == "gcash" else "pending"

        # Update reservation
        cursor.execute("""
            UPDATE reservations
            SET payment_method=%s,
                payment_status=%s
            WHERE id=%s
        """, (method, payment_status, reservation_id))

        db.commit()
        flash(f"Payment updated: {method.upper()}", "success")

    except Exception as e:
        db.rollback()
        flash(f"Error: {e}", "error")

    return redirect(url_for("user_dashboard"))

# --------------------------
# Admin release route (make table available again)
# --------------------------
@app.route("/release_table", methods=["POST"])
def release_table():
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "Admin only"}), 403

    data = request.get_json()  # <- read JSON payload
    table_id = data.get("table_id")

    if not table_id:
        return jsonify({"success": False, "error": "Missing table_id"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Release the table
        cursor.execute(
            "UPDATE tables SET status=%s, reserved_until=NULL WHERE id=%s",
            ("available", table_id)
        )
        # Optionally release reservations linked to this table
        cursor.execute(
            "UPDATE reservations SET status=%s WHERE table_id=%s AND status=%s",
            ("released", table_id, "reserved")
        )

        db.commit()
        return jsonify({"success": True, "message": "Table released"})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    
#==========================================
# Reserve table
#==========================================

@app.route("/reserve_table", methods=["POST"])
def reserve_table():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401

    data = request.get_json()
    table_id = data.get("table_id")
    reserved_until = data.get("reserved_until")  # e.g., "2025-11-24 19:00:00"

    if not table_id or not reserved_until:
        return jsonify({"success": False, "error": "Missing table_id or reserved_until"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Make sure the table is available
        cursor.execute("SELECT status FROM tables WHERE id=%s", (table_id,))
        table = cursor.fetchone()
        if not table:
            return jsonify({"success": False, "error": "Table not found"}), 404
        if table[0] != "available":
            return jsonify({"success": False, "error": "Table already reserved"}), 400

        # Reserve the table
        cursor.execute(
            "UPDATE tables SET status=%s, reserved_until=%s WHERE id=%s",
            ("reserved", reserved_until, table_id)
        )

        # Insert reservation record
        cursor.execute(
            "INSERT INTO reservations (user_id, table_id, status, reserved_until) VALUES (%s, %s, %s, %s)",
            (session["user_id"], table_id, "reserved", reserved_until)
        )

        db.commit()
        return jsonify({"success": True, "message": "Table reserved"})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

    
# --------------------------
# Create order and confirm reservation (admin confirms payment)
# --------------------------
@app.route("/confirm_reservation", methods=["POST"])
def confirm_reservation():
    if not session.get("is_admin"):
        flash("Admin only.", "error")
        return redirect(url_for("admin_login"))

    reservation_id = request.form.get("reservation_id")
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT * FROM reservations WHERE id=%s", (reservation_id,))
        res = cursor.fetchone()
        if not res:
            flash("Reservation not found.", "error")
            return redirect(url_for("admin"))

        # parse items
        try:
            items_list = json.loads(res.get("items")) if res.get("items") else []
        except:
            items_list = []

        total = 0.0
        enhanced_items = []
        for it in items_list:
            item_id = None
            try:
                item_id = int(it.get("id"))
            except Exception:
                item_id = None
            qty = int(it.get("qty", 1)) if it.get("qty") is not None else 1
            price = MENU_MAP.get(item_id, {}).get("price") if item_id in MENU_MAP else float(it.get("price",0))
            name = MENU_MAP.get(item_id, {}).get("name") if item_id in MENU_MAP else (it.get("name") or str(item_id))
            subtotal = float(price) * qty
            total += subtotal
            enhanced_items.append({"id": item_id, "qty": qty, "name": name, "price": price})

        # fetch table number
        table_number = None
        if res.get("table_id"):
            cursor.execute("SELECT table_number FROM tables WHERE id=%s", (res.get("table_id"),))
            t = cursor.fetchone()
            table_number = t.get("table_number") if t else None

        # create order with name and table_number
        cursor.execute(
            "INSERT INTO orders (name, table_number, reservation_id, user_id, items, total, created_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,NOW())",
            (
                res.get("name") or "Guest",
                table_number,
                reservation_id,
                res.get("user_id"),
                json.dumps(enhanced_items),
                float(total)
            )
        )

        # mark reservation confirmed/reserved
        cursor.execute(
            "UPDATE reservations SET status=%s, payment_status=%s WHERE id=%s",
            ("reserved","confirmed", reservation_id)
        )

        if res.get("table_id"):
            cursor.execute(
                "UPDATE tables SET status=%s, reserved_until=%s WHERE id=%s",
                ("reserved", res.get("time"), res.get("table_id"))
            )

        db.commit()
        flash(f"Reservation {reservation_id} confirmed. Order created (Total ₱{total}).", "success")

    except Exception as e:
        db.rollback()
        flash(f"Could not confirm reservation: {e}", "error")

    return redirect(url_for("admin"))


#=====================================================================================================
#                          get order
#=====================================================================================

@app.route("/get_order", methods=["GET"])
def get_order():
    username = session.get("username")
    if not username:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    # Query orders for this user
    user_orders = order.query.filter_by(user=username).all()
    result = []

    for order in user_orders:
        items = []
        for item in order.items:  # assuming relationship Order.items
            items.append({
                "name": item.name,
                "qty": item.quantity,
                "price": item.price
            })
        result.append({
            "id": order.id,
            "user": order.user,
            "time": order.time.strftime("%H:%M"),  # format time
            "items": items,
            "total": order.total,
            "status": order.status
        })

    # Optional: sort by time descending
    result.sort(key=lambda x: datetime.strptime(x["time"], "%H:%M"), reverse=True)

    return jsonify({
        "success": True,
        "orders": result
    })
#=======================================================================
#create order
#=============================================================================
@app.route("/create_order", methods=["POST"])
def create_order():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"status":"error","message":"Login required"}), 401

    reservation_id = request.form.get("reservation_id")
    items = request.form.get("items","[]")
    total_raw = request.form.get("total","0")
    table_number = request.form.get("table_number","")
    name = request.form.get("name", session.get("username","Guest"))

    if not reservation_id:
        return jsonify({"status":"error","message":"Missing reservation_id"}), 400

    try:
        total = float(total_raw)
    except:
        total = 0.0

    try:
        items_json = json.loads(items) if items else []
    except Exception:
        return jsonify({"status":"error","message":"Invalid items format"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            INSERT INTO orders (reservation_id, user_id, table_number, items, total, created_at)
            VALUES (%s,%s,%s,%s,%s,NOW())
        """, (reservation_id, user_id, table_number, json.dumps(items_json), total))

        order_id = cursor.lastrowid
        db.commit()

        return jsonify({
            "status": "success",
            "id": order_id,
            "reservation_id": reservation_id,
            "user_id": user_id,
            "table_number": table_number,
            "items": items_json,
            "total": total,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        db.rollback()
        return jsonify({"status":"error","message":str(e)}), 500
#=======================================================================================
#delete order
#=======================================================================================
@app.route("/delete_order", methods=["POST"])
def delete_order():
    order_id = request.form.get("order_id")
    if not order_id:
        return jsonify({"status":"error","message":"No order_id provided"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM orders WHERE id=%s", (order_id,))
        db.commit()
        return jsonify({"status":"success"})
    except Exception as e:
        db.rollback()
        return jsonify({"status":"error","message": str(e)}), 500
# --------------------------
# Admin page (list reservations, release button)
# --------------------------
@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        flash("Admin only.","warning"); return redirect(url_for("admin_login"))
    db = get_db(); cursor = db.cursor()
    cursor.execute("SELECT r.*, u.username, u.email FROM reservations r LEFT JOIN users u ON r.user_id=u.id ORDER BY r.time DESC")
    reservations = cursor.fetchall() or []
    for r in reservations:
        try: r["items_parsed"] = json.loads(r["items"]) if r.get("items") else []
        except: r["items_parsed"] = []
    cursor.execute("SELECT * FROM tables ORDER BY table_number")
    tables = cursor.fetchall() or []
    cursor.execute("SELECT o.*, u.username FROM orders o LEFT JOIN users u ON o.user_id=u.id ORDER BY o.created_at DESC")
    orders = cursor.fetchall() or []
    for o in orders:
        try: o["items_parsed"] = json.loads(o["items"]) if o.get("items") else []
        except: o["items_parsed"] = []
    return render_template("admin_dashboard.html", reservations=reservations, tables=tables, orders=orders)
#======================================================================================================
#get reservation 
#======================================================================================================
@app.route('/get_reservations')
def get_reservations():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": True, "reservations": []})

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            r.id,
            r.table_id,
            r.time,
            r.people,
            r.items,
            r.status,
            r.payment_status,
            r.payment_method,
            o.total
        FROM reservations r
        LEFT JOIN orders o ON o.reservation_id = r.id
        WHERE r.user_id = %s
        ORDER BY r.time DESC
    """, (user_id,))
    rows = cursor.fetchall()

    # Decode JSON items
    for row in rows:
        try:
            row["items"] = json.loads(row["items"]) if row["items"] else []
        except:
            row["items"] = []
        row["total"] = row.get("total") or 0.00

    return jsonify({"success": True, "reservations": rows})




#==================================================================================
# create reservation 
#================================================================================================
@app.route("/create_reservation", methods=["POST"])
def create_reservation():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"status":"error","message":"Login required"}), 401

    date_part = request.form.get("date","")
    time_part = request.form.get("time","")
    people_raw = request.form.get("people","1")
    items = request.form.get("items","[]")
    table_id = request.form.get("table_id")  # table ID

    try:
        people = int(people_raw)
    except:
        people = 1

    try:
        dt = parse_reservation_datetime(date_part, time_part)
    except Exception:
        return jsonify({"status":"error","message":"Invalid date/time"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        items_json = json.loads(items) if items else []

        # check table availability
        if table_id:
            cursor.execute("SELECT * FROM tables WHERE id=%s", (table_id,))
            t = cursor.fetchone()
            if not t:
                return jsonify({"status":"error","message":"Table not found"}), 404
            if t["status"] == "reserved":
                return jsonify({"status":"error","message":"Table already reserved"}), 409

        # insert reservation
        cursor.execute("""
            INSERT INTO reservations (user_id, table_id, time, people, items, status, payment_status)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (user_id, table_id if table_id else None, dt, people, json.dumps(items_json), "pending", "required"))
        reservation_id = cursor.lastrowid

        # mark table as reserved immediately
        if table_id:
            cursor.execute("UPDATE tables SET status=%s, reserved_until=%s WHERE id=%s", ("reserved", dt, table_id))

        db.commit()

        return jsonify({
            "status": "success",
            "id": reservation_id,
            "user_id": user_id,
            "table_id": table_id,
            "items": items_json,
            "people": people,
            "time": dt.strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        db.rollback()
        return jsonify({"status":"error","message":str(e)}), 500

# ==========================
# Book a reservation
# ==========================
@app.route('/book_reservation', methods=['POST'])
def book_reservation():
    db = get_db()
    cursor = db.cursor()

    try:
        data = request.get_json()

        user_id = data.get('user_id')
        table_id = data.get('table_id')
        date = data.get('date')
        time = data.get('time')
        people = data.get('people')
        items = data.get('items', [])
        payment_method = data.get('payment_method', None)
        payment_details = data.get('payment_details', '')

        from datetime import datetime
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

        # ----------------------------
        # Update table status
        # ----------------------------
        cursor.execute(
            "UPDATE tables SET status=%s, reserved_until=%s WHERE id=%s AND status='available'",
            ("reserved", dt, table_id)
        )
        if cursor.rowcount == 0:
            # Table already reserved
            return jsonify({"success": False, "error": "Table is already reserved"}), 400

        # ----------------------------
        # INSERT INTO RESERVATIONS
        # ----------------------------
        cursor.execute("""
            INSERT INTO reservations 
            (user_id, table_id, time, people, items, status, payment_status, payment_method, payment_details)
            VALUES (%s, %s, %s, %s, %s, 'pending', 'required', %s, %s)
        """, (
            user_id,
            table_id,
            dt,
            people,
            json.dumps(items),
            payment_method,
            payment_details
        ))

        reservation_id = cursor.lastrowid

        # ----------------------------
        # INSERT INTO ORDERS
        # ----------------------------
        total_amount = sum(float(item["price"]) * int(item["qty"]) for item in items)

        cursor.execute("""
            INSERT INTO orders (reservation_id, user_id, items, total)
            VALUES (%s, %s, %s, %s)
        """, (
            reservation_id,
            user_id,
            json.dumps(items),
            total_amount
        ))

        # ----------------------------
        # INSERT INTO PAYMENTS
        # ----------------------------
        cursor.execute("""
            INSERT INTO payments (user_id, reservation_id, name, payment_type, amount)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            reservation_id,
            "Pending Payment",
            payment_method if payment_method else "cash",
            total_amount
        ))

        db.commit()

        # ----------------------------
        # Return to frontend
        # ----------------------------
        return jsonify({
            "success": True,
            "reservation": {
                "id": reservation_id,
                "user_id": user_id,
                "table_id": table_id,
                "time": str(dt),
                "people": people,
                "items": items,
                "status": "pending",
                "payment_status": "required",
                "payment_method": payment_method
            }
        })

    except Exception as e:
        db.rollback()
        print("ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 500



# ==========================
# Edit a reservation
# ==========================
@app.route("/edit_reservation/<int:id>", methods=["GET", "POST"])
def edit_reservation(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reservations WHERE id=%s", (id,))
    reservation = cursor.fetchone()
    if not reservation:
        flash("Reservation not found.", "error")
        return redirect(url_for("user_dashboard"))

    import json
    reservation['items'] = json.loads(reservation['items']) if reservation['items'] else []

    if request.method == "POST":
        table_id = request.form.get("table_id")
        date = request.form.get("date")
        time = request.form.get("time")
        people = request.form.get("people")
        items = request.form.get("items", "[]")

        # Validate items
        try:
            items_list = json.loads(items)
        except Exception:
            items_list = []

        # Parse datetime
        from datetime import datetime
        try:
            if "-" in time:
                time = time.split("-")[0].strip()
            dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except Exception:
            flash("Invalid date/time format", "error")
            return redirect(url_for("edit_reservation", id=id))

        try:
            # Update table status if table changed
            old_table = reservation['table_id']
            if table_id != str(old_table):
                # Free old table
                if old_table:
                    cursor.execute("UPDATE tables SET status='available', reserved_until=NULL WHERE id=%s", (old_table,))
                # Reserve new table
                if table_id:
                    cursor.execute("UPDATE tables SET status='reserved', reserved_until=%s WHERE id=%s", (dt, table_id))

            cursor.execute("""
                UPDATE reservations
                SET table_id=%s, time=%s, people=%s, items=%s
                WHERE id=%s
            """, (table_id, dt, people, json.dumps(items_list), id))
            db.commit()
            flash("Reservation updated successfully.", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error updating reservation: {str(e)}", "error")

        return redirect(url_for("user_dashboard"))

    return render_template("edit_reservation.html", reservation=reservation)


# ==========================
# Delete a reservation
# ==========================
@app.route('/delete_reservation', methods=['POST'])
def delete_reservation():
    # Use form instead of JSON
    reservation_id = request.form.get('reservation_id')

    if not reservation_id:
        return jsonify({"success": False, "error": "No reservation selected"})

    try:
        reservation_id = int(reservation_id)
    except:
        return jsonify({"success": False, "error": f"Invalid reservation id: {reservation_id}"})

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT table_id FROM reservations WHERE id=%s", (reservation_id,))
        res = cursor.fetchone()
        if not res:
            return jsonify({"success": False, "error": f"Reservation {reservation_id} does not exist"})
        table_id = res[0]

        cursor.execute("DELETE FROM reservations WHERE id=%s", (reservation_id,))
        if table_id:
            cursor.execute("UPDATE tables SET status='available', reserved_until=NULL WHERE id=%s", (table_id,))

        db.commit()
        # Redirect back to admin dashboard or return success
        return redirect(url_for('admin_dashboard'))  # replace with your admin page route
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)})




#=====================================================================
#update button 
#====================================================================

@app.route('/update_reservation', methods=['POST'])
def update_reservation():
    from flask import jsonify
    import json

    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({"success": False, "error": "No reservation ID provided"})

        reservation_id = data['id']
        time = data.get('time', '')
        table_id = data.get('table_id', None)
        people = data.get('people', 1)
        items = data.get('items', [])  # optional JSON list

        db = get_db()
        cursor = db.cursor()

        # Only update columns that exist
        cursor.execute("""
            UPDATE reservations
            SET time=%s, table_id=%s, people=%s, items=%s
            WHERE id=%s
        """, (time, table_id, people, json.dumps(items), reservation_id))
        db.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": str(e)})


# --------------------------
# User dashboard (updated to send tables + menu parts)
# --------------------------
@app.route("/user_dashboard")
def user_dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)  # Use DictCursor for dict results

    # ------------------- FETCH RESERVATIONS -------------------
    cursor.execute(
        "SELECT * FROM reservations WHERE user_id=%s ORDER BY time DESC", 
        (user_id,)
    )
    reservations = cursor.fetchall() or []

    for r in reservations:
        try:
            # Store parsed items in a separate key for template use
            r["items"] = json.loads(r["items"]) if r.get("items") else []
        except Exception as e:
            print("Error parsing reservation items:", e)
            r["items"] = []

    # ------------------- FETCH ORDERS -------------------
    cursor.execute(
        "SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC", 
        (user_id,)
    )
    orders = cursor.fetchall() or []

    for o in orders:
        try:
            o["items"] = json.loads(o["items"]) if o.get("items") else []
        except Exception as e:
            print("Error parsing order items:", e)
            o["items"] = []

    # ------------------- FETCH TABLES -------------------
    cursor.execute("SELECT * FROM tables ORDER BY table_number ASC")
    tables = cursor.fetchall() or []

    # ------------------- MENU CATEGORIES -------------------
    drinks = [m for m in MENU_ITEMS if m.get("category") == "Drinks"]
    main_foods = [m for m in MENU_ITEMS if m.get("category") == "Main Food"]
    desserts = [m for m in MENU_ITEMS if m.get("category") == "Desserts"]

    # ------------------- RENDER TEMPLATE -------------------
    return render_template(
        "user_dashboard.html",
        reservations=reservations,
        orders=orders,
        times=ALLOWED_START_TIMES,
        drinks=drinks,
        main_foods=main_foods,
        desserts=desserts,
        tables=tables
    )
# --------------------------
# Serve uploaded files (GCash QR etc.)
# --------------------------
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
