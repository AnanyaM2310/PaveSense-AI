from flask import Blueprint, render_template

home = Blueprint(
    "home",
    __name__
)

from flask import redirect, url_for

@home.route("/")
def index():
    return redirect(url_for("auth.login"))