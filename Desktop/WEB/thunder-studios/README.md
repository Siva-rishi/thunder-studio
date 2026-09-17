# Thunder Studio — Backend

A Flask backend for the Thunder Studio site: user accounts, a booking system,
and an admin panel to manage services and gallery content — all built on your
existing design (`style.css`, `auth.css`, fonts, the lightning bolt, etc).

## What's included

- **Auth** — signup, login, logout, sessions (Flask-Login), hashed passwords.
- **Booking system** — a public `/book` form (name, email, phone, event date,
  service, message). Logged-in users see their requests under "My Bookings".
- **Admin panel** (`/admin`) — full CRUD for Services and Gallery items, plus a
  bookings inbox where you can change status (new / contacted / confirmed /
  declined). The homepage, Services, and Gallery pages now read from the
  database instead of hardcoded HTML, so editing them in `/admin` updates the
  live site immediately.
- **SQLite database**, auto-created on first run, seeded with your original
  services and gallery placeholders plus a default admin account.

## Setup

```bash
cd thunder-backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

Visit **http://127.0.0.1:5000**.

On first run it prints a default admin login in the terminal:

```
admin@thunderstudio.test / admin123
```

**Log in and change that password immediately** — there's currently no
"change password" screen, so for now that means editing the user's row
directly in `instance/thunder.db`, or deleting the DB file and setting your
own via environment variables before the first run:

```bash
ADMIN_EMAIL=you@yourstudio.com ADMIN_PASSWORD=something-strong python3 app.py
```

## Project layout

```
thunder-backend/
├── app.py              # routes, app factory, seed data
├── models.py           # User, Service, GalleryItem, Booking
├── extensions.py       # db + login_manager singletons
├── requirements.txt
├── instance/
│   └── thunder.db      # created automatically
├── static/
│   ├── style.css       # your original file + nav/flash styles it was missing
│   ├── auth.css        # your original file, untouched
│   ├── pages.css       # new — styles for services/gallery/booking/tables
│   ├── admin.css       # new — admin panel styling
│   └── script.js       # your original file, untouched
└── templates/
    ├── base.html        # shared nav/footer, extended by every page
    ├── index.html, services.html, gallery.html
    ├── signup.html, login.html, book.html, account.html
    └── admin/
        ├── dashboard.html, services.html, service_form.html
        ├── gallery.html, gallery_form.html, bookings.html
```

## Notes on things I added or changed

- Your uploaded `index.html`, `gallery.html`, `services.html` had empty
  `.nav-links` divs and `style.css` had no `.nav` rules at all, so the site
  had no working navigation. I added a real nav (Home / Services / Gallery /
  account links) in `templates/base.html` plus the missing CSS.
- `signup.html` linked to `login.html`, which wasn't in your upload — I built
  it to match the existing auth page style.
- `gallery.html` and `services.html` linked `pages.css`, which also wasn't
  provided — I wrote it to match your dark/gold/blue palette.
- Passwords are hashed with Werkzeug's `generate_password_hash` — never
  stored in plain text.
- This is a development setup (Flask's built-in server, `debug=True`). For
  production, run behind Gunicorn/uWSGI + Nginx, set a real `SECRET_KEY` env
  var, and turn debug off.
