from flask import Flask, request, redirect, url_for, session, render_template, jsonify, json
import mysql.connector
import logging

admin_phone = '4447778888'
admin_password = "hashedpassword5"

app = Flask(__name__)
app.secret_key = "123456"  # Set a secret key for session management

logging.basicConfig(level = logging.DEBUG)  # Configure logging


def get_database_connection():
    return mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "Climber@3001",
        database = "DailyHarbour"
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

        return json.dumps(cart_json)
    except Exception as e:
        print("Error fetching cart data:", e)
        return json.dumps([])


def get_cart_data2(user_id):
    db = get_database_connection()
    cursor = db.cursor()
    query = "SELECT product.product_id, add_to_cart.number_of_units FROM product NATURAL JOIN add_to_cart WHERE add_to_cart.user_id = %s"

    cursor.execute(query, (user_id,))
    cart_data = cursor.fetchall()
    cursor.close()
    db.close()

    # convert fetched data to python dictionary
    cart_dict = {}
    for item in cart_data:
        cart_dict[item[0]] = item[1]
    
    return cart_dict


@app.route('/get_cart_data', methods=['GET'])
def cart():
    user_id = session["user_id"]

    if user_id:
        cart_data = get_cart_data(user_id)
        return cart_data
    else:
        return "User not authenticated"


@app.route('/add_user', methods=["POST"])
def add_user():
    try:
        data = request.get_json()
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

        if not products:
            return jsonify({'error': 'No products provided'}), 400

        user_id = session.get("user_id")
        if user_id is None:
            return jsonify({'error': 'User not authenticated'}), 401

        db = get_database_connection()
        cursor = db.cursor()

        for product in products:
            product_id = get_product_id(cursor, product.get('name'))
            add_to_cart_db(cursor, db, user_id, product_id,
                    product.get('quantity'))
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
    

def get_number_of_products(cursor, user_id):
    try:
        query = '''SELECT sum(number_of_units) AS total_products from add_to_cart where user_id = %s;'''

        cursor.execute(query, (user_id,))
        value = cursor.fetchone()
        return value[0] if value else None
    except Exception as e:
        print(e)
        return None


# returns the order number
def orderDetails(address):
    user_id = session.get("user_id")

    if user_id:
        db = get_database_connection()
        cursor = db.cursor()

        order_value = get_order_value(cursor, user_id)
        number_of_products = get_number_of_products(cursor, user_id)
        query = '''INSERT INTO order_details (user_id, address_name, order_date, total_number_of_items, order_value, delivery_charge) VALUES (%s, %s, %s, %s, %s, %s);'''
        cursor.execute(query, (user_id, address, '2021-09-01', number_of_products, order_value, 0))
        db.commit()

        # obtain order_no of the order
        query = '''SELECT order_no from order_details where user_id = %s and order_date = %s;'''
        cursor.execute(query, (user_id, '2021-09-01'))
        order_no = cursor.fetchone()

        cursor.close()
        db.close()

        return order_no[0] if order_no else None


# def orderProducts(order_no):
#     user_id = session.get("user_id")

#     if user_id:
#         # first get the products in the cart
#         cart_data = get_cart_data2(user_id)
#         db = get_database_connection()
#         cursor = db.cursor()

#         for product_id, quantity in cart_data.items():
#             query = '''INSERT INTO order_products (order_no, product_id, number_of_units) VALUES (%s, %s, %s);'''
#             cursor.execute(query, (order_no, product_id, quantity))
#             db.commit()

@app.route('/send_address', methods = ["POST"])
def get_address():
    user_id = session.get("user_id")

    try:
        data = request.get_json()
        address = data.get('address')
        order_no = orderDetails(address)
        # orderProducts(order_no)
        
        # empty the cart for the user once the order has been created
        db = get_database_connection()
        cursor = db.cursor()
        query = "DELETE FROM add_to_cart where user_id = %s"
        cursor.execute(query, (user_id,))
        db.commit()

        return jsonify({'message': 'Fetched address successfully'})
    except:
        return jsonify({'error': 'Address not provided'}), 400


if __name__ == "__main__":
    app.run(debug = True)
