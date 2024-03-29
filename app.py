from flask import Flask, request, redirect, url_for, session, render_template
import mysql.connector
import time

app = Flask(_name_)
app.secret_key = "123456"  # Set a secret key for session management

# MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="angad123",
    database="dailyharbour"
)
cursor = db.cursor()

@app.route('/', methods=["POST", "GET"])
def login():
    
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]
        
        if "login_attempts" not in session:
            session["login_attempts"] = 0
        
        # Check user credentials from the database
        query = "SELECT * FROM user WHERE mobile_number=%s AND password_hash=%s"
        cursor.execute(query, (phone, password))
        user_data = cursor.fetchone()
        
        if user_data:
            # Successful login, reset login attempts
            session.pop("login_attempts", None)
            return redirect(url_for("user", usr=user_data[1]))  # Redirect to user profile
        else:
            # Failed login attempt
            session["login_attempts"] += 1
            remaining_attempts = 3 - session.get("login_attempts", 0)
            if remaining_attempts <= 0:
                session.pop("login_attempts", None)  # Reset login attempts
                return "Too many failed attempts. Please try again later."
    
    remaining_attempts = 3 - session.get("login_attempts", 0)
    return render_template("login.html",  remaining_attempts=remaining_attempts)

@app.route('/user/<usr>')
def user(usr):
    return f"Welcome, {usr}!"

if _name_ == "_main_":
    app.run(debug=True)
