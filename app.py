from flask import Flask, redirect, url_for, render_template, request
import demo as dm

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug = True)