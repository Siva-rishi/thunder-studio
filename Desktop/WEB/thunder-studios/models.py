from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="user", lazy=True)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(10), default="\u2726")
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    features = db.Column(db.Text, nullable=False, default="")  # one per line
    price_label = db.Column(db.String(80), nullable=False)
    featured = db.Column(db.Boolean, default=False)
    badge = db.Column(db.String(60))
    sort_order = db.Column(db.Integer, default=0)

    bookings = db.relationship("Booking", backref="service", lazy=True)

    def feature_list(self):
        return [f.strip() for f in (self.features or "").split("\n") if f.strip()]


class GalleryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(40), nullable=False)  # wedding / prewedding / portrait
    label = db.Column(db.String(160), nullable=False)
    color = db.Column(db.String(20), default="#1a2535")
    height = db.Column(db.Integer, default=280)
    image_url = db.Column(db.String(400))  # optional real photo, falls back to color block
    sort_order = db.Column(db.Integer, default=0)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40))
    event_date = db.Column(db.String(40))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default="new")  # new / contacted / confirmed / declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
