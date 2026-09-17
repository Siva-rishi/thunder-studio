import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import (
    login_user, logout_user, login_required, current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager
from models import User, Service, GalleryItem, Booking

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # If DATABASE_URL is set (e.g. on the App EC2 server, pointing at RDS),
    # use that. Otherwise fall back to a local SQLite file for quick testing.
    # Example DATABASE_URL for RDS MySQL:
    #   mysql+pymysql://<db_user>:<db_password>@<rds_endpoint>:3306/thunderstudio
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        database_url = "sqlite:///" + os.path.join(BASE_DIR, "instance", "thunder.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        _seed_if_empty()

    register_routes(app)
    return app


# ---------------------------------------------------------------- auth setup
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------- seed data
def _seed_if_empty():
    if Service.query.count() == 0:
        db.session.add_all([
            Service(
                icon="\u26a1", title="Wedding Photography",
                description="Full-day coverage from getting ready to the last dance. "
                             "We capture every tear, laugh, and stolen glance.",
                features="8\u201312 hours of coverage\n2 professional photographers\n"
                         "500+ edited high-res images\nPrivate online gallery",
                price_label="Starting at \u20b945,000", sort_order=1,
            ),
            Service(
                icon="\u2726", title="Wedding Film",
                description="A cinematic short film of your day \u2014 scored to music you "
                             "love, edited to make you feel it all over again.",
                features="Full-day videography\n3\u20135 min highlight reel\n"
                         "Full ceremony & speeches edit\n4K delivery + drone footage",
                price_label="Starting at \u20b965,000", featured=True,
                badge="Most Popular", sort_order=2,
            ),
            Service(
                icon="\u25c8", title="Pre-Wedding Shoot",
                description="An intimate session before the big day \u2014 perfect for "
                             "save-the-dates, getting comfortable on camera, or just "
                             "celebrating your love.",
                features="3\u20134 hours session\nLocation of your choice\n"
                         "100+ edited images\nSame-day sneak peek",
                price_label="Starting at \u20b918,000", sort_order=3,
            ),
            Service(
                icon="\u2758", title="Albums & Prints",
                description="Heirloom-quality lay-flat albums and fine art prints. "
                             "Something tangible to hold and pass down for generations.",
                features="Custom designed layouts\nPremium lay-flat binding\n"
                         "10\u00d710 to 14\u00d714 sizes\nArchival-grade paper",
                price_label="Starting at \u20b912,000", sort_order=4,
            ),
        ])

    if GalleryItem.query.count() == 0:
        db.session.add_all([
            GalleryItem(category="wedding", label="Wedding \u00b7 Ceremony", color="#1a2535", height=320, sort_order=1),
            GalleryItem(category="prewedding", label="Pre-Wedding \u00b7 Outdoor", color="#1e2d1e", height=220, sort_order=2),
            GalleryItem(category="portrait", label="Portrait \u00b7 Studio", color="#2a1e35", height=400, sort_order=3),
            GalleryItem(category="wedding", label="Wedding \u00b7 Reception", color="#2a2010", height=260, sort_order=4),
            GalleryItem(category="prewedding", label="Pre-Wedding \u00b7 Beach", color="#10202a", height=340, sort_order=5),
            GalleryItem(category="wedding", label="Wedding \u00b7 Details", color="#251a10", height=280, sort_order=6),
            GalleryItem(category="portrait", label="Portrait \u00b7 Natural light", color="#1a1a2a", height=220, sort_order=7),
            GalleryItem(category="wedding", label="Wedding \u00b7 First dance", color="#1e1a10", height=360, sort_order=8),
            GalleryItem(category="prewedding", label="Pre-Wedding \u00b7 Golden hour", color="#102020", height=240, sort_order=9),
        ])

    if User.query.filter_by(is_admin=True).count() == 0:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@thunderstudio.test")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        db.session.add(User(
            name="Studio Admin",
            email=admin_email,
            password_hash=generate_password_hash(admin_password),
            is_admin=True,
        ))
        print(f"[seed] Created default admin: {admin_email} / {admin_password} "
              f"\u2014 change this password after first login!")

    db.session.commit()


# ---------------------------------------------------------------- routes
def register_routes(app):

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/services")
    def services():
        items = Service.query.order_by(Service.sort_order).all()
        return render_template("services.html", services=items)

    @app.route("/gallery")
    def gallery():
        items = GalleryItem.query.order_by(GalleryItem.sort_order).all()
        categories = sorted({i.category for i in items})
        return render_template("gallery.html", items=items, categories=categories)

    # ------------------------------------------------------------ auth
    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            error = None
            if not name or not email or not password:
                error = "Please fill in every field."
            elif len(password) < 8:
                error = "Password must be at least 8 characters."
            elif User.query.filter_by(email=email).first():
                error = "An account with that email already exists."

            if error:
                flash(error, "error")
                return render_template("signup.html", name=name, email=email), 400

            user = User(name=name, email=email,
                        password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to Thunder Studio!", "success")
            return redirect(url_for("index"))

        return render_template("signup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash("Logged in successfully.", "success")
                next_url = request.args.get("next")
                return redirect(next_url or url_for("index"))

            flash("Incorrect email or password.", "error")
            return render_template("login.html", email=email), 401

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You've been logged out.", "success")
        return redirect(url_for("index"))

    # ------------------------------------------------------------ booking
    @app.route("/book", methods=["GET", "POST"])
    def book():
        service_items = Service.query.order_by(Service.sort_order).all()
        selected_service_id = request.values.get("service_id", type=int)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()
            event_date = request.form.get("event_date", "").strip()
            message = request.form.get("message", "").strip()
            service_id = request.form.get("service_id", type=int)

            if not name or not email:
                flash("Name and email are required.", "error")
                return render_template(
                    "book.html", services=service_items,
                    selected_service_id=service_id,
                ), 400

            booking = Booking(
                user_id=current_user.id if current_user.is_authenticated else None,
                service_id=service_id or None,
                name=name, email=email, phone=phone,
                event_date=event_date, message=message,
            )
            db.session.add(booking)
            db.session.commit()
            flash("Thanks! We've received your request and will be in touch soon.", "success")
            return redirect(url_for("services"))

        return render_template(
            "book.html", services=service_items,
            selected_service_id=selected_service_id,
        )

    @app.route("/account")
    @login_required
    def account():
        bookings = (
            Booking.query.filter_by(user_id=current_user.id)
            .order_by(Booking.created_at.desc()).all()
        )
        return render_template("account.html", bookings=bookings)

    # ------------------------------------------------------------ admin
    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        stats = {
            "users": User.query.count(),
            "services": Service.query.count(),
            "gallery": GalleryItem.query.count(),
            "bookings": Booking.query.count(),
            "new_bookings": Booking.query.filter_by(status="new").count(),
        }
        recent = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
        return render_template("admin/dashboard.html", stats=stats, recent=recent)

    # -- services CRUD
    @app.route("/admin/services")
    @admin_required
    def admin_services():
        items = Service.query.order_by(Service.sort_order).all()
        return render_template("admin/services.html", services=items)

    @app.route("/admin/services/new", methods=["GET", "POST"])
    @admin_required
    def admin_service_new():
        if request.method == "POST":
            _save_service(Service(), request.form)
            flash("Service created.", "success")
            return redirect(url_for("admin_services"))
        return render_template("admin/service_form.html", service=None)

    @app.route("/admin/services/<int:service_id>/edit", methods=["GET", "POST"])
    @admin_required
    def admin_service_edit(service_id):
        service = db.session.get(Service, service_id) or abort(404)
        if request.method == "POST":
            _save_service(service, request.form)
            flash("Service updated.", "success")
            return redirect(url_for("admin_services"))
        return render_template("admin/service_form.html", service=service)

    @app.route("/admin/services/<int:service_id>/delete", methods=["POST"])
    @admin_required
    def admin_service_delete(service_id):
        service = db.session.get(Service, service_id) or abort(404)
        db.session.delete(service)
        db.session.commit()
        flash("Service deleted.", "success")
        return redirect(url_for("admin_services"))

    # -- gallery CRUD
    @app.route("/admin/gallery")
    @admin_required
    def admin_gallery():
        items = GalleryItem.query.order_by(GalleryItem.sort_order).all()
        return render_template("admin/gallery.html", items=items)

    @app.route("/admin/gallery/new", methods=["GET", "POST"])
    @admin_required
    def admin_gallery_new():
        if request.method == "POST":
            _save_gallery_item(GalleryItem(), request.form)
            flash("Gallery item created.", "success")
            return redirect(url_for("admin_gallery"))
        return render_template("admin/gallery_form.html", item=None)

    @app.route("/admin/gallery/<int:item_id>/edit", methods=["GET", "POST"])
    @admin_required
    def admin_gallery_edit(item_id):
        item = db.session.get(GalleryItem, item_id) or abort(404)
        if request.method == "POST":
            _save_gallery_item(item, request.form)
            flash("Gallery item updated.", "success")
            return redirect(url_for("admin_gallery"))
        return render_template("admin/gallery_form.html", item=item)

    @app.route("/admin/gallery/<int:item_id>/delete", methods=["POST"])
    @admin_required
    def admin_gallery_delete(item_id):
        item = db.session.get(GalleryItem, item_id) or abort(404)
        db.session.delete(item)
        db.session.commit()
        flash("Gallery item deleted.", "success")
        return redirect(url_for("admin_gallery"))

    # -- bookings management
    @app.route("/admin/bookings")
    @admin_required
    def admin_bookings():
        items = Booking.query.order_by(Booking.created_at.desc()).all()
        return render_template("admin/bookings.html", bookings=items)

    @app.route("/admin/bookings/<int:booking_id>/status", methods=["POST"])
    @admin_required
    def admin_booking_status(booking_id):
        booking = db.session.get(Booking, booking_id) or abort(404)
        status = request.form.get("status")
        if status in {"new", "contacted", "confirmed", "declined"}:
            booking.status = status
            db.session.commit()
            flash("Booking status updated.", "success")
        return redirect(url_for("admin_bookings"))


def _save_service(service, form):
    service.icon = form.get("icon", "\u2726").strip() or "\u2726"
    service.title = form.get("title", "").strip()
    service.description = form.get("description", "").strip()
    service.features = form.get("features", "").strip()
    service.price_label = form.get("price_label", "").strip()
    service.featured = form.get("featured") == "on"
    service.badge = form.get("badge", "").strip() or None
    service.sort_order = int(form.get("sort_order") or 0)
    if service.id is None:
        db.session.add(service)
    db.session.commit()


def _save_gallery_item(item, form):
    item.category = form.get("category", "wedding").strip()
    item.label = form.get("label", "").strip()
    item.color = form.get("color", "#1a2535").strip() or "#1a2535"
    item.height = int(form.get("height") or 280)
    item.image_url = form.get("image_url", "").strip() or None
    item.sort_order = int(form.get("sort_order") or 0)
    if item.id is None:
        db.session.add(item)
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
