import os
import random
import boto3
import pdfplumber
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from functools import wraps
from botocore.exceptions import ClientError

# ===============================
# 1. INITIALIZATION
# ===============================
load_dotenv()

app = Flask(__name__)
app.secret_key = "career_guide_ai_secure_key_2026"

# ===============================
# 2. AWS CONFIG (IAM BASED)
# ===============================
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")


dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
sns = boto3.client("sns", region_name=AWS_REGION)

users_table = dynamodb.Table("Users")
admin_users_table = dynamodb.Table("AdminUsers")
projects_table = dynamodb.Table("Projects")

# ===============================
# 3. AUTH DECORATOR (UNCHANGED)
# ===============================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ===============================
# 4. SNS HELPER
# ===============================
def send_notification(subject, message):
    if not SNS_TOPIC_ARN:
        return
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except ClientError as e:
        print("SNS Error:", e)

# ===============================
# 5. PUBLIC ROUTES (UNCHANGED)
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

# ===============================
# 6. CAREER ASSESSMENT (UNCHANGED)
# ===============================
@app.route('/career-assessment', methods=['GET', 'POST'])
def career_assessment():
    if request.method == 'POST':
        session['interest'] = request.form.get('interest')
        return redirect(url_for('quiz'))
    return render_template('career_assessment.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    interest = session.get('interest')
    if not interest:
        return redirect(url_for('career_assessment'))

    if request.method == 'POST':
        session['result'] = request.form.get('answer')
        return redirect(url_for('result'))

    return render_template('quiz.html', interest=interest)

@app.route('/result')
def result():
    return render_template(
        'result.html',
        interest=session.get('interest'),
        result=session.get('result')
    )

@app.route("/ai-suggestions")
def ai_suggestions():
    return render_template("ai_suggestions.html")

# ===============================
# 7. SKILL ROADMAP (UNCHANGED)
# ===============================
@app.route("/skill-roadmap", methods=["GET", "POST"])
def skill_roadmap():
    if request.method == "POST":
        return render_template("skill_roadmap.html", **request.form)
    return render_template("skill_roadmap.html")

@app.route("/cloud-platform")
def cloud_platform():
    return render_template("cloud_platform.html")

# ===============================
# 8. PROJECTS (DYNAMODB BACKEND)
# ===============================
@app.route("/projects")
def show_projects():
    items = projects_table.scan().get("Items", [])
    return render_template("projects_list.html", projects=items)

# ===============================
# 9. AI INTERVIEWS (UNCHANGED)
# ===============================
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
    q = random.choice(INTERVIEW_QUESTIONS["Software Developer"])
    return jsonify({"question": q})

@app.route("/api/interview/evaluate", methods=["POST"])
def evaluate_answer():
    answer = request.get_json().get("answer", "")
    if len(answer.strip()) < 20:
        return jsonify({"feedback": "Answer is too short. Try explaining with examples.", "score": 4})
    return jsonify({"feedback": "Good answer. Clear explanation.", "score": 8})

@app.route("/ai-interviews")
def ai_interviews():
    return render_template("ai_interviews.html")

# ===============================
# 10. RESUME ANALYSIS (UNCHANGED)
# ===============================
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
            skills = ["Python", "AWS", "Flask", "SQL", "Machine Learning"]
            found = [s for s in skills if s.lower() in text.lower()]
            result = {
                "ats": min(90, 40 + len(found) * 10),
                "skill_match": min(100, len(found) * 20),
                "experience": "Fresher / Entry Level",
                "skills": found
            }
    return render_template("resume.html", result=result)

# ===============================
# 11. USER AUTH (DYNAMODB)
# ===============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "username" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            # Check if user already exists
            response = users_table.get_item(
                Key={"username": username}
            )

            if "Item" in response:
                return "User already exists"

            # Create new user
            users_table.put_item(
                Item={
                    "username": username,
                    "password": password
                }
            )

            session["username"] = username
            return redirect(url_for("dashboard"))

        except ClientError as e:
            print("SIGNUP ERROR:", e)
            return "Server error during signup. Check DynamoDB."

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            response = users_table.get_item(
                Key={"username": username}
            )

            if "Item" in response:
                if response["Item"]["password"] == password:
                    session["username"] = username
                    return redirect(url_for("dashboard"))

            return "Invalid username or password"

        except ClientError as e:
            print("LOGIN ERROR:", e)
            return "Server error during login. Check DynamoDB."

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ===============================
# 12. DASHBOARD (UNCHANGED)
# ===============================
@app.route("/dashboard", methods=["GET", "POST"])
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
# 13. ADMIN (DYNAMODB)
# ===============================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        try:
            admin_id = request.form["admin_id"]
            password = request.form["password"]

            response = admin_users_table.get_item(
                Key={"admin_id": admin_id}
            )

            if "Item" in response and response["Item"]["password"] == password:
                session["admin_id"] = admin_id
                return redirect(url_for("admin_dashboard"))

            return "Invalid admin credentials"

        except Exception as e:
            print("ADMIN LOGIN ERROR:", e)
            return "Server error during admin login. Check DynamoDB."

    return render_template("admin_login.html")

@app.route("/admin-signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        try:
            admin_id = request.form["admin_id"]
            password = request.form["password"]

            response = admin_users_table.get_item(
                Key={"admin_id": admin_id}
            )

            if "Item" in response:
                return "Admin already exists"

            admin_users_table.put_item(Item={
                "admin_id": admin_id,
                "password": password
            })

            session["admin_id"] = admin_id
            return redirect(url_for("admin_dashboard"))

        except Exception as e:
            print("ADMIN SIGNUP ERROR:", e)
            return "Server error during admin signup."

    return render_template("admin_signup.html")

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
    return redirect(url_for("admin_login"))

# ===============================
# 14. AI CHATBOT (UNCHANGED)
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
    reply = chatbot_reply(request.get_json().get("message", ""))
    return jsonify({"reply": reply})

# ===============================
# 15. RUN (EC2 READY)
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
