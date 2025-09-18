import os
import json
import datetime
import tempfile
from flask import Flask, request, jsonify, send_from_directory, render_template_string

# use static folder named "static"
app = Flask(__name__, static_folder="static", static_url_path="/static")

VERIFY_TOKEN = "Personal92!"
STATIC_FOLDER = app.static_folder
LATEST_PATH = os.path.join(STATIC_FOLDER, "latest_comment.json")

# ensure static folder exists and an initial latest_comment.json
os.makedirs(STATIC_FOLDER, exist_ok=True)
if not os.path.exists(LATEST_PATH):
    with open(LATEST_PATH, "w", encoding="utf-8") as f:
        json.dump({"user":"", "comment":""}, f, ensure_ascii=False)

# ---------- Facebook verification + webhook endpoint ----------
@app.route("/", methods=["GET", "POST"])
def webhook_root():
    if request.method == "GET":
        # Facebook verification
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        # Browser hit -> friendly message
        return "OBS Webhook Server — use /ui or /overlay", 200

    # POST: Facebook will send events here
    data = request.get_json(silent=True)
    print("Received webhook POST:", data, flush=True)

    # parse feed changes and extract comment + user
    try:
        for entry in (data or {}).get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") == "feed":
                    value = change.get("value", {})
                    if value.get("item") == "comment" or value.get("verb") == "add":
                        user = value.get("from", {}).get("name") or "FacebookUser"
                        message = value.get("message") or value.get("text") or ""
                        if message:
                            payload = {"user": user, "comment": message, "time": datetime.datetime.utcnow().isoformat()}
                            # atomic write to static/latest_comment.json
                            fd, tmp_path = tempfile.mkstemp(dir=STATIC_FOLDER)
                            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                                json.dump(payload, tmp, ensure_ascii=False)
                            os.replace(tmp_path, LATEST_PATH)
    except Exception as e:
        print("Error parsing webhook:", e, flush=True)

    return "EVENT_RECEIVED", 200


# ---------- OBS test endpoint (keeps your existing flow) ----------
@app.route("/webhook", methods=["POST"])
def obs_webhook():
    data = request.get_json(silent=True) or {}
    user = data.get("user", "OBS")
    comment = data.get("comment", "")
    if comment:
        payload = {"user": user, "comment": comment, "time": datetime.datetime.utcnow().isoformat()}
        fd, tmp_path = tempfile.mkstemp(dir=STATIC_FOLDER)
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(payload, tmp, ensure_ascii=False)
        os.replace(tmp_path, LATEST_PATH)
    return jsonify({"status": "ok"}), 200


# ---------- endpoint to read latest comment (used by overlay) ----------
@app.route("/latest_comment", methods=["GET"])
def latest_comment():
    try:
        with open(LATEST_PATH, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify({"user":"", "comment":""})


# ---------- serve overlay HTML from /overlay ----------
@app.route("/overlay")
def overlay():
    # serve the static overlay.html if present, otherwise a fallback
    overlay_path = os.path.join(STATIC_FOLDER, "overlay.html")
    if os.path.exists(overlay_path):
        return send_from_directory(STATIC_FOLDER, "overlay.html")
    # fallback minimal page
    return render_template_string("<h3>Overlay not found. Upload static/overlay.html</h3>"), 404


# ---------- UI and other endpoints (optional) ----------
@app.route("/ui")
def ui():
    return send_from_directory(STATIC_FOLDER, "ui.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
