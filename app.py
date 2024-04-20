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
        host = "127.0.0.1",
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

# conflicting transaction
def add_to_cart_db(cursor, db, user_id, product_id, quantity):
    try:
        if db.in_transaction:
            db.commit()
        db.start_transaction()  # Starting the transaction
        insert_query = "INSERT INTO add_to_cart (user_id, product_id, number_of_units) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (user_id, product_id, quantity))
        db.commit()  # Committing the transaction
    except Exception as e:
        db.rollback()  # Rolling back the transaction if an exception occurs
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
# non-conflicting transaction
@app.route('/timer_expired', methods=["POST"])
def timer_expired():
    user_id = session.get("user_id")

    if user_id:
        # Implement logic to empty the user's cart in the database
        try:
            db = get_database_connection()
            cursor = db.cursor()
            
            if db.in_transaction:
                db.commit()

            db.start_transaction()
            query = "DELETE FROM add_to_cart WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            db.commit()
            return jsonify({'message': 'Cart emptied successfully'}), 200
        except Exception as e:
            print(e)
            db.rollback()
            return jsonify({'error': 'Database failed to empty cart'}), 500
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
    query = "SELECT product.product_id, add_to_cart.number_of_units, product.selling_price FROM product NATURAL JOIN add_to_cart WHERE add_to_cart.user_id = %s"

    cursor.execute(query, (user_id,))
    cart_data = cursor.fetchall()
    cursor.close()
    db.close()

    # convert fetched data to python dictionary
    cart_dict = {}
    for item in cart_data:
        product_id = item[0]
        number_of_units = item[1]
        selling_price = item[2]
        cart_dict[product_id] = {
            'number_of_units': number_of_units,
            'selling_price': selling_price
        }

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
            if (db.in_transaction):
                db.commit()

            db.start_transaction()
            query = "DELETE FROM user WHERE user_id = %s"
            cursor.execute(query, (id,))
            db.commit()
            return jsonify({'message': 'User deleted successfully'}), 200
        except Exception as e:
            print(e)
            db.rollback()
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
                'mobile_number': user[1],
                'first_name': user[2],
                'last_name': user[4],
                # Add other user attributes as needed
            }
            users_list.append(user_dict)

        return jsonify(users_list)  # Return JSON response with user details
    except Exception as e:
        # Return error message with status code 500
        return jsonify({'error': str(e)}), 500


# non-conflicting transaction
@app.route('/add_product', methods=["POST"])
def add_product():
    try:
        data = request.get_json()
        print(data)
        product_name = data.get('product_name')
        unit_of_measure = data.get('unit_of_measure')
        selling_price = data.get('selling_price')
        available_units = data.get('avail_units')
        category_id = data.get('category_id')
        mrp = data.get('mrp')
        quantity_per_unit = data.get('quantity_per_unit')

        db = get_database_connection()
        cursor = db.cursor()

        if db.in_transaction:
            db.commit()

        db.start_transaction()

        query = '''INSERT INTO product (product_name, unit_of_measure, selling_price, available_units, category_id, mrp, quantity_per_unit) VALUES (%s, %s, %s, %s, %s, %s, %s);'''

        cursor.execute(query, (product_name, unit_of_measure, selling_price, available_units, category_id, mrp, quantity_per_unit))
        db.commit()

        cursor.close()
        db.close()

        return jsonify({'message': 'Product added successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Product not added'}), 500
    
@app.route('/delete_product', methods=["POST"])
def delete_product():
    try:
        data = request.get_json()
        id = data.get('product_id')
        db = get_database_connection()
        cursor = db.cursor()
        if db.in_transaction:
            db.commit()

        db.start_transaction()
        try:
            query = "DELETE FROM product WHERE product_id = %s"
            cursor.execute(query, (id,))
            db.commit()
            return jsonify({'message': 'Product deleted successfully'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Database failed to delete product'}), 500
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
        products = cursor.fetchall()
        cursor.close()
        db.close()

        # Convert the users data to a list of dictionaries for JSON serialization
        products_list = []
        for product in products:
            product_dict = {
                'id': product[0],
                'product_name': product[1],
                'available_units': product[4],
                'selling_price': product[6]
                # Add other product attributes as needed
            }
            products_list.append(product_dict)

        return jsonify(products_list)  # Return JSON response with product details
    except Exception as e:
        # Return error message with status code 500
        return jsonify({'error': str(e)}), 500

@app.route('/update_product', methods=["POST"])
def update_product():
    try:
        data = request.get_json()
        product_ID = data.get('product_ID')
        product_name = data.get('product_name')
        unit_of_measure = data.get('unit_of_measure')
        quantity_per_unit = data.get('quantity_per_unit')
        available_units = data.get('available_units')
        mrp = data.get('mrp')
        selling_price = data.get('selling_price')
        manufacturer_name = data.get('manufacturer_name')
        product_description = data.get('product_description')
        category_ID = data.get('category_ID')

        db = get_database_connection()
        cursor = db.cursor()
        if db.in_transaction:
            db.commit()

        db.start_transaction()
        try:
            query = "UPDATE product SET product_name = %s, unit_of_measure = %s, quantity_per_unit = %s, available_units = %s, mrp = %s, selling_price = %s, manufacturer_name = %s, product_description = %s, category_id = %s WHERE product_id = %s;"
            cursor.execute(query, (product_name, unit_of_measure, quantity_per_unit, available_units, 
                            mrp, selling_price, manufacturer_name, product_description, category_ID, product_ID))
            db.commit()
            return jsonify({'message': 'Product updated successfully'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Database failed to update product'}), 500
        finally:
            cursor.close()
            db.close()
    except Exception as e:
        print(e)
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
# non-conflicting transaction
def orderDetails(address, user_id):
    db = get_database_connection()
    cursor = db.cursor()

    try:
        order_value = get_order_value(cursor, user_id)
        number_of_products = get_number_of_products(cursor, user_id)

        if db.in_transaction:
            db.commit()

        db.start_transaction()
        
        # Insert order details into the database
        query = '''INSERT INTO order_details (user_id, address_name, order_date, total_number_of_items, order_value, delivery_charge) VALUES (%s, %s, %s, %s, %s, %s);'''
        cursor.execute(query, (user_id, address, '2021-09-01', number_of_products, order_value, 0))
        db.commit()

        # obtain order_no of the order
        query = '''SELECT order_no FROM order_details WHERE user_id = %s AND order_date = %s;'''
        cursor.execute(query, (user_id, '2021-09-01'))
        order_no = cursor.fetchall()


        return order_no[0] if order_no else None

    except Exception as e:
        print("Error in orderDetails:", e)
        return None

    finally:
        cursor.close()
        db.close()

# non-conflicting transaction
def orderProducts(order_no, user_id):
    # first get the products in the cart
    cart_data = get_cart_data2(user_id)
    db = get_database_connection()
    cursor = db.cursor()

    if db.in_transaction:
        db.commit()

    db.start_transaction()

    for product_id in cart_data:
        query = '''INSERT INTO order_products (order_no, product_id, number_of_units, price_per_unit) VALUES (%s, %s, %s, %s);'''
        cursor.execute(query, (order_no, product_id, cart_data[product_id]['number_of_units'], cart_data[product_id]['selling_price']))
        db.commit()

    cursor.close()
    db.close()


@app.route('/send_address', methods = ["POST"])
def place_order():
    user_id = session.get("user_id")

    if user_id:
        try:
            data = request.get_json()
            address = data.get('address')
            order_no = orderDetails(address, user_id)

            if order_no is not None:
                orderProducts(order_no[0], user_id)
            
            # empty the cart for the user once the order has been created
            db = get_database_connection()
            cursor = db.cursor()

            if db.in_transaction:
                db.commit()

            db.start_transaction()
            # conflicting transaction
            query = "DELETE FROM add_to_cart where user_id = %s"
            cursor.execute(query, (user_id,))
            cursor.fetchall()
            db.commit()

            cursor.close()
            db.close()

            return jsonify({'message': 'Fetched address successfully'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Address not provided'}), 400
    else:
        return jsonify({'error': 'User not authenticated'}), 401    

@app.route('/signup', methods = ["GET"])
def signup():
    return render_template("signup.html")


# non-conflicting transaction
@app.route('/send_user_details', methods=["POST"])
def register_user():
    try:
        data = request.get_json()
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        middle_name = data.get('middleName')
        gender = data.get('gender')
        dob = data.get('dob')
        phone = data.get('phone')
        password = data.get('password')

        db = get_database_connection()
        cursor = db.cursor()

        try:
            if (db.in_transaction):
                db.commit()

            # Start transaction
            db.start_transaction()

            query = "INSERT INTO user (mobile_number, first_name, middle_name, last_name, password_hash, gender, date_of_birth) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (phone, first_name, middle_name, last_name, password, gender, dob))

            # Commit transaction
            db.commit()
            return jsonify({'message': 'User added successfully'}), 200
        except mysql.connector.Error as err:
            # Rollback transaction in case of errors
            db.rollback()
            return jsonify({'error': 'Database failed to add user'}), 500
        finally:
            cursor.close()
            db.close()
            # Ensure to end the transaction even in case of exceptions
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# non-conflicting transaction
@app.route('/api_address', methods=["POST"])
def api_address():
    user_id = session.get("user_id")

    if user_id:
        try:
            data = request.get_json()
            
            # Retrieve all the fields from the JSON data
            address_name = data.get('address_name')
            address_line_1 = data.get('address_line_1')
            address_line_2 = data.get('address_line_2')
            address_line_3 = data.get('address_line_3')
            city = data.get('city')
            state = data.get('state')
            pincode = data.get('pincode')
            
            db = get_database_connection()
            cursor = db.cursor()

            if db.in_transaction:
                db.commit()

            db.start_transaction()
            
            # Inserting the address into the database
            query = '''INSERT INTO shipping_address (user_id, address_name, address_line_1, address_line_2, address_line_3, city, state, pincode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);'''
            
            cursor.execute(query, (user_id, address_name, address_line_1, address_line_2, address_line_3, city, state, pincode))
            
            db.commit()

            cursor.close()
            db.close()

            return jsonify({'message': 'Address created successfully'}), 200
        except Exception as e:
            print(e)
            return jsonify({'error': 'Address not provided or database error'}), 400
    else:
        return jsonify({'error': 'User not authenticated'}), 401
    
if __name__ == "__main__":
    app.run(debug = True)
