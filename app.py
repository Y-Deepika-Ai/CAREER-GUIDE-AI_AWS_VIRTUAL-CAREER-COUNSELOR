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


@app.route("/career-assessment")
def career_assessment():
    return render_template("career_assessment.html")


@app.route("/ai-suggestions")
def ai_suggestions():
    return render_template("ai_suggestions.html")


@app.route("/skill-roadmap")
def skill_roadmap():
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
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session["username"])


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


# ===============================
# 9. RUN APP
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
