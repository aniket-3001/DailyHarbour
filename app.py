from flask import Flask, request, redirect, url_for, session, render_template, jsonify
import mysql.connector
import logging

admin_phone = '4447778888'
admin_password = "hashedpassword5"

app = Flask(__name__)
app.secret_key = "123456"  # Set a secret key for session management

logging.basicConfig(level=logging.DEBUG)  # Configure logging

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
    cursor.execute(query, (name,))
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
        # idhar error add to cart mei same entry karne pe aajayega   
        # remember ki checkout karne pe poori cart khaali karni hogi    

@app.route('/', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]

        if phone == admin_phone and password == admin_password:
            session["user_id"] = "admin" # take note
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
    return render_template("login.html",  remaining_attempts = remaining_attempts)

@app.route('/products', methods=["GET"])
def products():
    return render_template("products.html")

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    #print("add_to_cart")

    try:
        data = request.get_json()
        products = data.get('products')
        #print(products)

        if not products:
            return jsonify({'error': 'No products provided'}), 400

        user_id = session.get("user_id")
        if user_id is None:
            return jsonify({'error': 'User not authenticated'}), 401
        
        #print("reach here")
        db = get_database_connection()
        cursor = db.cursor()
        #print("reach here2")
        
        for product in products:
            #print(product.get('name'))
            #print(product.get('quantity'))
            product_id = get_product_id(cursor, product.get('name'))  # Assuming you have a 'name' field in products
            # print(user_id, product_id, product.get('quantity'))
            add_to_cart_db(cursor, db, user_id, product_id, product.get('quantity'))
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

if __name__ == "__main__":
    app.run(debug=True)