from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# ------------------ SECRET KEY ------------------
app.secret_key = "KOBAMS__080309"

# ------------------ DATABASE CONFIG ------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# ------------------ DATABASE MODELS ------------------

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    location = db.Column(db.String(100))
    price = db.Column(db.String(50))
    image = db.Column(db.String(200))


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    location = db.Column(db.String(100))
    price = db.Column(db.String(50))
    image = db.Column(db.String(200))


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whatsapp_number = db.Column(db.String(20))


# ------------------ HOME ROUTE ------------------

@app.route("/")
def home():
    search = request.args.get("search")

    if search:
        properties = Property.query.filter(Property.location.contains(search)).all()
        vehicles = Vehicle.query.filter(Vehicle.location.contains(search)).all()
    else:
        properties = Property.query.all()
        vehicles = Vehicle.query.all()

    settings = Settings.query.first()

    return render_template(
        "index.html",
        properties=properties,
        vehicles=vehicles,
        settings=settings
    )


# ------------------ LOGIN ROUTE ------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "KOBAMS" and password == "080309":
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


# ------------------ LOGOUT ROUTE ------------------

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


# ------------------ ADMIN ROUTE ------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    settings = Settings.query.first()

    if request.method == "POST":

        # 🔹 Update WhatsApp number
        if "whatsapp_number" in request.form:
            settings.whatsapp_number = request.form["whatsapp_number"]
            db.session.commit()
            return redirect(url_for("admin"))

        # 🔹 Handle Property / Vehicle Upload
        title = request.form["title"]
        location = request.form["location"]
        price = request.form["price"]
        item_type = request.form["type"]
        image = request.files["image"]

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(image_path)

            if item_type == "property":
                new_item = Property(
                    title=title,
                    location=location,
                    price=price,
                    image="uploads/" + filename
                )
            else:
                new_item = Vehicle(
                    title=title,
                    location=location,
                    price=price,
                    image="uploads/" + filename
                )

            db.session.add(new_item)
            db.session.commit()

        return redirect(url_for("admin"))

    properties = Property.query.all()
    vehicles = Vehicle.query.all()

    return render_template(
        "admin.html",
        properties=properties,
        vehicles=vehicles,
        settings=settings
    )


# ------------------ DELETE ROUTE ------------------

@app.route("/delete/<string:item_type>/<int:item_id>")
def delete(item_type, item_id):

    if "logged_in" not in session:
        return redirect(url_for("login"))

    if item_type == "property":
        item = Property.query.get_or_404(item_id)
    else:
        item = Vehicle.query.get_or_404(item_id)

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for("admin"))


# ------------------ EDIT ROUTE ------------------

@app.route("/edit/<string:item_type>/<int:item_id>", methods=["GET", "POST"])
def edit(item_type, item_id):

    if "logged_in" not in session:
        return redirect(url_for("login"))

    if item_type == "property":
        item = Property.query.get_or_404(item_id)
    else:
        item = Vehicle.query.get_or_404(item_id)

    if request.method == "POST":
        item.title = request.form["title"]
        item.location = request.form["location"]
        item.price = request.form["price"]

        db.session.commit()
        return redirect(url_for("admin"))

    return render_template("edit.html", item=item, item_type=item_type)


# ------------------ RUN APP ------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Ensure WhatsApp settings row exists
        if Settings.query.first() is None:
            default_settings = Settings(whatsapp_number="2347085257837")
            db.session.add(default_settings)
            db.session.commit()
            
        app.run(host="0.0.0.0", port=5000)