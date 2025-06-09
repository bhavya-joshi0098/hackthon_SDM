from flask import Flask, flash, redirect, render_template, url_for
# import openai
# from google.generativeai import Model
import google.generativeai as genai
import re
import random
from functools import wraps
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin
cred = credentials.Certificate("finance-game-7c716-firebase-adminsdk-fbsvc-61b53e3b0e.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Flask app setup
app = Flask(__name__)
# Set a secure secret key for session
app.secret_key = os.urandom(24)  # Generate a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

genai.configure(api_key="AIzaSyBjqSYnsr2Le7-QgX_eoATrrQ-Y9mGNS2U")
model = genai.GenerativeModel("gemini-1.5-flash")
# Firebase Pyrebase config (for auth only)z



Config = {
  "apiKey": "AIzaSyBdkeUCyJwP1Ip4M05kyxksMGs3T0e_Z0c",
  "authDomain": "finance-game-7c716.firebaseapp.com",
  "databaseURL": "https://finance-game-7c716-default-rtdb.firebaseio.com",
  "projectId": "finance-game-7c716",
  "storageBucket": "finance-game-7c716.firebasestorage.app",
  "messagingSenderId": "100856364080",
  "appId": "1:100856364080:web:be1ca42f5a035be29c41f5",
  "databaseURL": "https://finance-game-7c716-default-rtdb.firebaseio.com/",

}

# Homepage
@app.route("/")
def index():
    return render_template("front_page.html")

# Login page
@app.route("/login")
def login():
    return render_template("/login/index.html")

# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not session.get("loginSuccess"):
#             return redirect(url_for("login"))
#         return f(*args, **kwargs)
#     return decorated_function

@app.route("/dashboard")
# @login_required
def dashboard():
    # Get level1 score from session (for backward compatibility)
    level1_score = session.get("level1_final_score", 0)
    return render_template("dashboard.html", level1_score=level1_score)


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
