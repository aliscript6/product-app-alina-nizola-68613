from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DATABASE = "products.db"


# ---------- DB INIT ----------
def init_db():
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

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    category = data.get("category") or "Other"
    quantity = data.get("quantity") or "1"
    calories = data.get("calories") or 0

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products (name, category, quantity, calories, purchased)
        VALUES (?, ?, ?, ?, 0)
        """,
        (name, category, quantity, calories),
    )

    conn.commit()
    new_id = cursor.lastrowid
    new_product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (new_id,)
    ).fetchone()
    conn.close()

    return jsonify(dict(new_product)), 201


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.json

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE products
        SET name = ?, category = ?, quantity = ?, calories = ?, purchased = ?
        WHERE id = ?
        """,
        (
            data.get("name"),
            data.get("category"),
            data.get("quantity"),
            data.get("calories"),
            1 if data.get("purchased") else 0,
            product_id,
        ),
    )

    conn.commit()
    updated = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    conn.close()

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
    if request.method == "GET":
        return get_products()
    if request.method == "POST":
        return add_product()


@app.route("/api/products/<int:product_id>", methods=["PUT", "DELETE"])
def api_product_detail(product_id):
    if request.method == "PUT":
        return update_product(product_id)
    if request.method == "DELETE":
        return delete_product(product_id)


# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    app.run(debug=True)
