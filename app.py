from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DATABASE = "products.db"


# ---------- DB INIT ----------
def init_db():
    # jeśli baza jeszcze nie istnieje – tworzymy ją z pełną strukturą
    # (w tym z kolumną 'price' dla ceny produktu)
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                quantity TEXT,
                calories INTEGER,
                price REAL DEFAULT 0,           -- dodane pole 'price' (cena produktu)
                purchased BOOLEAN DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()


init_db()


# ---------- HELPERS ----------
def db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- UI ROUTE ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- CORE CRUD (без /api) ----------
@app.route("/products", methods=["GET"])
def get_products():
    conn = db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])


@app.route("/products", methods=["POST"])
def add_product():
    data = request.json

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    category = data.get("category") or "other"
    quantity = data.get("quantity") or "1"
    calories = data.get("calories") or 0

    # nowa logika – obsługa ceny z frontendu
    # jeśli price не пришла – подставляем 0
    price = data.get("price")
    if price is None or price == "":
        price = 0
    try:
        price = float(price)
    except (TypeError, ValueError):
        price = 0

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products (name, category, quantity, calories, price, purchased)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (name, category, quantity, calories, price),
    )

    conn.commit()
    new_id = cursor.lastrowid
    new_product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (new_id,)
    ).fetchone()
    conn.close()

    # zwracamy cały produkt, w tym price (cena)
    return jsonify(dict(new_product)), 201


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.json

    # bezpieczne pobieranie pól z JSON
    name = data.get("name")
    category = data.get("category")
    quantity = data.get("quantity")
    calories = data.get("calories")

    # obsługa ceny przy aktualizacji
    price = data.get("price")
    if price is None or price == "":
        price = 0
    try:
        price = float(price)
    except (TypeError, ValueError):
        price = 0

    purchased = 1 if data.get("purchased") else 0

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE products
        SET name = ?, category = ?, quantity = ?, calories = ?, price = ?, purchased = ?
        WHERE id = ?
        """,
        (name, category, quantity, calories, price, purchased, product_id),
    )

    conn.commit()
    updated = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    conn.close()

    # frontend u Ciebie i tak aktualizuje stan lokalny,
    # ale zwrot pełnego obiektu też jest OK
    return jsonify(dict(updated))


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = db_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


# ---------- ALIASЫ /api/... ДЛЯ ФРОНТА ----------
@app.route("/api/products", methods=["GET", "POST"])
def api_products():
    # alias dla /products – żeby działały oba warianty ścieżek
    if request.method == "GET":
        return get_products()
    if request.method == "POST":
        return add_product()


@app.route("/api/products/<int:product_id>", methods=["PUT", "DELETE"])
def api_product_detail(product_id):
    # alias dla /products/<id> – PUT/DELETE pod /api/...
    if request.method == "PUT":
        return update_product(product_id)
    if request.method == "DELETE":
        return delete_product(product_id)


# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    app.run(debug=True)
