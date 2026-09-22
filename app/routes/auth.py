from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app
)
from streamlit import user

from app import email
from app.database.db import db
from app.models.user import User

from authlib.integrations.flask_client import OAuth


auth = Blueprint(
    "auth",
    __name__
)

# =========================================================
# HOME
# =========================================================

@auth.route("/")
def home():
    return redirect(url_for("auth.login"))

# =========================================================
# GOOGLE OAUTH SETUP
# =========================================================

oauth = OAuth()


def get_google_client():
    """
    Creates and returns the Google OAuth client.
    """

    if "google" not in oauth._clients:

        oauth.register(
            name="google",
            client_id=current_app.config.get("GOOGLE_CLIENT_ID"),
            client_secret=current_app.config.get("GOOGLE_CLIENT_SECRET"),

            server_metadata_url=(
                "https://accounts.google.com/.well-known/openid-configuration"
            ),

            client_kwargs={
                "scope": "openid email profile"
            }
        )

    return oauth.create_client("google")


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        remember = request.form.get(
            "remember"
        )

        # -------------------------
        # Validation
        # -------------------------

        if not email or not password:

            flash(
                "Please enter your email and password.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        # -------------------------
        # Find User
        # -------------------------

        user = User.query.filter_by(
            email=email
        ).first()

        # -------------------------
        # Check Credentials
        # -------------------------

        if user is None:
            print("LOGIN DEBUG: User NOT FOUND:", email)

            flash(
                "Incorrect email or password.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        if not user.check_password(password):
            print("LOGIN DEBUG: User found, but PASSWORD INCORRECT:", email)
            print("LOGIN DEBUG: User ID:", user.id)
            print("LOGIN DEBUG: Password hash exists:", bool(user.password_hash))

            flash(
                "Incorrect email or password.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        # -------------------------
        # Login Successful
        # -------------------------

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email

        # -------------------------
        # Remember Me
        # -------------------------

        if remember:
            session.permanent = True
        else:
            session.permanent = False

        flash(
            "Login successful!",
            "success"
        )

        return redirect(
            url_for("dashboard.home")
        )

    return render_template(
        "auth/login.html"
    )


# =========================================================
# GOOGLE LOGIN
# =========================================================

@auth.route("/google/login")
def google_login():

    google = get_google_client()

    if not google:
        flash(
            "Google login is not configured correctly.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    redirect_uri = url_for(
        "auth.google_callback",
        _external=True
    )

    return google.authorize_redirect(
        redirect_uri
    )


# =========================================================
# GOOGLE CALLBACK
# =========================================================

@auth.route("/google/callback")
def google_callback():

    google = get_google_client()

    try:

        # -------------------------
        # Get Google Access Token
        # -------------------------

        token = google.authorize_access_token()

        # -------------------------
        # Get Google User Information
        # -------------------------

        userinfo = token.get("userinfo")

        if not userinfo:

            userinfo = google.userinfo()

        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name")

        # -------------------------
        # Validate Google Response
        # -------------------------

        if not google_id or not email:

            flash(
                "Unable to retrieve your Google account information.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )

        # -------------------------
        # Find Existing Google User
        # -------------------------

        user = User.query.filter_by(
            google_id=google_id
        ).first()

        # -------------------------
        # If Google ID not found,
        # check email
        # -------------------------

        if user is None:

            user = User.query.filter_by(
                email=email
            ).first()

        # -------------------------
        # Existing User
        # -------------------------

        if user:

            # Connect Google account to
            # existing account if necessary

            if not user.google_id:

                user.google_id = google_id

            if not user.name and name:

                user.name = name

            db.session.commit()

        # -------------------------
        # New Google User
        # -------------------------

        else:

            user = User(
                name=name or "Google User",
                email=email,
                phone=None,
                google_id=google_id
            )

            db.session.add(user)
            db.session.commit()

        # -------------------------
        # Create Login Session
        # -------------------------

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email

        # Google login should persist
        # like Remember Me

        session.permanent = True

        flash(
            "Google login successful!",
            "success"
        )

        return redirect(
            url_for("dashboard.home")
        )

    except Exception as e:

        print(
            "Google Login Error:",
            e
        )

        flash(
            "Google login failed. Please try again.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # -------------------------
        # Required Fields
        # -------------------------

        if not name or not email or not phone or not password:

            flash(
                "Please fill in all required fields.",
                "error"
            )

            return render_template(
                "auth/register.html"
            )

        # -------------------------
        # Password Match
        # -------------------------

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "auth/register.html"
            )

        # -------------------------
        # Check Existing User
        # -------------------------

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists.",
                "error"
            )

            return render_template(
                "auth/register.html"
            )

        # -------------------------
        # Create User
        # -------------------------

        user = User(
            name=name,
            email=email,
            phone=phone
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(
            "Registration successful. Please log in.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/register.html"
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        if not email:

            flash(
                "Please enter your email address.",
                "error"
            )

            return render_template(
                "auth/forgot_password.html"
            )

        user = User.query.filter_by(
            email=email
        ).first()

        if user:

            session["reset_email"] = email

            flash(
                "Account found. Password reset can continue.",
                "success"
            )

            return redirect(
                url_for("auth.reset_password")
            )

        else:

            flash(
                "No account was found with that email address.",
                "error"
            )

            return render_template(
                "auth/forgot_password.html"
            )

    return render_template(
        "auth/forgot_password.html"
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    email = session.get(
        "reset_email"
    )

    if not email:

        flash(
            "Please start the password reset process again.",
            "error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:

        session.pop(
            "reset_email",
            None
        )

        flash(
            "User account could not be found.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not password:

            flash(
                "Please enter a new password.",
                "error"
            )

            return render_template(
                "auth/reset_password.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "auth/reset_password.html"
            )

        user.set_password(
            password
        )

        db.session.commit()

        session.pop(
            "reset_email",
            None
        )

        flash(
            "Password changed successfully. Please log in.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )