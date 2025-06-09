from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
# import openai
import json
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

def build_level1_prompt():
    return (
        "You are an educational game assistant for teenagers learning about finance. "
        "Teach a concept about money in a fun, simple way, then ask a multiple-choice question (MCQ) with 4 options about what you just taught. "
        "Today's topic is: 'What is money and why do we use it?'. "
        "Format your response as:\n"
        "Paragraph: <your paragraph>\n"
        "Question: <your question>\n"
        "Options:\nA) <option1>\nB) <option2>\nC) <option3>\nD) <option4>"
    )

def generate_questions():
    questions = []
    for _ in range(5):
        prompt = build_level1_prompt()
        response = model.generate_content(prompt)
        content = response.text

        paragraph_match = re.search(r'Paragraph:\s*(.*?)\s*Question:', content, re.DOTALL)
        question_match = re.search(r'Question:\s*(.*?)\s*Options:', content, re.DOTALL)
        options_match = re.findall(r'[A-D]\)\s*(.*)', content)

        if paragraph_match and question_match and len(options_match) == 4:
            questions.append({
                'paragraph': paragraph_match.group(1).strip(),
                'question': question_match.group(1).strip(),
                'options': options_match,
                'correct_option': random.choice(['A', 'B', 'C', 'D'])
            })
    return questions

@app.route("/level1", methods=["GET", "POST"])
def level1():
    total_questions = 5
    marks_per_question = 5

    # Initialize session variables if not set
    if "level1_questions" not in session or request.method == "GET":
        print("Generating new questions...")  # Debug print
        questions = generate_questions()
        session["level1_questions"] = questions
        session["level1_current_question"] = 0
        session["level1_score"] = 0
        session.modified = True  # Ensure session is saved
        print(f"Session after initialization: {session}")  # Debug print

    current_question = session["level1_current_question"]
    score = session["level1_score"]
    questions = session["level1_questions"]
    feedback = None

    print(f"Current session state: {session}")  # Debug print

    # On POST, check the answer
    if request.method == "POST":
        user_answer = request.form.get("answer", "")
        if not questions or current_question >= len(questions):
            # If questions are missing, regenerate them
            questions = generate_questions()
            session["level1_questions"] = questions
            session["level1_current_question"] = 0
            session["level1_score"] = 0
            session.modified = True
            return redirect(url_for("level1"))

        current_q = questions[current_question]
        options = current_q['options']
        correct = current_q['correct_option']
        
        # Find which option letter was chosen
        answer_letter = ""
        for idx, opt in enumerate(options):
            if opt == user_answer:
                answer_letter = chr(ord('A') + idx)
                break

        if answer_letter == correct:
            feedback = "✅ Correct! Great job!"
            score += marks_per_question
        else:
            feedback = f"❌ Incorrect. The correct answer was option {correct}."
        
        session["level1_score"] = score
        current_question += 1
        session["level1_current_question"] = current_question
        session.modified = True  # Ensure session is saved

    # If finished all questions, show final score and redirect
    if current_question >= total_questions:
        final_score = session["level1_score"]
        # Store the score in session for dashboard
        session["level1_final_score"] = final_score

        # Update score in Firebase
        player_id = session.get("playerId")
        if player_id:
            try:
                # Get the user document
                user_ref = db.collection("users").document(player_id)
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    # Get current high score
                    current_high_score = user_doc.to_dict().get("hightScore", {}).get("level1", 0)
                    
                    # Update only if new score is higher
                    if final_score > current_high_score:
                        user_ref.update({
                            "hightScore.level1": final_score
                        })
                        print(f"Updated level 1 score in Firebase for user {player_id}: {final_score}")
                    else:
                        print(f"Current score {final_score} not higher than high score {current_high_score}")
                else:
                    print(f"User document not found for player_id: {player_id}")
            except Exception as e:
                print(f"Error updating Firebase score: {str(e)}")
        else:
            print("No player_id found in session")

        # Clear level1 session data
        session.pop("level1_questions", None)
        session.pop("level1_current_question", None)
        session.pop("level1_score", None)
        session.modified = True
        flash(f"Level 1 Complete! Your score: {final_score} out of {total_questions * marks_per_question}")
        return redirect(url_for("dashboard"))

    # Get current question data
    if not questions or current_question >= len(questions):
        # If questions are missing or invalid, regenerate them
        questions = generate_questions()
        session["level1_questions"] = questions
        session["level1_current_question"] = 0
        session["level1_score"] = 0
        session.modified = True
        return redirect(url_for("level1"))

    current_q = questions[current_question]
    return render_template(
        "level1.html",
        paragraph=f"Question {current_question + 1} of {total_questions}:<br><br>{current_q['paragraph']}",
        question=current_q['question'],
        options=current_q['options'],
        feedback=feedback,
        total_questions=total_questions,
        current_score=score  # Pass current score to template
    )

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
