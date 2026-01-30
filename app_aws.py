from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import uuid
import boto3
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError

# -------------------- APP SETUP --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key")

# -------------------- AWS CONFIG --------------------
REGION = os.environ.get("AWS_REGION", "us-east-1")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

# DynamoDB Tables
users_table = dynamodb.Table("Users")
admin_users_table = dynamodb.Table("AdminUsers")
projects_table = dynamodb.Table("Projects")
enrollments_table = dynamodb.Table("Enrollments")

# -------------------- FILE UPLOAD CONFIG --------------------
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------- SNS HELPER --------------------
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

# -------------------- ROUTES --------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

# -------------------- USER AUTH --------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            if "Item" in users_table.get_item(Key={"username": username}):
                flash("User already exists")
                return redirect(url_for("signup"))

            users_table.put_item(Item={
                "username": username,
                "password": password
            })

            send_notification("New User Signup", f"{username} registered")
            flash("Signup successful")
            return redirect(url_for("login"))
        except ClientError as e:
            flash("Signup error")
            print(e)

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            res = users_table.get_item(Key={"username": username})
            if "Item" in res and res["Item"]["password"] == password:
                session["username"] = username
                send_notification("User Login", f"{username} logged in")
                return redirect(url_for("home"))
        except ClientError as e:
            print(e)

        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# -------------------- USER DASHBOARD --------------------
@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    enrollments = enrollments_table.get_item(Key={"username": username}).get("Item", {})
    project_ids = enrollments.get("project_ids", [])

    my_projects = []
    for pid in project_ids:
        res = projects_table.get_item(Key={"id": pid})
        if "Item" in res:
            my_projects.append(res["Item"])

    return render_template("home.html", username=username, my_projects=my_projects)

@app.route("/projects")
def projects():
    if "username" not in session:
        return redirect(url_for("login"))

    projects = projects_table.scan().get("Items", [])
    enrollments = enrollments_table.get_item(
        Key={"username": session["username"]}
    ).get("Item", {}).get("project_ids", [])

    return render_template(
        "projects_list.html",
        projects=projects,
        user_enrollments=enrollments
    )

@app.route("/enroll/<project_id>")
def enroll(project_id):
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    record = enrollments_table.get_item(Key={"username": username}).get("Item", {})
    project_ids = record.get("project_ids", [])

    if project_id not in project_ids:
        project_ids.append(project_id)
        enrollments_table.put_item(Item={
            "username": username,
            "project_ids": project_ids
        })
        send_notification("Project Enrollment", f"{username} enrolled")

    return redirect(url_for("home"))

# -------------------- ADMIN AUTH --------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        res = admin_users_table.get_item(Key={"username": username})
        if "Item" in res and res["Item"]["password"] == password:
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

# -------------------- ADMIN DASHBOARD --------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    users = users_table.scan().get("Items", [])
    projects = projects_table.scan().get("Items", [])
    enrollments = enrollments_table.scan().get("Items", [])

    enrollments_map = {e["username"]: e.get("project_ids", []) for e in enrollments}

    return render_template(
        "admin_dashboard.html",
        users=users,
        projects=projects,
        enrollments=enrollments_map
    )

@app.route("/admin/create-project", methods=["GET", "POST"])
def admin_create_project():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        title = request.form["title"]
        problem = request.form["problem_statement"]
        solution = request.form["solution_overview"]

        image = request.files.get("image")
        document = request.files.get("document")

        image_name = None
        doc_name = None

        if image and allowed_file(image.filename):
            image_name = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))

        if document and allowed_file(document.filename):
            doc_name = secure_filename(document.filename)
            document.save(os.path.join(app.config["UPLOAD_FOLDER"], doc_name))

        project = {
            "id": str(uuid.uuid4()),
            "title": title,
            "problem_statement": problem,
            "solution_overview": solution,
            "image": image_name,
            "document": doc_name
        }

        projects_table.put_item(Item=project)
        send_notification("New Project", title)

        return redirect(url_for("admin_dashboard"))

    return render_template("admin_create_project.html")

# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
