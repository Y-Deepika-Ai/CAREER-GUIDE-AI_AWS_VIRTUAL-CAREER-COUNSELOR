import os
import uuid
import random
import boto3
import pdfplumber
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
from functools import wraps

# ===============================
# 1. APP SETUP
# ===============================
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "career_guide_ai_secure_key_2026")

# ===============================
# 2. AWS CONFIG
# ===============================
REGION = os.environ.get("AWS_REGION", "us-east-1")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

users_table = dynamodb.Table("Users")
admin_users_table = dynamodb.Table("AdminUsers")
projects_table = dynamodb.Table("Projects")
enrollments_table = dynamodb.Table("Enrollments")

# ===============================
# 3. FILE UPLOAD CONFIG
# ===============================
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ===============================
# 4. HELPERS
# ===============================
def send_notification(subject, message):
    if not SNS_TOPIC_ARN:
        return
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
    except ClientError as e:
        print("SNS Error:", e)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# ===============================
# 5. PUBLIC ROUTES
# ===============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ===============================
# 6. AUTH ROUTES
# ===============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if "Item" in users_table.get_item(Key={"username": username}):
            flash("User already exists")
            return redirect(url_for("signup"))

        users_table.put_item(Item={"username": username, "password": password})
        send_notification("New Signup", username)

        session["username"] = username
        return redirect(url_for("dashboard"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        res = users_table.get_item(Key={"username": username})
        if "Item" in res and res["Item"]["password"] == password:
            session["username"] = username
            send_notification("Login", username)
            return redirect(url_for("dashboard"))

        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ===============================
# 7. DASHBOARD
# ===============================
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    roadmap = None
    if request.method == "POST":
        roadmap = [
            "Fundamentals",
            "Core Skills",
            "Projects",
            "Advanced Topics",
            "Interview Prep"
        ]
    return render_template("dashboard.html", roadmap=roadmap)

# ===============================
# 8. CAREER ASSESSMENT FLOW
# ===============================
@app.route("/career-assessment", methods=["GET", "POST"])
def career_assessment():
    if request.method == "POST":
        session["interest"] = request.form.get("interest")
        return redirect(url_for("quiz"))
    return render_template("career_assessment.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "interest" not in session:
        return redirect(url_for("career_assessment"))

    if request.method == "POST":
        session["result"] = request.form.get("answer")
        return redirect(url_for("result"))

    return render_template("quiz.html", interest=session["interest"])

@app.route("/result")
def result():
    return render_template(
        "result.html",
        interest=session.get("interest"),
        result=session.get("result")
    )

# ===============================
# 9. SKILL ROADMAP
# ===============================
@app.route("/skill-roadmap", methods=["GET", "POST"])
def skill_roadmap():
    if request.method == "POST":
        return render_template("skill_roadmap.html", **request.form)
    return render_template("skill_roadmap.html")

# ===============================
# 10. PROJECTS
# ===============================
@app.route("/projects")
@login_required
def projects():
    items = projects_table.scan().get("Items", [])
    enrolled = enrollments_table.get_item(
        Key={"username": session["username"]}
    ).get("Item", {}).get("project_ids", [])
    return render_template("projects_list.html", projects=items, user_enrollments=enrolled)

@app.route("/enroll/<project_id>")
@login_required
def enroll(project_id):
    username = session["username"]
    record = enrollments_table.get_item(Key={"username": username}).get("Item", {})
    ids = record.get("project_ids", [])

    if project_id not in ids:
        ids.append(project_id)
        enrollments_table.put_item(Item={"username": username, "project_ids": ids})
        send_notification("Enrollment", username)

    return redirect(url_for("projects"))

# ===============================
# 11. AI INTERVIEW
# ===============================
INTERVIEW_QUESTIONS = {
    "Software Developer": [
        "What is OOP?",
        "Explain REST APIs",
        "What is Flask?",
        "Difference between list and tuple?",
        "Explain load balancing"
    ]
}

@app.route("/ai-interviews")
def ai_interviews():
    return render_template("ai_interviews.html")

@app.route("/api/interview/question", methods=["POST"])
def interview_question():
    q = random.choice(INTERVIEW_QUESTIONS["Software Developer"])
    return jsonify({"question": q})

@app.route("/api/interview/evaluate", methods=["POST"])
def interview_evaluate():
    answer = request.json.get("answer", "")
    if len(answer) < 20:
        return jsonify({"feedback": "Answer too short", "score": 4})
    return jsonify({"feedback": "Good answer", "score": 8})

# ===============================
# 12. RESUME ANALYSIS
# ===============================
def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for p in pdf.pages:
            text += p.extract_text() or ""
    return text

@app.route("/resume", methods=["GET", "POST"])
def resume():
    result = None
    if request.method == "POST":
        file = request.files.get("resume")
        if file:
            text = extract_text(file)
            skills = ["Python", "AWS", "Flask", "SQL"]
            found = [s for s in skills if s.lower() in text.lower()]
            result = {
                "ats": min(90, 40 + len(found) * 10),
                "skills": found
            }
    return render_template("resume.html", result=result)

# ===============================
# 13. AI CHATBOT
# ===============================
@app.route("/ai-chat", methods=["POST"])
def ai_chat():
    msg = request.json.get("message", "").lower()

    if "ai" in msg:
        reply = "AI is a great career. Start with Python."
    elif "cloud" in msg:
        reply = "Cloud Engineering needs AWS, EC2, S3."
    else:
        reply = "Ask me about AI, Cloud, Data, or Software!"

    return jsonify({"reply": reply})

# ===============================
# 14. ADMIN
# ===============================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        res = admin_users_table.get_item(Key={"username": u})
        if "Item" in res and res["Item"]["password"] == p:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin")
    return render_template("admin_login.html")

@app.route("/admin-dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template(
        "admin_dashboard.html",
        users_count=users_table.scan()["Count"],
        projects_count=projects_table.scan()["Count"]
    )

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

# ===============================
# 15. RUN
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
