
"""
AccessPathAI — Paavai Engineering College, Namakkal
===================================================

Flask backend for AccessPathAI.

Features:
- Serves the existing HTML/CSS/JS frontend
- Google Translate proxy
- Emergency SOS logging
- Recent SOS API
- Campus configuration API
- Health-check API

Run:
    pip install -r requirements.txt
    python app.py

Open:
    http://127.0.0.1:5000
"""

import os
import sqlite3
import datetime
from pathlib import Path

import requests
from flask import Flask, render_template, request, jsonify, g, send_from_directory


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "accesspath.db"

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)


# ============================================================
# PAAVAI ENGINEERING COLLEGE CONFIGURATION
# ============================================================

CAMPUS_CONFIG = {
    "name": "Paavai Engineering College",
    "short_name": "Paavai",
    "location": "Namakkal, Tamil Nadu, India",

    # Used when generating Google Maps directions.
    #
    # IMPORTANT:
    # Replace this with the exact Google Maps address
    # of your Paavai Engineering College campus if necessary.
    "address": (
        "Paavai Engineering College, "
        "Paavai Nagar, Pachal, "
        "Namakkal, Tamil Nadu, India"
    ),

    "default_travel_mode": "walking",

    "languages": [
        {
            "code": "en-IN",
            "name": "English (India)"
        },
        {
            "code": "ta-IN",
            "name": "தமிழ் (Tamil)"
        },
        {
            "code": "hi-IN",
            "name": "हिन्दी (Hindi)"
        },
        {
            "code": "te-IN",
            "name": "తెలుగు (Telugu)"
        },
        {
            "code": "kn-IN",
            "name": "ಕನ್ನಡ (Kannada)"
        },
        {
            "code": "ml-IN",
            "name": "മലയാളം (Malayalam)"
        }
    ]
}


# ============================================================
# DATABASE
# ============================================================

def get_db():
    """
    Open SQLite connection for the current request.
    """
    if "db" not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row

    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    """
    Close database connection after every request.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """
    Create required database tables.
    """

    conn = sqlite3.connect(str(DB_PATH))

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sos_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            page TEXT,

            lat REAL,

            lng REAL,

            message TEXT,

            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")


@app.route("/shuttle.html")
def shuttle():
    return render_template("shuttle.html")


@app.route("/virtual.html")
def virtual():
    return render_template("virtual.html")


@app.route("/wheelchair.html")
def wheelchair():
    return render_template("wheelchair.html")


@app.route("/manifest.webmanifest")
def manifest():
    return send_from_directory(BASE_DIR, "manifest.webmanifest")


@app.route("/service-worker.js")
def service_worker():
    response = send_from_directory(BASE_DIR / "static", "service-worker.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def api_health():

    return jsonify({
        "status": "ok",
        "application": "AccessPathAI",
        "campus": CAMPUS_CONFIG["name"],
        "location": CAMPUS_CONFIG["location"]
    })


# ============================================================
# CAMPUS CONFIGURATION API
# ============================================================

@app.route("/api/campus", methods=["GET"])
def api_campus():

    return jsonify({
        "name": CAMPUS_CONFIG["name"],
        "short_name": CAMPUS_CONFIG["short_name"],
        "location": CAMPUS_CONFIG["location"],
        "address": CAMPUS_CONFIG["address"],
        "travel_mode": CAMPUS_CONFIG["default_travel_mode"],
        "languages": CAMPUS_CONFIG["languages"]
    })


# ============================================================
# TRANSLATION API
# ============================================================

@app.route("/api/translate", methods=["POST"])
def api_translate():
    """
    Translate text using Google's public translation endpoint.

    Request:

        {
            "text": "Where is the library?",
            "target": "ta"
        }

    Response:

        {
            "translated": "...",
            "original": "..."
        }
    """

    payload = request.get_json(silent=True) or {}

    text = str(
        payload.get("text", "")
    ).strip()

    target = str(
        payload.get("target", "en")
    ).strip()

    if not text:

        return jsonify({
            "error": "No text provided",
            "translated": ""
        }), 400

    if not target:
        target = "en"

    try:

        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",

            params={
                "client": "gtx",
                "sl": "auto",
                "tl": target,
                "dt": "t",
                "q": text
            },

            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        translated_parts = []

        if (
            isinstance(data, list)
            and len(data) > 0
            and isinstance(data[0], list)
        ):

            for part in data[0]:

                if (
                    isinstance(part, list)
                    and len(part) > 0
                    and isinstance(part[0], str)
                ):
                    translated_parts.append(part[0])

        translated = " ".join(
            translated_parts
        ).strip()

        if not translated:

            return jsonify({
                "error": "Empty translation response",
                "translated": ""
            }), 502

        return jsonify({
            "translated": translated,
            "original": text
        })

    except requests.RequestException as exc:

        return jsonify({
            "error": str(exc),
            "translated": ""
        }), 502


# ============================================================
# SOS API
# ============================================================

@app.route("/api/sos", methods=["POST"])
def api_sos():
    """
    Store Emergency SOS event.

    Request:

        {
            "page": "index",
            "lat": 11.234,
            "lng": 78.456,
            "message": "Emergency assistance required"
        }
    """

    payload = request.get_json(
        silent=True
    ) or {}

    page = str(
        payload.get(
            "page",
            "unknown"
        )
    ).strip()

    message = str(
        payload.get(
            "message",
            ""
        )
    ).strip()

    lat = payload.get("lat")
    lng = payload.get("lng")

    # Safely convert coordinates.
    try:

        lat = float(lat) if lat is not None else None

    except (TypeError, ValueError):

        lat = None

    try:

        lng = float(lng) if lng is not None else None

    except (TypeError, ValueError):

        lng = None

    created_at = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()

    db = get_db()

    db.execute(
        """
        INSERT INTO sos_events
        (
            page,
            lat,
            lng,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,

        (
            page,
            lat,
            lng,
            message,
            created_at
        )
    )

    db.commit()

    print(
        f"[SOS] "
        f"campus={CAMPUS_CONFIG['name']} "
        f"page={page} "
        f"lat={lat} "
        f"lng={lng} "
        f"time={created_at} "
        f"message={message}"
    )

    return jsonify({
        "status": "logged",
        "campus": CAMPUS_CONFIG["name"],
        "created_at": created_at
    })


# ============================================================
# RECENT SOS EVENTS
# ============================================================

@app.route("/api/sos/recent", methods=["GET"])
def api_sos_recent():

    db = get_db()

    rows = db.execute(
        """
        SELECT
            id,
            page,
            lat,
            lng,
            message,
            created_at
        FROM sos_events
        ORDER BY id DESC
        LIMIT 50
        """
    ).fetchall()

    return jsonify([
        dict(row)
        for row in rows
    ])


# ============================================================
# CLEAR SOS EVENTS
# ============================================================

@app.route("/api/sos/clear", methods=["POST"])
def api_sos_clear():

    db = get_db()

    db.execute(
        "DELETE FROM sos_events"
    )

    db.commit()

    return jsonify({
        "status": "cleared"
    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "error": "Route not found"
    }), 404


@app.errorhandler(500)
def server_error(error):

    return jsonify({
        "error": "Internal server error"
    }), 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    init_db()

    print()
    print("=" * 60)
    print("AccessPathAI")
    print("Paavai Engineering College, Namakkal")
    print("=" * 60)
    print()
    print("Campus :", CAMPUS_CONFIG["name"])
    print("Location:", CAMPUS_CONFIG["location"])
    print("URL    : http://127.0.0.1:5000")
    print()
    print("API:")
    print("  /api/health")
    print("  /api/campus")
    print("  /api/translate")
    print("  /api/sos")
    print("  /api/sos/recent")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
