
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

DATABASE = os.path.join(app.root_path, "inventory.db")


# Connect to database
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# Create tables and update existing database
def init_db():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            low_stock_threshold INTEGER NOT NULL DEFAULT 10
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS stock_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            transaction_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Add product_name column if it does not exist
    columns = connection.execute(
        "PRAGMA table_info(stock_transactions)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "product_name" not in column_names:
        connection.execute(
            "ALTER TABLE stock_transactions ADD COLUMN product_name TEXT"
        )

    connection.commit()
    connection.close()

# Authentication and role protection

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            abort(403)

        return view(*args, **kwargs)
    return wrapped_view


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = get_db()
        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        connection.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            flash("Login successful.")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))
# Admin-only User Management
@app.route("/users", methods=["GET", "POST"])
@admin_required
def manage_users():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("manage_users"))

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("manage_users"))

        connection = get_db()
        try:
            connection.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), "operator")
            )
            connection.commit()
            flash("Operator account created successfully.")
        except sqlite3.IntegrityError:
            flash("Username already exists. Choose another username.")
        finally:
            connection.close()

        return redirect(url_for("manage_users"))

    connection = get_db()
    users = connection.execute(
        "SELECT id, username, role, created_at FROM users ORDER BY id"
    ).fetchall()
    connection.close()

    return render_template("users.html", users=users)
# Dashboard
@app.route("/")
@login_required
def dashboard():
    connection = get_db()

    # Total products
    total_products = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    # Products at or below their low-stock threshold
    low_stock_items = connection.execute("""
        SELECT COUNT(*) FROM products
        WHERE quantity <= low_stock_threshold
    """).fetchone()[0]

    # NEW: Count products that are completely out of stock
    out_of_stock_items = connection.execute("""
        SELECT COUNT(*) FROM products
        WHERE quantity = 0
    """).fetchone()[0]

    # Total stock transactions
    total_transactions = connection.execute(
        "SELECT COUNT(*) FROM stock_transactions"
    ).fetchone()[0]

    # Search products
    search = request.args.get("search", "").strip()

    products = connection.execute("""
        SELECT * FROM products
        WHERE name LIKE ?
        ORDER BY id DESC
    """, (f"%{search}%",)).fetchall()

    # Fill missing names for transactions whose products still exist
    connection.execute("""
        UPDATE stock_transactions
        SET product_name = (
            SELECT products.name
            FROM products
            WHERE products.id = stock_transactions.product_id
        )
        WHERE product_name IS NULL
          AND product_id IS NOT NULL
    """)
    connection.commit()

    
   
    # Transaction history filters
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()
    period = request.args.get("period", "today").strip()

    date_condition = ""
    params = []

    if from_date and to_date:
        date_condition = """
            WHERE date(stock_transactions.created_at) >= date(?)
              AND date(stock_transactions.created_at) <= date(?)
        """
        params = [from_date, to_date]
    elif period == "yesterday":
        date_condition = """
            WHERE date(stock_transactions.created_at) = date('now', '-1 day')
        """
    elif period == "7days":
        date_condition = """
            WHERE date(stock_transactions.created_at) >= date('now', '-6 days')
        """
    else:
        date_condition = """
            WHERE date(stock_transactions.created_at) = date('now')
        """

    # Fetch all transactions for the selected period
    transactions = connection.execute(f"""
        SELECT
            stock_transactions.id,
            stock_transactions.product_id,
            stock_transactions.transaction_type,
            stock_transactions.quantity,
            datetime(stock_transactions.created_at, '+5 hours', '+30 minutes') AS created_at,
            COALESCE(
                stock_transactions.product_name,
                products.name,
                'Deleted product'
            ) AS product_name
        FROM stock_transactions
        LEFT JOIN products
            ON products.id = stock_transactions.product_id
        {date_condition}
        ORDER BY stock_transactions.id DESC
    """, params).fetchall()



    connection.close()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        low_stock_items=low_stock_items,
        out_of_stock_items=out_of_stock_items,
        total_transactions=total_transactions,
        products=products,
        transactions=transactions,
        search=search,
        period=period,
        from_date=from_date,
        to_date=to_date
    )



# Add product
@app.route("/add-product", methods=["POST"])
@admin_required
def add_product():
    name = request.form.get("name", "").strip()
    try:
        quantity = int(request.form.get("quantity", "0"))
        threshold = int(request.form.get("threshold", "10"))
    except ValueError:
        flash("Quantity and threshold must be whole numbers.")
        return redirect(url_for("dashboard"))

    if not name or quantity < 0 or threshold < 0:
        flash("Enter valid product details.")
        return redirect(url_for("dashboard"))

    connection = get_db()

    try:
        # Check whether the product already exists
        existing_product = connection.execute(
            "SELECT id FROM products WHERE name = ? COLLATE NOCASE",
            (name,)
        ).fetchone()

        if existing_product:
            flash("Product already exists. Use Stock In to increase its quantity.")
            return redirect(url_for("dashboard"))

        cursor = connection.execute("""
            INSERT INTO products
                (name, quantity, low_stock_threshold)
            VALUES (?, ?, ?)
        """, (name, quantity, threshold))

        # Record initial stock along with product name
        if quantity > 0:
            connection.execute("""
                INSERT INTO stock_transactions
                    (product_id, product_name, transaction_type, quantity)
                VALUES (?, ?, ?, ?)
            """, (cursor.lastrowid, name, "STOCK_IN", quantity))

        connection.commit()
        flash("Product added successfully.")

    except sqlite3.Error:
        connection.rollback()
        flash("Could not add product. Please try again.")

    finally:
        connection.close()

    return redirect(url_for("dashboard"))


# Update stock
@app.route("/update-stock", methods=["POST"])
@login_required
def update_stock():    
    try:
        product_id = int(request.form.get("product_id", "0"))
        quantity = int(request.form.get("quantity", "0"))
    except ValueError:
        flash("Please enter valid numbers.")
        return redirect(url_for("dashboard"))

    action = request.form.get("action", "")

    if quantity <= 0 or action not in ("STOCK_IN", "STOCK_OUT"):
        flash("Choose a valid action and enter a quantity greater than zero.")
        return redirect(url_for("dashboard"))

    connection = get_db()

    try:
        product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if product is None:
            flash("Product not found.")
            return redirect(url_for("dashboard"))

        if action == "STOCK_OUT" and product["quantity"] < quantity:
            flash("Not enough stock available.")
            return redirect(url_for("dashboard"))

        if action == "STOCK_IN":
            new_quantity = product["quantity"] + quantity
        else:
            new_quantity = product["quantity"] - quantity

        connection.execute(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (new_quantity, product_id)
        )

        # Save product name with every stock transaction
        connection.execute("""
            INSERT INTO stock_transactions
                (product_id, product_name, transaction_type, quantity)
            VALUES (?, ?, ?, ?)
        """, (product_id, product["name"], action, quantity))

        connection.commit()
        flash("Stock updated successfully.")

    except sqlite3.Error:
        connection.rollback()
        flash("Could not update stock. Please try again.")

    finally:
        connection.close()

    return redirect(url_for("dashboard"))


# Delete product but preserve transaction history
@app.route("/delete-product", methods=["POST"])
@admin_required
def delete_product():
    try:
        product_id = int(request.form.get("product_id", "0"))
    except ValueError:
        flash("Invalid product ID.")
        return redirect(url_for("dashboard"))

    connection = get_db()

    try:
        product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if product is None:
            flash("Product not found.")
            return redirect(url_for("dashboard"))

        # Preserve product name in all related transactions
        connection.execute("""
            UPDATE stock_transactions
            SET product_name = ?,
                product_id = NULL
            WHERE product_id = ?
        """, (product["name"], product_id))

        connection.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,)
        )

        connection.commit()
        flash("Product deleted. Transaction history has been preserved.")

    except sqlite3.Error:
        connection.rollback()
        flash("Could not delete product. Please try again.")

    finally:
        connection.close()

    return redirect(url_for("dashboard"))


# Start Flask application
if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
