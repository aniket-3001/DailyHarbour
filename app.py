
from flask import Flask, request, redirect, url_for, session, render_template, jsonify, json
import mysql.connector
import logging

admin_phone = '4447778888'
admin_password = "hashedpassword5"

app = Flask(__name__)
app.secret_key = "123456"

logging.basicConfig(level=logging.DEBUG)


def get_database_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Climber@3001",
        database="DailyHarbour"
    )


@app.route('/homepage', methods=["GET"])
def homepage():
    return render_template("homepage.html")


@app.route('/admin', methods=["GET"])
def admin():
    return render_template("admin.html")


def get_product_id(cursor, name):
    query = "SELECT product_id FROM product WHERE product_name = %s"
    cursor.execute(query, (name,))  # the comma is important
    product_data = cursor.fetchone()
    # print(product_data)
    return product_data[0] if product_data else None


def add_to_cart_db(cursor, db, user_id, product_id, quantity):
    try:
        insert_query = "INSERT INTO add_to_cart (user_id, product_id, number_of_units) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (user_id, product_id, quantity))
        db.commit()
    except Exception as e:
        print(e)


@app.route('/', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]

        if phone == admin_phone and password == admin_password:
            session["user_id"] = "admin"  # take note
            return redirect(url_for("admin"))

        if "login_attempts" not in session:
            session["login_attempts"] = 0

        # Check user credentials from the database
        db = get_database_connection()
        cursor = db.cursor()
        query = "SELECT * FROM user WHERE mobile_number= %s AND password_hash= %s"
        cursor.execute(query, (phone, password))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        if user_data:
            # Successful login, reset login attempts
            session["user_id"] = user_data[0]
            session.pop("login_attempts", None)
            return redirect(url_for("homepage"))  # Redirect to user profile
        else:
            # Failed login attempt
            session["login_attempts"] += 1
            remaining_attempts = 3 - session.get("login_attempts", 0)
            if remaining_attempts <= 0:
                session.pop("login_attempts", None)  # Reset login attempts
                return "Too many failed attempts. Please try again later."

    remaining_attempts = 3 - session.get("login_attempts", 0)
    return render_template("login.html",  remaining_attempts=remaining_attempts)


# Define a route to handle the timer expiration
@app.route('/timer_expired', methods=["POST"])
def timer_expired():
    user_id = session.get("user_id")

    if user_id:
        # Implement logic to empty the user's cart in the database
        try:
            db = get_database_connection()
            cursor = db.cursor()
            delete_query = "DELETE FROM add_to_cart WHERE user_id = %s"
            cursor.execute(delete_query, (user_id,))
            db.commit()
            cursor.close()
            db.close()
            return jsonify({'message': 'User cart emptied successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'User not authenticated'}), 401


# Function to fetch cart data from the database (private function)
def get_cart_data(user_id):
    try:
        db = get_database_connection()
        cursor = db.cursor()
        query = "SELECT product.product_name, add_to_cart.number_of_units, product.selling_price FROM product NATURAL JOIN add_to_cart WHERE add_to_cart.user_id = %s"

        cursor.execute(query, (user_id,))
        cart_data = cursor.fetchall()
        cursor.close()
        db.close()

        # Convert fetched data to JSON format
        cart_json = []
        for item in cart_data:
            cart_json.append(
                {'product_name': item[0], 'quantity': item[1], 'price': item[2] * item[1]})

        print(cart_json)
        return json.dumps(cart_json)
    except Exception as e:
        print("Error fetching cart data:", e)
        return json.dumps([])


# Route to render the cart page
@app.route('/get_cart_data', methods=['GET'])
def cart():
    user_id = session["user_id"]

    if user_id:
        cart_data = get_cart_data(user_id)
        return cart_data
    else:
        print("Something failed")
        return "User not authenticated"


@app.route('/add_user', methods=["POST"])
def add_user():
    try:
        data = request.get_json()
        print(data)
        id = data.get('user_id')  # Assuming the JSON key is 'user_id'
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        middle_name = data.get('middle_name')
        gender = data.get('gender')
        dob = data.get('date_of_birth')
        phone = data.get('mobile_number')
        password = data.get('password_hash')

        db = get_database_connection()
        cursor = db.cursor()
        try:
            query = "INSERT INTO user (mobile_number, first_name, middle_name, last_name, password_hash, gender, date_of_birth) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (phone, first_name, middle_name,
                                last_name, password, gender, dob))
            db.commit()
            return jsonify({'message': 'User added successfully'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Database failed to add user'}), 500
        finally:
            cursor.close()
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_user', methods=["POST"])
def delete_user():
    try:
        data = request.get_json()
        print(data)
        id = data.get('user_id')
        db = get_database_connection()
        cursor = db.cursor()
        try:
            query = "DELETE FROM user WHERE user_id = %s"
            cursor.execute(query, (id,))
            db.commit()
            return jsonify({'message': 'User deleted successfully'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Database failed to delete user'}), 500
        finally:
            cursor.close()
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_product_id(cursor, name):
    query = "SELECT product_id FROM product WHERE product_name = %s"
    cursor.execute(query, (name,))
    product_data = cursor.fetchone()
    # print(product_data)
    return product_data[0] if product_data else None


def get_num_of_units(cursor, user_id):
    try:
        query = '''SELECT SUM(total_units_ordered) AS total_ordered_units
                    FROM (
                        SELECT SUM(number_of_units) AS total_units_ordered
                        FROM add_to_cart
                        WHERE user_id = %s
                        GROUP BY product_id
                    ) AS user_orders;'''
        cursor.execute(query, (user_id,))
        # Fetch the first column of the first row
        total_ordered_units = cursor.fetchone()[0]
        print(total_ordered_units)
        return total_ordered_units if total_ordered_units else None
    except Exception as e:
        print(e)
        return None


def get_order_value(cursor, user_id):
    try:
        query = '''SELECT SUM(p.selling_price * c.number_of_units) AS total_price
                    FROM add_to_cart AS c
                    JOIN product AS p ON c.product_id = p.product_id
                    WHERE c.user_id = %s;'''

        cursor.execute(query, (user_id,))
        value = cursor.fetchone()
        return value[0] if value else None
    except Exception as e:
        print(e)
        return None


def get_price(cursor, product_id):
    try:
        query = "SELECT selling_price FROM product WHERE product_id = %s;"
        cursor.execute(query, (product_id,))
        price = cursor.fetchone()
        return price[0] if price else None
    except Exception as e:
        print(e)
        return None


def order_details_db(cursor, db, user_id, coupon_code, address_name, order_date, total_number_of_items, order_value, delivery_charge):
    try:
        insert_query = "INSERT INTO order_details (user_id, coupon_code, address_name, order_date, total_number_of_items, order_value, delivery_charge) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (user_id, coupon_code, address_name,
                    order_date, total_number_of_items, order_value, delivery_charge))
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        print(e)
        return None


def order_products_db(cursor, db, order_no, product_id, number_of_units, price_per_unit):
    print("reached order_products_db")
    try:
        insert_query = "INSERT INTO order_products (order_no, product_id, number_of_units, price_per_unit) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (order_no, product_id,
                    number_of_units, price_per_unit))
        db.commit()
    except Exception as e:
        print(e)


@app.route('/order_details', methods=['POST'])
def order_details():
    try:
        data = request.get_json()
        address = data.get("address")
        user_id = session.get("user_id")

        if user_id is None:
            return jsonify({'error': 'User not authenticated'}), 401

        print(user_id)
        print(address)
        db = get_database_connection()
        cursor = db.cursor()
        num_of_units = get_num_of_units(cursor, user_id)
        order_value = get_order_value(cursor, user_id)
        order_no = order_details_db(
            cursor, db, user_id, None, address, '2024-03-31', num_of_units, order_value, 0)
        print("this is order number", order_no)
        cart_query = "SELECT * FROM add_to_cart WHERE user_id = %s"
        cursor.execute(cart_query, (user_id,))
        result = cursor.fetchall()
        cart_items = []

        for row in result:
            print("new")
            cart_item = {}
            for i, column in enumerate(cursor.description):
                cart_item[column[0]] = row[i]
            cart_items.append(cart_item)

        for item in cart_items:
            price = get_price(cursor, item["product_id"])
            print(item["product_id"])
            print(item["number_of_units"])
            print(price)
            order_products_db(cursor, db, order_no,
                            item["product_id"], item["number_of_units"], price)
        return jsonify({'message': 'Bill Paid'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/products', methods=["GET"])
def products():
    return render_template("products.html")


@app.route('/display_user', methods=["GET"])
def display_users():
    try:
        db = get_database_connection()
        cursor = db.cursor()
        query = "SELECT * FROM user"
        cursor.execute(query)
        users = cursor.fetchall()
        cursor.close()
        db.close()

        # Convert the users data to a list of dictionaries for JSON serialization
        users_list = []
        for user in users:
            user_dict = {
                'id': user[0],
                'first_name': user[1],
                'last_name': user[2],
                # Add other user attributes as needed
            }
            users_list.append(user_dict)

        return jsonify(users_list)  # Return JSON response with user details
    except Exception as e:
        # Return error message with status code 500
        return jsonify({'error': str(e)}), 500

# This route is used to fetch the products added by user to their cart on the frontend


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.get_json()
        products = data.get('products')
        # print(products)

        if not products:
            return jsonify({'error': 'No products provided'}), 400

        user_id = session.get("user_id")
        if user_id is None:
            return jsonify({'error': 'User not authenticated'}), 401

        # print("reach here")
        db = get_database_connection()
        cursor = db.cursor()
        # print("reach here2")

        for product in products:
            # print(product.get('name'))
            # print(product.get('quantity'))
            product_id = get_product_id(cursor, product.get('name'))
            # print(user_id, product_id, product.get('quantity'))
            add_to_cart_db(cursor, db, user_id, product_id,
                        product.get('quantity'))
            # print("data added")
        return jsonify({'message': 'Items added to cart successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/checkout', methods=["GET"])
def checkout():
    return render_template("checkout.html")


@app.route('/profile', methods=["GET"])
def profile():
    return render_template("profile.html")


@app.route('/orderPlaced', methods=["GET"])
def orderPlaced():
    return render_template("orderPlaced.html")


@app.route('/add_product', methods=["POST"])
def add_product():
    print("Reached here")
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided in the request'}), 400

        product_name = data.get('product_name')
        unit_of_measure = data.get('unit_of_measure')
        quantity_per_unit = data.get('quantity_per_unit')
        available_units = data.get('available_units')
        mrp = data.get('mrp')
        selling_price = data.get('selling_price')
        manufacturer_name = data.get('manufacturer_name')
        product_description = data.get('product_description')
        category_id = data.get('category_id')
        print(product_name, unit_of_measure, quantity_per_unit, available_units,
            mrp, selling_price, manufacturer_name, product_description, category_id)
        if not (product_name and quantity_per_unit and available_units and mrp and selling_price and category_id):
            return jsonify({'error': 'Missing required fields'}), 400

        db = get_database_connection()
        cursor = db.cursor()
        try:
            query = "INSERT INTO product (product_name, unit_of_measure, quantity_per_unit, available_units, mrp, selling_price, manufacturer_name, product_description, category_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (product_name, unit_of_measure, quantity_per_unit, available_units,
                        mrp, selling_price, manufacturer_name, product_description, category_id))
            db.commit()
            return jsonify({'message': 'Product added successfully'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Database failed to add product'}), 500
        finally:
            cursor.close()
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/display_product', methods=["GET"])
def display_product():
    try:
        db = get_database_connection()
        cursor = db.cursor()
        query = "SELECT * FROM product"
        cursor.execute(query)
        users = cursor.fetchall()
        cursor.close()
        db.close()

        # Convert the users data to a list of dictionaries for JSON serialization
        users_list = []
        for user in users:
            user_dict = {
                'product_name': user[1],
                'selling_price': user[2],
                # Add other user attributes as needed
            }
            users_list.append(user_dict)
        print(users_list)
        return jsonify(users_list)  # Return JSON response with user details
    except Exception as e:
        # Return error message with status code 500
        return jsonify({'error': str(e)}), 500


@app.route('/delete_product', methods=["POST"])
def delete_product():
    try:
        print("Reached here delete product")
        data = request.get_json()
        print(data)
        id = data.get('product_id')
        db = get_database_connection()
        cursor = db.cursor()
        print(id)
        try:
            query = "DELETE FROM product WHERE product_id = %s"
            cursor.execute(query, (id,))
            db.commit()
            print("Product deleted")
            return jsonify({'message': 'Product deleted successfully'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Database failed to delete product'}), 500
        finally:
            cursor.close()
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
