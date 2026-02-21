
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from extensions import db
from models import User, Ticket
import os


# ======================================================
# APP + PATH CONFIG
# ======================================================

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

# Render writable folders
instance_path = os.path.join(basedir, "instance")
os.makedirs(instance_path, exist_ok=True)

upload_path = os.path.join(basedir, "uploads")
os.makedirs(upload_path, exist_ok=True)

db_path = os.path.join(instance_path, "site.db")


# ======================================================
# CONFIGURATION
# ======================================================

app.config["SECRET_KEY"] = "secret123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = upload_path


# ======================================================
# EXTENSIONS INIT
# ======================================================

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ======================================================
# CREATE DATABASE TABLES (IMPORTANT FOR RENDER)
# ======================================================

with app.app_context():
    db.create_all()


# ======================================================
# LOGIN MANAGER
# ======================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ======================================================
# ROUTES
# ======================================================

@app.route("/")
def home():
    return redirect(url_for("login"))


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        # prevent duplicate users
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email already registered")
            return redirect(url_for("register"))

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password")

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    tickets = Ticket.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", tickets=tickets)


# ---------------- CREATE TICKET ----------------
@app.route("/create_ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        file = request.files.get("file")
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        ticket = Ticket(
            title=title,
            description=description,
            attachment=filename,
            author=current_user
        )

        db.session.add(ticket)
        db.session.commit()

        flash("Ticket created successfully!")
        return redirect(url_for("dashboard"))

    return render_template("create_ticket.html")


# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        return "Access denied"

    tickets = Ticket.query.all()
    return render_template("admin.html", tickets=tickets)


# ---------------- UPDATE STATUS ----------------
@app.route("/update_status/<int:id>", methods=["POST"])
@login_required
def update_status(id):
    if current_user.role != "admin":
        return "Access denied"

    ticket = Ticket.query.get(id)
    ticket.status = request.form["status"]
    db.session.commit()

    return redirect(url_for("admin_panel"))


# ---------------- SERVE FILES ----------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ======================================================
# RUN APP (Render Compatible)
# ======================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# For Gunicorn
application = app
