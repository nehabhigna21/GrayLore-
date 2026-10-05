import os
import uuid
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

import tmdb

app = Flask(__name__)
app.secret_key = "graylore-dev-secret"  # change before any real deployment

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",       # set your MySQL password here
    "database": "graylore"
}

ADMIN_EMAIL = "admin@graylore.com"
DEFAULT_REGION = "IN"   # demo assumes the viewer is browsing from India
RATE_PER_MIN = 0.05


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def current_user_id():
    return session.get("user_id")


def current_profile_id():
    return session.get("profile_id")


def require_login():
    return current_user_id() is not None


# ---------- Auth ----------

@app.route("/")
def index():
    if not require_login():
        return redirect(url_for("auth"))
    if not current_profile_id():
        return redirect(url_for("profiles"))
    return redirect(url_for("home"))


@app.route("/auth")
def auth():
    return render_template("auth.html")


@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, generate_password_hash(password))
        )
        user_id = cur.lastrowid
        # Every new user starts on Basic until they pick a plan
        cur.execute(
            "INSERT INTO Subscriptions (user_id, plan_type, device_limit, start_date, status) "
            "VALUES (%s, 'Basic', 1, %s, 'active')",
            (user_id, date.today())
        )
        conn.commit()
        session["user_id"] = user_id
    except mysql.connector.IntegrityError:
        flash("An account with that email already exists.")
        return redirect(url_for("auth"))
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("profiles"))


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["user_id"]
        return redirect(url_for("profiles"))

    flash("Invalid email or password.")
    return redirect(url_for("auth"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))


# ---------- Profiles ----------

@app.route("/profiles", methods=["GET", "POST"])
def profiles():
    if not require_login():
        return redirect(url_for("auth"))

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["profile_name"]
        is_kids = 1 if request.form.get("is_kids") == "on" else 0
        cur.execute(
            "INSERT INTO Profiles (user_id, profile_name, is_kids) VALUES (%s, %s, %s)",
            (current_user_id(), name, is_kids)
        )
        conn.commit()

    cur.execute("SELECT * FROM Profiles WHERE user_id = %s", (current_user_id(),))
    profile_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("profile.html", profiles=profile_list)


@app.route("/select_profile/<int:profile_id>")
def select_profile(profile_id):
    session["profile_id"] = profile_id
    return redirect(url_for("home"))


# ---------- Home / Catalog ----------

@app.route("/home")
def home():
    if not require_login():
        return redirect(url_for("auth"))
    if not current_profile_id():
        return redirect(url_for("profiles"))

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # Full catalog — only titles currently licensed for DEFAULT_REGION
    cur.execute("""
        SELECT c.content_id, c.title, c.genre, c.release_date, c.duration_min,
               c.age_rating, c.overview, c.poster_url, c.backdrop_url, c.trailer_key,
               l.region
        FROM Content c
        JOIN Licenses l ON c.content_id = l.content_id
        WHERE l.region = %s AND CURDATE() BETWEEN l.license_start AND l.license_end
        ORDER BY c.content_id DESC
    """, (DEFAULT_REGION,))
    catalog = cur.fetchall()

    # Continue watching — this profile's most recent watch per title,
    # with the resume position so the card can show a progress bar
    cur.execute("""
        SELECT c.content_id, c.title, c.genre, c.overview, c.poster_url, c.backdrop_url,
               c.duration_min, c.release_date, c.age_rating,
               w.position_sec, w.watched_at AS last_watched
        FROM WatchHistory w
        JOIN Content c ON w.content_id = c.content_id
        WHERE w.profile_id = %s
          AND w.watch_id = (
              SELECT w2.watch_id FROM WatchHistory w2
              WHERE w2.profile_id = w.profile_id AND w2.content_id = w.content_id
              ORDER BY w2.watched_at DESC, w2.watch_id DESC LIMIT 1
          )
        ORDER BY w.watched_at DESC
        LIMIT 6
    """, (current_profile_id(),))
    continue_watching = cur.fetchall()

    # Recommendations — co-watch correlation: titles watched by profiles
    # who also watched something this profile watched
    cur.execute("""
        SELECT c.content_id, c.title, c.genre, c.overview, c.poster_url, c.backdrop_url,
               c.release_date, c.age_rating, COUNT(*) AS shared_viewers
        FROM WatchHistory w1
        JOIN WatchHistory w2
          ON w1.profile_id = w2.profile_id AND w1.content_id != w2.content_id
        JOIN Content c ON w2.content_id = c.content_id
        WHERE w1.profile_id = %s
        GROUP BY c.content_id, c.title, c.genre, c.overview, c.poster_url, c.backdrop_url,
                 c.release_date, c.age_rating
        ORDER BY shared_viewers DESC
        LIMIT 6
    """, (current_profile_id(),))
    recommendations = cur.fetchall()

    # Trending — most total watch-minutes across all profiles
    cur.execute("""
        SELECT c.content_id, c.title, c.genre, c.overview, c.poster_url, c.backdrop_url,
               c.release_date, c.age_rating, SUM(w.watch_minutes) AS total_minutes
        FROM WatchHistory w
        JOIN Content c ON w.content_id = c.content_id
        GROUP BY c.content_id, c.title, c.genre, c.overview, c.poster_url, c.backdrop_url,
                 c.release_date, c.age_rating
        ORDER BY total_minutes DESC
        LIMIT 6
    """)
    trending = cur.fetchall()

    cur.close()
    conn.close()
    return render_template(
        "home.html",
        catalog=catalog,
        continue_watching=continue_watching,
        recommendations=recommendations,
        trending=trending
    )


# ---------- Playback ----------

@app.route("/play/<int:content_id>")
def play(content_id):
    if not require_login() or not current_profile_id():
        return redirect(url_for("auth"))

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # License check — block playback outside licensed region/date window
    cur.execute("""
        SELECT * FROM Licenses
        WHERE content_id = %s AND region = %s
          AND CURDATE() BETWEEN license_start AND license_end
    """, (content_id, DEFAULT_REGION))
    license_row = cur.fetchone()
    if not license_row:
        cur.close()
        conn.close()
        flash("This title isn't licensed for playback in your region right now.")
        return redirect(url_for("home"))

    # Device-session bookkeeping — trigger enforces the plan's device limit
    device_id = session.get("device_id") or str(uuid.uuid4())
    session["device_id"] = device_id
    cur.execute(
        "INSERT INTO Sessions (user_id, device_id) VALUES (%s, %s)",
        (current_user_id(), device_id)
    )

    # Resume point — last position this profile reached on this title
    cur.execute("""
        SELECT position_sec, watched_at FROM WatchHistory
        WHERE profile_id = %s AND content_id = %s
        ORDER BY watched_at DESC, watch_id DESC LIMIT 1
    """, (current_profile_id(), content_id))
    last = cur.fetchone()
    resume_sec = last["position_sec"] if last else 0

    # Open a new watch-history row for this viewing; the player updates it
    # via /progress as playback advances
    cur.execute(
        "INSERT INTO WatchHistory (profile_id, content_id, watch_minutes, position_sec) "
        "VALUES (%s, %s, 0, %s)",
        (current_profile_id(), content_id, resume_sec)
    )
    watch_id = cur.lastrowid
    conn.commit()

    cur.execute("SELECT * FROM Content WHERE content_id = %s", (content_id,))
    content = cur.fetchone()
    cur.close()
    conn.close()
    return render_template(
        "player.html",
        content=content,
        watch_id=watch_id,
        resume_sec=resume_sec,
        last_watched=last["watched_at"] if last else None
    )


@app.route("/progress", methods=["POST"])
def progress():
    """
    Called by the player every few seconds (and on pause / page close).
    Body: {"watch_id": int, "position_sec": int, "watched_sec": int}
    Updates the current viewing's resume position and total minutes watched.
    """
    if not require_login() or not current_profile_id():
        return jsonify(ok=False), 401
    data = request.get_json(silent=True) or {}
    try:
        watch_id = int(data["watch_id"])
        position_sec = max(0, int(data.get("position_sec", 0)))
        watched_sec = max(0, int(data.get("watched_sec", 0)))
    except (KeyError, ValueError, TypeError):
        return jsonify(ok=False), 400

    conn = get_db()
    cur = conn.cursor()
    # profile_id in the WHERE clause stops one profile updating another's row
    cur.execute("""
        UPDATE WatchHistory
        SET position_sec = %s,
            watch_minutes = GREATEST(watch_minutes, %s),
            watched_at = NOW()
        WHERE watch_id = %s AND profile_id = %s
    """, (position_sec, watched_sec // 60, watch_id, current_profile_id()))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(ok=True)


# ---------- Ratings ----------

@app.route("/rate", methods=["POST"])
def rate():
    content_id = request.form["content_id"]
    rating = request.form["rating"]
    review = request.form.get("review", "")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Ratings (profile_id, content_id, rating, review)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE rating = VALUES(rating), review = VALUES(review)
    """, (current_profile_id(), content_id, rating, review))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("home"))


# ---------- Billing ----------

PLAN_PRICES = {"Basic": (149, 1), "Standard": (399, 2), "Premium": (649, 4)}

@app.route("/billing", methods=["POST"])
def billing():
    if not require_login():
        return redirect(url_for("auth"))

    plan = request.form["plan_type"]
    price, device_limit = PLAN_PRICES[plan]

    conn = get_db()
    cur = conn.cursor()
    # Trigger auto-cancels the previous active subscription
    cur.execute("""
        INSERT INTO Subscriptions (user_id, plan_type, device_limit, start_date, status)
        VALUES (%s, %s, %s, %s, 'active')
    """, (current_user_id(), plan, device_limit, date.today()))
    sub_id = cur.lastrowid
    cur.execute("""
        INSERT INTO Payments (user_id, sub_id, amount, payment_date, status)
        VALUES (%s, %s, %s, %s, 'paid')
    """, (current_user_id(), sub_id, price, date.today()))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("home"))


# ---------- Admin ----------

@app.route("/admin")
def admin():
    if not require_login():
        return redirect(url_for("auth"))

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT email FROM Users WHERE user_id = %s", (current_user_id(),))
    user = cur.fetchone()
    if not user or user["email"] != ADMIN_EMAIL:
        cur.close()
        conn.close()
        return "Admin access only.", 403

    cur.execute("""
        SELECT c.content_id, c.title, c.genre, c.tmdb_id, c.poster_url, c.video_url,
               l.region, l.license_end
        FROM Content c
        LEFT JOIN Licenses l ON c.content_id = l.content_id
        ORDER BY c.content_id DESC
    """)
    content_rows = cur.fetchall()

    # Royalty payout — computed live, not stored (see schema note on Payouts)
    cur.execute("""
        SELECT c.title,
               COALESCE(SUM(w.watch_minutes), 0) AS total_minutes,
               ROUND(COALESCE(SUM(w.watch_minutes), 0) * %s, 2) AS payout_amount
        FROM Content c
        LEFT JOIN WatchHistory w ON c.content_id = w.content_id
        GROUP BY c.content_id, c.title
        ORDER BY payout_amount DESC
    """, (RATE_PER_MIN,))
    payouts = cur.fetchall()

    cur.execute("SELECT COUNT(*) AS n FROM Subscriptions WHERE status = 'active'")
    active_subs = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM Content")
    total_titles = cur.fetchone()["n"]
    cur.execute("SELECT COALESCE(SUM(watch_minutes),0) AS n FROM WatchHistory")
    total_minutes = cur.fetchone()["n"]

    cur.close()
    conn.close()
    return render_template(
        "admin.html",
        content_rows=content_rows,
        payouts=payouts,
        active_subs=active_subs,
        total_titles=total_titles,
        total_minutes=total_minutes,
        rate_per_min=RATE_PER_MIN,
        tmdb_enabled=bool(os.environ.get("TMDB_API_KEY"))
    )


@app.route("/admin/add_content", methods=["POST"])
def admin_add_content():
    title = request.form["title"]
    genre = request.form["genre"]
    region = request.form["region"]
    license_end = request.form["license_end"]
    video_url = request.form.get("video_url") or None

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Content (title, genre, release_date, duration_min, video_url) "
        "VALUES (%s, %s, CURDATE(), 100, %s)",
        (title, genre, video_url)
    )
    content_id = cur.lastrowid
    cur.execute(
        "INSERT INTO Licenses (content_id, region, license_start, license_end) VALUES (%s, %s, CURDATE(), %s)",
        (content_id, region, license_end)
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin"))


@app.route("/admin/import_tmdb", methods=["POST"])
def admin_import_tmdb():
    """Search TMDB for a title and import the best match (admin only)."""
    if not require_login():
        return redirect(url_for("auth"))
    query = request.form.get("query", "").strip()
    region = request.form.get("region") or DEFAULT_REGION
    if not query:
        return redirect(url_for("admin"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT email FROM Users WHERE user_id = %s", (current_user_id(),))
    row = cur.fetchone()
    if not row or row[0] != ADMIN_EMAIL:
        cur.close()
        conn.close()
        return "Admin access only.", 403

    try:
        hits = tmdb.search_movies(query, limit=1)
        if not hits:
            flash(f"TMDB has no results for \"{query}\".")
        else:
            movie = tmdb.fetch_movie(hits[0]["tmdb_id"])
            tmdb.upsert_content(cur, movie, region=region)
            conn.commit()
            flash(f"Imported \"{movie['title']}\" from TMDB, licensed for {region}.")
    except tmdb.TMDBError as e:
        flash(f"TMDB error: {e}")
    except Exception as e:
        flash(f"Import failed: {e}")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
