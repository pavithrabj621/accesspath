# AccessPathAI — Full-Stack Python Version

Same UI, same functionality as the original static site — now served by a
real Python (Flask) backend instead of raw HTML files.

## What changed vs. the original repo

- **Backend added:** Flask (`app.py`) serves all 4 pages and exposes real
  API endpoints:
  - `POST /api/translate` — server-side proxy for destination translation
    (previously called directly from the browser).
  - `POST /api/sos` — logs every Emergency SOS press (page, GPS lat/lng,
    message, timestamp) into a local SQLite database (`accesspath.db`,
    created automatically on first run).
  - `GET /api/sos/recent` — returns the last 50 SOS events as JSON, useful
    for building an admin/monitoring view later.
- **Frontend:** untouched UI/UX. Same HTML structure, same CSS, same
  navigation, same voice assistant / GPS / camera / shuttle simulation —
  all client-side browser features (Geolocation, Web Speech API,
  TensorFlow.js object detection) still run exactly as before, in the browser.
- Page files are served at the exact same paths the JS already expects
  (`/`, `/index.html`, `/shuttle.html`, `/virtual.html`, `/wheelchair.html`),
  so none of the original navigation code (`window.location.href = "..."`)
  needed to change.

## Folder structure

```
AccessPathAI_FullStack/
├── app.py               # Flask backend (routes + API + SQLite)
├── requirements.txt
├── templates/
│   ├── index.html        # AI Voice Assistant / dashboard (home page)
│   ├── shuttle.html       # Campus Shuttle Live tracking
│   ├── virtual.html       # Visual AI Guidance (camera + TensorFlow.js)
│   └── wheelchair.html    # Wheelchair Access Routes
├── static/                # reserved for any future extracted CSS/JS/images
└── accesspath.db          # created automatically on first run (SQLite)
```

## How to run

1. Make sure you have **Python 3.9+** installed.
2. Open a terminal in this folder and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   python app.py
   ```
4. Open your browser at:
   ```
   http://127.0.0.1:5000
   ```

That's it — no build step, no Node.js, no external services required
beyond an internet connection (needed for the Google Fonts/Lucide/
TensorFlow.js CDN scripts and for real-time GPS/voice/translation to work).

## Notes

## Voice-first workflow

The browser is the voice orchestration layer. On the home page it greets the
user, listens for a destination, repeats the recognized destination, and
accepts a spoken yes/no confirmation before creating a Google Maps Directions
URL with the live GPS source and walking navigation mode. The Maps URL opens in
its own window so the visual guidance page can remain active in the app tab.

Supported voice commands are:

| Context | Voice phrases | Result |
| --- | --- | --- |
| Home | Any destination, "yes", "no" | Confirm or retry the destination, then launch navigation |
| Home or virtual | "shuttle", "shuttle near me", "shuttle schedule" | Open `shuttle.html` |
| Home, virtual, or shuttle | "emergency", "SOS", "help" | Log an SOS with the latest GPS coordinates |
| Virtual or shuttle | "back", "home", "main navigation" | Return to the home voice assistant |
| Shuttle | "arrival", "ETA", "route", "next stop", "repeat" | Speak current simulated shuttle status |

When a route enters `virtual.html`, AccessPathAI asks, “Would you like to
enable camera for your safety?” A spoken yes starts `getUserMedia` with the
rear-facing camera and Vision AI; a spoken no keeps voice navigation active
without camera access. Browser permission prompts cannot be bypassed by web
code, so the first visit still requires the user to grant microphone, camera,
and location permissions. Web Speech recognition and speech synthesis also
depend on browser and operating-system accessibility support such as TalkBack
or VoiceOver.

The implementation is intentionally progressive: Google Maps turn-by-turn
guidance is provided through the official Maps Directions URL, while camera
analysis uses TensorFlow.js in `virtual.html`, shuttle data is presented by
the existing live simulation, and SOS events are persisted by Flask at
`POST /api/sos`.

- Camera-based Visual AI Guidance (`virtual.html`) and voice input require
  the browser to grant camera/microphone/location permissions — this is
  standard browser behavior and works the same as it did in the static
  version.
- `accesspath.db` is created automatically the first time you run
  `python app.py`. Delete it any time to reset the SOS log.
- This is a Flask **development server**. For real deployment, run it
  behind a production WSGI server (e.g. `gunicorn app:app`) and set
  `debug=False` in `app.py`.
