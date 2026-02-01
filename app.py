import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from functools import wraps

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
# 5. USER AUTH ROUTES
# ===============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if 'username' in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username not in users:
            users[username] = password
            session["username"] = username
            return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if 'username' in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("dashboard"))

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

    if "ai" in message or "machine learning" in message:
        return "AI is booming 🤖 Learn Python, ML & LLMs."

    if "cyber" in message:
        return "Cybersecurity is huge 🔐 Learn networking & ethical hacking."

    if "devops" in message:
        return "DevOps needs Docker, Kubernetes & CI/CD."

    if "software" in message:
        return "Software Dev is great! Start with Python or Web Dev."

    if "data" in message:
        return "Data Science needs Python, SQL & statistics."

    if "ui" in message or "design" in message:
        return "UI/UX focuses on design & user experience 🎨."

    if "career" in message:
        return "Tell me your interests, I’ll guide you 🙂"

    return "I’m your Career Guide Bot 🤖 Ask me about careers or skills."


@app.route("/ai-chat", methods=["GET", "POST"])
def ai_chat():
    if request.method == "POST":
        data = request.get_json()
        reply = chatbot_reply(data.get("message", ""))
        return jsonify({"reply": reply})

    return render_template("ai_chat.html")


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
