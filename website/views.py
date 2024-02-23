from flask import Blueprint, render_template

views = Blueprint("views", __name__)


@views.route("/")
def home():
    return render_template("home.html")


@views.route("/search")
def search():
    return render_template("search.html")


@views.route("/upload")
def upload():
    return render_template("upload.html")


@views.route("/profile")
def profile():
    return render_template("profile.html")