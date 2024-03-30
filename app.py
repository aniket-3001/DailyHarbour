from flask import Flask, request, redirect, url_for, session, render_template
import mysql.connector
import time

app = Flask(__name__)
app.secret_key = "123456"  # Set a secret key for session management

# MySQL database connection
db = mysql.connector.connect (
    host = "127.0.0.1",
    user = "root",
    password = "Schrodanger@754",
    database = "DailyHarbour"
)

cursor = db.cursor()

@app.route('/homepage', methods=["POST", "GET"])
def homepage():
    return render_template("homepage.html")

@app.route('/', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]
        
        if "login_attempts" not in session:
            session["login_attempts"] = 0
        
        # Check user credentials from the database
        query = "SELECT * FROM user WHERE mobile_number= %s AND password_hash= %s"
        cursor.execute(query, (phone, password))
        user_data = cursor.fetchone()
        
        if user_data:
            # Successful login, reset login attempts
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

@app.route('/products', methods=["POST", "GET"])
def products():
    return render_template("products.html")

@app.route('/checkout', methods=["POST", "GET"])
def checkout():
    return render_template("checkout.html")

@app.route('/profile', methods=["POST", "GET"])
def profile():
    return render_template("profile.html")

@app.route('/orderPlaced', methods=["POST", "GET"])
def orderPlaced():
    return render_template("orderPlaced.html")

if __name__ == "__main__":
    app.run(debug = True)
