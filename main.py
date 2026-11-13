import sqlite3
import re
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "inventory.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

print("Connected to:", DB_PATH)

def create_tables():

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        phone TEXT,
        email TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        category TEXT,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        supplier_id INTEGER,
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        transaction_type TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        transaction_date TEXT NOT NULL,
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
    )
    """)


    cursor.execute("""
    INSERT OR IGNORE INTO users
    (username, password, role)
    VALUES (?, ?, ?)
    """, ("bipin", "admin123", "admin"))

    conn.commit()


def get_valid_username():

    while True:
        username = input("Enter username: ")

        if re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
            return username

        print("Username must contain 3-20 letters, numbers or underscores.")


def get_valid_password():

    while True:
        password = input("Enter password: ")

        if re.fullmatch(r"[A-Za-z0-9@#$]{6,20}", password):
            return password

        print("Password must be 6-20 characters.")
        print("Allowed characters: letters, numbers, @, #, $")


def get_integer(message):

    while True:
        try:
            value = int(input(message))

            if value < 0:
                print("Enter a positive number.")
                continue

            return value

        except ValueError:
            print("Please enter a valid integer.")


def get_float(message):

    while True:
        try:
            value = float(input(message))

            if value < 0:
                print("Enter a positive amount.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


#user reg

def register_user():

    print("User registration")

    username = get_valid_username()
    password = get_valid_password()

    try:
        cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
        """, (username, password, "user"))

        conn.commit()

        print("Registration successful!")

    except sqlite3.IntegrityError:
        print("Username already exists.")


#login

def login():

    print("Login")

    username = input("Username: ")
    password = input("Password: ")

    try:
        cursor.execute("""
        SELECT user_id, username, role
        FROM users
        WHERE username = ? AND password = ?
        """, (username, password))

        user = cursor.fetchone()

        if user is None:
            print("Invalid username or password.")
            return None

        print("\nLogin successful!")
        print("Welcome", user[1])

        return user

    except sqlite3.Error as e:
        print("Login error:", e)
        return None


#supplier

def add_supplier():

    print("Adding Supplier")

    name = input("Supplier name: ")
    phone = input("Phone number: ")
    email = input("Email: ")

    try:
        cursor.execute("""
        INSERT INTO suppliers
        (supplier_name, phone, email)
        VALUES (?, ?, ?)
        """, (name, phone, email))

        conn.commit()

        print("Supplier added successfully!")

    except sqlite3.Error as e:
        print("Error:", e)


#view supplier

def view_suppliers():

    cursor.execute("SELECT * FROM suppliers")

    suppliers = cursor.fetchall()

    if not suppliers:
        print("No suppliers found.")
        return

    print("Supplier list")

    for supplier in suppliers:
        print(
            "ID:", supplier[0],
            " Name:", supplier[1],
            "Phone:", supplier[2],
            "Email:", supplier[3]
        )


#update

def update_supplier():

    view_suppliers()

    supplier_id = get_integer("Enter supplier ID: ")

    cursor.execute("""
    SELECT * FROM suppliers
    WHERE supplier_id = ?
    """, (supplier_id,))

    supplier = cursor.fetchone()

    if supplier is None:
        print("Supplier not found")
        return

    name = input("New supplier name: ")
    phone = input("New phone: ")
    email = input("New email: ")

    try:
        cursor.execute("""
        UPDATE suppliers
        SET supplier_name = ?, phone = ?, email = ?
        WHERE supplier_id = ?
        """, (name, phone, email, supplier_id))

        conn.commit()

        print("Supplier updated successfully!")

    except sqlite3.Error as e:
        print("Error:", e)


#dlt supplier

def delete_supplier():

    view_suppliers()

    supplier_id = get_integer("Enter supplier ID: ")

    try:
        cursor.execute("""
        DELETE FROM suppliers
        WHERE supplier_id = ?
        """, (supplier_id,))

        if cursor.rowcount == 0:
            print("Supplier not found.")
        else:
            conn.commit()
            print("Supplier deleted successfully!")

    except sqlite3.IntegrityError:
        conn.rollback()
        print("Cannot delete supplier because products are linked to it.")


#adding product

def add_product():

    print("add product")

    name = input("Product name: ")
    category = input("Category: ")

    price = get_float("Price: ")
    quantity = get_integer("Initial quantity: ")

    view_suppliers()

    supplier_id = get_integer("Enter supplier ID: ")

    try:
        cursor.execute("""
        INSERT INTO products
        (product_name, category, price, quantity, supplier_id)
        VALUES (?, ?, ?, ?, ?)
        """, (name, category, price, quantity, supplier_id))

        product_id = cursor.lastrowid

        if quantity > 0:
            cursor.execute("""
            INSERT INTO stock_transactions
            (product_id, transaction_type, quantity, transaction_date)
            VALUES (?, ?, ?, ?)
            """, (
                product_id,
                "IN",
                quantity,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        conn.commit()

        print("Product added successfully!")

    except sqlite3.IntegrityError:
        conn.rollback()
        print("Invalid supplier ID.")

    except sqlite3.Error as e:
        conn.rollback()
        print("Error:", e)


#view
def view_products():

    cursor.execute("""
    SELECT
        products.product_id,
        products.product_name,
        products.category,
        products.price,
        products.quantity,
        suppliers.supplier_name

    FROM products

    LEFT JOIN suppliers
    ON products.supplier_id = suppliers.supplier_id
    """)

    products = cursor.fetchall()

    if not products:
        print("No products found.")
        return

    print("product arsenal")

    for product in products:

        print(
            "ID:", product[0],
            "Name:", product[1],
            "Category:", product[2],
            "Price:", product[3],
            "Quantity:", product[4],
            "Supplier:", product[5]
        )

#search product

def search_product():

    print("\n--- SEARCH PRODUCTS ---")
    print("1. Search by Product ID")
    print("2. Search by Product Name")
    print("3. Search by Category")
    print("4. Search by Supplier ID")
    print("5. Search by Supplier Name")

    choice = input("Enter your choice: ")

    if choice == "1":

        product_id = input("Enter Product ID: ")

        cursor.execute("""
            SELECT p.*, s.supplier_name
            FROM products p
            LEFT JOIN suppliers s
            ON p.supplier_id = s.supplier_id
            WHERE p.product_id = ?
        """, (product_id,))

    elif choice == "2":

        name = input("Enter Product Name: ")

        cursor.execute("""
            SELECT p.*, s.supplier_name
            FROM products p
            LEFT JOIN suppliers s
            ON p.supplier_id = s.supplier_id
            WHERE p.product_name LIKE ?
        """, ('%' + name + '%',))

    elif choice == "3":

        category = input("Enter Category: ")

        cursor.execute("""
            SELECT p.*, s.supplier_name
            FROM products p
            LEFT JOIN suppliers s
            ON p.supplier_id = s.supplier_id
            WHERE p.category LIKE ?
        """, ('%' + category + '%',))

    elif choice == "4":

        supplier_id = input("Enter Supplier ID: ")

        cursor.execute("""
            SELECT p.*, s.supplier_name
            FROM products p
            LEFT JOIN suppliers s
            ON p.supplier_id = s.supplier_id
            WHERE p.supplier_id = ?
        """, (supplier_id,))

    elif choice == "5":

        supplier_name = input("Enter Supplier Name: ")

        cursor.execute("""
            SELECT p.*, s.supplier_name
            FROM products p
            LEFT JOIN suppliers s
            ON p.supplier_id = s.supplier_id
            WHERE s.supplier_name LIKE ?
        """, ('%' + supplier_name + '%',))

    else:
        print("Invalid choice")
        return

    results = cursor.fetchall()

    if not results:
        print("No matching products found.")

    else:
        for product in results:
            print("-" * 40)
            print("Product ID:", product[0])
            print("Product Name:", product[1])
            print("Category:", product[2])
            print("Price:", product[3])
            print("Quantity:", product[4])
            print("Supplier:", product[-1])

#update product

def update_product():

    view_products()

    product_id = get_integer("Enter product ID: ")

    cursor.execute("""
    SELECT * FROM products
    WHERE product_id = ?
    """, (product_id,))

    product = cursor.fetchone()

    if product is None:
        print("Product not found.")
        return

    name = input("New product name: ")
    category = input("New category: ")
    price = get_float("New price: ")

    view_suppliers()

    supplier_id = get_integer("New supplier ID: ")

    try:
        cursor.execute("""
        UPDATE products

        SET product_name = ?,
            category = ?,
            price = ?,
            supplier_id = ?

        WHERE product_id = ?
        """, (name, category, price, supplier_id, product_id))

        if cursor.rowcount == 0:
            print("Product not found.")
        else:
            conn.commit()
            print("Product updated successfully!")

    except sqlite3.IntegrityError:
        conn.rollback()
        print("Invalid supplier ID.")

    except sqlite3.Error as e:
        conn.rollback()
        print("Error:", e)


#dlt product

def delete_product():

    view_products()

    product_id = get_integer("Enter product ID: ")

    try:
        cursor.execute("""
        DELETE FROM products
        WHERE product_id = ?
        """, (product_id,))

        if cursor.rowcount == 0:
            print("Product not found.")
        else:
            conn.commit()
            print("Product deleted successfully!")

    except sqlite3.IntegrityError:
        conn.rollback()
        print("Cannot delete product because stock transactions exist.")


#Stock IN/out

def update_stock():

    print("Stock management")

    view_products()

    product_id = get_integer("Enter product ID: ")

    cursor.execute("""
    SELECT quantity FROM products
    WHERE product_id = ?
    """, (product_id,))

    product = cursor.fetchone()

    if product is None:
        print("Product not found.")
        return

    print("\n1. Stock IN")
    print("2. Stock OUT")

    choice = input("Choose: ")

    if choice not in ["1", "2"]:
        print("Invalid choice.")
        return

    quantity = get_integer("Enter quantity: ")

    if quantity == 0:
        print("Quantity must be greater than zero.")
        return

    current_quantity = product[0]

    if choice == "1":

        new_quantity = current_quantity + quantity
        transaction_type = "IN"

    else:

        if quantity > current_quantity:
            print("Insufficient stock!")
            return

        new_quantity = current_quantity - quantity
        transaction_type = "OUT"

    try:
        cursor.execute("""
        UPDATE products
        SET quantity = ?
        WHERE product_id = ?
        """, (new_quantity, product_id))

        cursor.execute("""
        INSERT INTO stock_transactions
        (product_id, transaction_type, quantity, transaction_date)
        VALUES (?, ?, ?, ?)
        """, (
            product_id,
            transaction_type,
            quantity,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

        print("Stock updated successfully!")
        print("Available stock:", new_quantity)

    except sqlite3.Error as e:
        conn.rollback()
        print("Error:", e)


#transaction history

def view_transactions():

    cursor.execute("""
    SELECT
        stock_transactions.transaction_id,
        products.product_name,
        stock_transactions.transaction_type,
        stock_transactions.quantity,
        stock_transactions.transaction_date

    FROM stock_transactions

    LEFT JOIN products
    ON stock_transactions.product_id = products.product_id

    ORDER BY stock_transactions.transaction_id DESC
    """)

    transactions = cursor.fetchall()

    if not transactions:
        print("No transactions found.")
        return

    print("stock transaction history")

    for transaction in transactions:

        print(
            "Transaction ID:", transaction[0],
            "Product:", transaction[1],
            "Type:", transaction[2],
            "Quantity:", transaction[3],
            "Date:", transaction[4]
        )


#admin menu

def admin_menu():

    while True:

        print("Admin menu")

        print("1. Add Supplier")
        print("2. View Suppliers")
        print("3. Update Supplier")
        print("4. Delete Supplier")

        print("5. Add Product")
        print("6. View Products")
        print("7. Search Product")
        print("8. Update Product")
        print("9. Delete Product")

        print("10. Update Stock")
        print("11. View Transactions")

        print("12. Register User")
        print("13. Logout")

        choice = input("Enter choice: ")

        if choice == "1":
            add_supplier()

        elif choice == "2":
            view_suppliers()

        elif choice == "3":
            update_supplier()

        elif choice == "4":
            delete_supplier()

        elif choice == "5":
            add_product()

        elif choice == "6":
            view_products()

        elif choice == "7":
            search_product()

        elif choice == "8":
            update_product()

        elif choice == "9":
            delete_product()

        elif choice == "10":
            update_stock()

        elif choice == "11":
            view_transactions()

        elif choice == "12":
            register_user()

        elif choice == "13":
            print("Logged out.")
            break

        else:
            print("Invalid choice!")


#nuser menu

def user_menu():

    while True:

        print("user menu")

        print("1. View Products")
        print("2. Search Product")
        print("3. View Suppliers")
        print("4. Logout")

        choice = input("Enter choice: ")

        if choice == "1":
            view_products()

        elif choice == "2":
            search_product()

        elif choice == "3":
            view_suppliers()

        elif choice == "4":
            print("Logged out.")
            break

        else:
            print("Invalid choice!")


# ==========================================
# 19. MAIN PROGRAM
# ==========================================

def main():

    create_tables()

    while True:

        print("INVENTORY MANAGEMENT SYSTEM")

        print("1. Login")
        print("2. Register")
        print("3. Exit")

        choice = input("\nEnter choice: ")

        if choice == "1":

            user = login()

            if user is not None:

                if user[2] == "admin":
                    admin_menu()

                else:
                    user_menu()

        elif choice == "2":

            register_user()

        elif choice == "3":

            print("Thank you for using the system!")
            break

        else:

            print("Invalid choice!")


#main

try:

    main()

except sqlite3.Error as e:

    print("Database error:", e)

finally:

    conn.close()
