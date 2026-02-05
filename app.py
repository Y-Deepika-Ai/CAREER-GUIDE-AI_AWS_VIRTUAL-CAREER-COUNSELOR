import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from functools import wraps
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import sqlite3
from flask import g

DATABASE = "career_guide_ai.db"

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()
def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            admin_id TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    db.commit()
with app.app_context():
    init_db()


# ===============================
# 1. INITIALIZATION
# ===============================
load_dotenv()

app = Flask(__name__)
app.secret_key = "career_guide_ai_secure_key_2026"


# ===============================
# 2. AUTH DECORATOR
# ===============================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ===============================
# 3. STORAGE (TEMP)
# ===============================
users = {}
admin_users = {"admin": "admin123"}
projects = []


# ===============================
# 4. PUBLIC ROUTES
# ===============================
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/career-assessment', methods=['GET', 'POST'])
def career_assessment():
    if request.method == 'POST':
        interest = request.form.get('interest')
        session['interest'] = interest   # store choice
        return redirect(url_for('quiz'))
    return render_template('career_assessment.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    interest = session.get('interest')

    if not interest:
        return redirect(url_for('career_assessment'))

    if request.method == 'POST':
        score = request.form.get('answer')
        session['result'] = score
        return redirect(url_for('result'))

    return render_template('quiz.html', interest=interest)


# STEP 3: Result page
@app.route('/result')
def result():
    interest = session.get('interest')
    result = session.get('result')
    return render_template('result.html', interest=interest, result=result)

@app.route("/ai-suggestions")
def ai_suggestions():
    return render_template("ai_suggestions.html")
def generate_roadmap(goal, level, hours):
    base = {
        "Frontend Developer": [
            "HTML & Semantic Markup",
            "CSS & Flexbox/Grid",
            "JavaScript Fundamentals",
            "Git & GitHub",
            "React Basics",
            "Projects & Portfolio"
        ],
        "Backend Developer": [
            "Python Basics",
            "Flask Framework",
            "REST APIs",
            "Databases (SQL)",
            "Authentication",
            "Deploy Backend"
        ],
        "Cloud Engineer": [
            "Linux Fundamentals",
            "Networking Basics",
            "AWS Core Services",
            "EC2 & S3",
            "IAM & Security",
            "Deploy Cloud Project"
        ]
    }

    roadmap = base.get(goal, [])

    if level == "Beginner":
        roadmap = roadmap[:4]
    elif level == "Intermediate":
        roadmap = roadmap[:5]

    return roadmap


@app.route("/skill-roadmap", methods=["GET", "POST"])
def skill_roadmap():
    if request.method == "POST":
        career_goal = request.form.get("career_goal")
        current_level = request.form.get("current_level")
        interests = request.form.get("interests")
        hours_per_week = request.form.get("hours_per_week")

        return render_template(
            "skill_roadmap.html",
            career_goal=career_goal,
            current_level=current_level,
            interests=interests,
            hours_per_week=hours_per_week
        )

    return render_template("skill_roadmap.html")

@app.route("/cloud-platform")
def cloud_platform():
    return render_template("cloud_platform.html")


@app.route("/projects")
def show_projects():
    project_list = [
        {"title": "Software Developer", "problem_statement": "Build applications"},
        {"title": "Data Scientist", "problem_statement": "Analyze data"},
        {"title": "UI/UX Designer", "problem_statement": "Design experiences"},
    ]
    return render_template("projects_list.html", projects=project_list)


# ===============================
# 5. AI INTERVIEWS (WORKING)
# ===============================
# Sample interview questions
from flask import jsonify, request
import random

INTERVIEW_QUESTIONS = {
    "Software Developer": [
        "What is OOP?",
        "Explain REST APIs.",
        "What is Flask?",
        "Difference between list and tuple?",
        "Explain load balancing."
    ]
}

@app.route("/api/interview/question", methods=["POST"])
def get_interview_question():
    role = "Software Developer"
    question = random.choice(INTERVIEW_QUESTIONS[role])
    return jsonify({"question": question})


@app.route("/api/interview/evaluate", methods=["POST"])
def evaluate_answer():
    data = request.get_json()
    answer = data.get("answer", "")

    if len(answer.strip()) < 20:
        return jsonify({
            "feedback": "Answer is too short. Try explaining with examples.",
            "score": 4
        })

    return jsonify({
        "feedback": "Good answer. Clear explanation.",
        "score": 8
    })
@app.route("/ai-interviews")
def ai_interviews():
    return render_template("ai_interviews.html")


# ===============================
# 6. RESUME ANALYSIS (WORKING)
# ===============================
from PyPDF2 import PdfReader

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

import pdfplumber

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

@app.route("/resume", methods=["GET", "POST"])
def resume_analysis():
    result = None

    if request.method == "POST":
        file = request.files.get("resume")

        if file:
            text = extract_text_from_pdf(file)

            # SIMPLE ANALYSIS LOGIC (for now)
            skills_list = ["Python", "AWS", "Flask", "SQL", "Machine Learning"]
            found_skills = [s for s in skills_list if s.lower() in text.lower()]

            result = {
                "ats": min(90, 40 + len(found_skills) * 10),
                "skill_match": min(100, len(found_skills) * 20),
                "experience": "Fresher / Entry Level",
                "skills": found_skills
            }

    return render_template("resume.html", result=result)


@app.route("/interview-feedback", methods=["POST"])
def interview_feedback():
    data = request.get_json()
    answer = data.get("answer", "")

    if len(answer) < 20:
        feedback = "Answer is too short. Try explaining with examples."
    else:
        feedback = "Good response! Improve by structuring your answer using STAR method."

    return jsonify({"feedback": feedback})

@app.route("/test")
def test():
    return "Route is working"

# ===============================
# 7. USER AUTH ROUTES
# ===============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "username" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            db.commit()
            session["username"] = username
            return redirect(url_for("dashboard"))

        except sqlite3.IntegrityError:
            return "Username already exists"

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        if user:
            session["username"] = username
            return redirect(url_for("dashboard"))

        return "Invalid username or password"

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))


# ===============================
# 6. USER DASHBOARD
# ===============================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    roadmap = None

    if request.method == "POST":
        career = request.form.get("career")
        roadmap = [
            "Fundamentals",
            "Core Skills",
            "Projects",
            "Advanced Topics",
            "Interview Prep"
        ]

    return render_template("dashboard.html", roadmap=roadmap)


# ===============================
# 7. ADMIN ROUTES
# ===============================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if admin_users.get(username) == password:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))

    return render_template("admin_login.html")


@app.route("/admin-dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    return render_template(
        "admin_dashboard.html",
        users_count=len(users),
        projects_count=len(projects),
    )


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# ===============================
# 8. AI CHATBOT LOGIC
# ===============================
def chatbot_reply(message):
    message = message.lower()

    if "ai" in message:
        return "🤖 AI is a great career! Start with Python and Machine Learning."

    if "cloud" in message:
        return "☁️ Cloud Engineering is hot! Learn AWS, EC2, S3, IAM."

    if "data" in message:
        return "📊 Data Science needs Python, SQL, and statistics."

    if "software" in message:
        return "💻 Software Development is evergreen! Focus on DSA + Projects."

    return "🤖 I am your Career Guide Bot. Ask me about AI, Cloud, Data, Software!"
@app.route("/ai-chat", methods=["POST"])
def ai_chat():
    print("🔥 AI CHAT HIT")

    data = request.get_json()
    print("📩 DATA:", data)

    user_message = data.get("message", "")
    reply = chatbot_reply(user_message)

    return jsonify({"reply": reply})


ROADMAPS = {
    "HR Specialist": {
        "foundation": [
            "Communication Skills",
            "Organizational Behavior",
            "MS Excel Basics"
        ],
        "tools": [
            "ATS (Zoho Recruit / BambooHR)",
            "Google Workspace",
            "Excel Advanced"
        ],
        "certifications": [
            "SHRM Essentials",
            "LinkedIn Learning HR Basics"
        ],
        "advanced": [
            "Talent Analytics",
            "Employee Engagement Strategy"
        ]
    }
}

# ===============================
# 9. RUN APP
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
