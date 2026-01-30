import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv

# --- 1. INITIALIZATION ---
load_dotenv()
app = Flask(__name__)
app.secret_key = "career_guide_ai_secure_key_2026" 

# --- 2. AI CONFIG ---
# -------------------- CHATBOT LOGIC --------------------
def chatbot_reply(message):
    message = message.lower()

    if "career" in message:
        return "Tell me your interests and strengths. I can help you choose a career 😊"

    if "software" in message:
        return "Software Development is a great field! Want a learning roadmap?"

    if "data" in message:
        return "Data Science combines coding and analytics. Want guidance?"

    if "ui" in message or "design" in message:
        return "UI/UX focuses on user experience and visuals 🎨"

    if "cloud" in message:
        return "Cloud careers include AWS, Azure & DevOps ☁️"

    if "help" in message or "confused" in message:
        return "No worries 🙂 Tell me what you like doing."

    return "I’m your Career Guide Bot 🤖 Ask me about careers, skills, or roadmaps."

# --- 3. STORAGE ---
users = {}
admin_users = {"admin": "admin123"}
projects = []

# --- 4. PUBLIC PAGE ROUTES ---
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

@app.route("/cloud-platform") # FIXES BuildError 'cloud_platform'
def cloud_platform():
    return render_template("cloud_platform.html")

@app.route("/projects")
def show_projects():
    projects = [
        {
            "title": "Software Developer",
            "problem_statement": "Build applications, websites, and systems"
        },
        {
            "title": "Data Scientist",
            "problem_statement": "Analyze data and build predictive models"
        },
        {
            "title": "UI/UX Designer",
            "problem_statement": "Design user-friendly digital experiences"
        }
    ]
    return render_template("projects_list.html", projects=projects)

# --- 5. USER AUTH ROUTES ---
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u, p = request.form.get("username"), request.form.get("password")
        users[u] = p
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form.get("username"), request.form.get("password")
        if users.get(u) == p:
            session["user"] = u
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["user"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# --- 6. ADMIN ROUTES ---
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        u, p = request.form.get("username"), request.form.get("password")
        if admin_users.get(u) == p:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")

@app.route("/admin-dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html", users_count=len(users), projects_count=len(projects))

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# --- 7. AI CHAT LOGIC ---
def chatbot_reply(message):
    message = message.lower()

    if "software" in message:
        return "Software Development is a great career! Start with Python, Java, or Web Dev."

    if "data" in message:
        return "Data Science needs Python, SQL, statistics, and ML."

    if "ui" in message or "design" in message:
        return "UI/UX Designers focus on user experience and visual design."
    
    # 1. NEW: Artificial Intelligence & ML
    if "ai" in message or "machine learning" in message or "intelligence" in message:
        return ("AI is the fastest-growing field in 2026! 🤖 You should learn Python, "
                "Neural Networks, and LLM integration (like OpenAI or Gemini APIs).")

    # 2. NEW: Cybersecurity
    if "cyber" in message or "security" in message or "hack" in message:
        return ("Cybersecurity is critical! 🔐 Focus on Networking, Ethical Hacking, "
                "and certifications like CompTIA Security+ or CEH.")

    # 3. NEW: DevOps & Automation
    if "devops" in message or "automation" in message or "pipeline" in message:
        return ("DevOps bridges the gap between coding and operations 🚀. "
                "Learn Docker, Kubernetes, and CI/CD tools like GitHub Actions.")

    if "medical" in message or "healthcare" in message or "doctor" in message:
        return ("Healthcare is booming! 🏥 Beyond being a doctor, you can explore "
                "Telemedicine, Biomedical Research, or Health Data Analytics.")

    if "biotech" in message or "biology" in message:
        return ("Biotechnology is the future of medicine! 🧬 You could work in "
                "Genetics, Vaccine Development, or Agricultural Tech.")

    # --- BUSINESS & FINANCE ---
    if "business" in message or "management" in message:
        return ("Management roles are vital 💼. Consider being a Project Manager, "
                "Business Analyst, or specializing in Supply Chain Operations.")

    if "finance" in message or "money" in message or "bank" in message:
        return ("Finance is evolving! 💰 Look into Fintech, Investment Banking, "
                "or Risk Compliance. Understanding Excel and SQL helps here too.")

    # --- CREATIVE & HUMANITIES ---
    if "psychology" in message or "mental" in message:
        return ("Mental health is a priority in 2026 🧠. You can become a Clinical "
                "Psychologist, Industrial Counselor, or a Marketing Psychologist.")

    if "marketing" in message or "ads" in message:
        return ("Digital Marketing is huge! 📱 Focus on Content Strategy, SEO, "
                "and Social Media Growth. It's great for creative thinkers.")

    # --- SUSTAINABILITY (Green Careers) ---
    if "green" in message or "environment" in message or "energy" in message:
        return ("Sustainability is a massive 2026 trend! 🌱 Check out Renewable Energy "
                "(Solar/EV), Sustainability Consulting, or Environmental Law.")

    # --- EXISTING TECH TRIGGERS (Keep these for balance) ---
    if "software" in message or "data" in message or "ai" in message:
        return "I can help with Tech paths too! Ask about AI, Cyber, or Cloud 💻."
    
    # 8. Help / Confused
    if "help" in message or "confused" in message or "start" in message:
        return "Don't worry! Tell me: Do you like Coding, Designing, or Solving Security puzzles? 🤔"

    if "career" in message:
        return "Tell me your interests and strengths, I’ll guide you 🙂"

    return "I’m your Career Guide Bot 🤖 Ask me about careers, skills, or projects."

@app.route("/ai-chat", methods=["GET", "POST"])
def ai_chat():
    if request.method == "POST":
        msg = request.get_json().get("message")
        reply = chatbot_reply(msg)
        return jsonify({"reply": reply})

    return render_template("ai_chat.html")



if __name__ == "__main__":
    app.run(debug=True)