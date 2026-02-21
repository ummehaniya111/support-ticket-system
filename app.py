from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from flask_login import LoginManager
from models import User
from models import Ticket
# import os
from werkzeug.utils import secure_filename
from flask import send_from_directory





app = Flask(__name__)
import os

basedir = os.path.abspath(os.path.dirname(__file__))
# Render provides persistent disk at /var/data
if os.environ.get("RENDER"):
    db_path = "/var/data/site.db"
else:
    db_path = os.path.join(basedir, "site.db")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'secret123'

db.init_app(app)

with app.app_context():
    db.create_all()


# app.config['SECRET_KEY'] = 'secret123'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/site.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# create uploads folder
upload_path = os.path.join(basedir, "uploads")
os.makedirs(upload_path, exist_ok=True)
app.config["UPLOAD_FOLDER"] = upload_path
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


from models import *

@app.route("/")
def home():
    return redirect(url_for("login"))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registration route
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")

# Login route
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid login")

    return render_template("login.html")


#logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# Dashboard route
@app.route("/dashboard")
@login_required
def dashboard():
    tickets = Ticket.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", tickets=tickets)


# Create ticket route
@app.route("/create_ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        file = request.files["file"]
        filename = None

        if file and file.filename != "":
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


# Admin panel route
@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        return "Access denied"

    tickets = Ticket.query.all()
    return render_template("admin.html", tickets=tickets)

# Update ticket status route
@app.route("/update_status/<int:id>", methods=["POST"])
@login_required
def update_status(id):
    print(request.form) 
    if current_user.role != "admin":
        return "Access denied"

    ticket = Ticket.query.get(id)
    ticket.status = request.form["status"]
    db.session.commit()

    return redirect(url_for("admin_panel"))

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# if __name__ == "__main__":
#     app.run()

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


application = app


