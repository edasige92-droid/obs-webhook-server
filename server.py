from flask import Flask, request, jsonify, render_template_string
import datetime

app = Flask(__name__)

# Store comments in memory (reset on restart)
comments = []

# Facebook Verify Token
VERIFY_TOKEN = "Personal92!"

# -------------------------------
# Facebook Webhook Verification
# -------------------------------
@app.route("/", methods=["GET"])
def facebook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Facebook webhook verified!")
        return challenge, 200
    else:
        return "Verification failed", 403


# -------------------------------
# Facebook Webhook Event Receiver
# -------------------------------
@app.route("/", methods=["POST"])
def facebook_webhook():
    data = request.get_json()
    print("📩 Facebook Webhook Event:", data)

    # Optional: store as a comment for testing
    comments.append({
        "user": "Facebook",
        "comment": str(data),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return "EVENT_RECEIVED", 200


# -------------------------------
# OBS Webhook Endpoints
# -------------------------------
@app.route("/webhook", methods=["POST"])
def obs_webhook():
    data = request.get_json()
    print("🎥 OBS Webhook Event:", data)

    comments.append({
        "user": data.get("user", "Anonymous"),
        "comment": data.get("comment", ""),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({"status": "success", "message": "Comment received!"}), 200


@app.route("/comments", methods=["GET"])
def get_comments():
    return jsonify(comments)


@app.route("/clear", methods=["POST"])
def clear_comments():
    comments.clear()
    return jsonify({"status": "cleared"})


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "running", "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


# -------------------------------
# Simple UI
# -------------------------------
@app.route("/ui", methods=["GET"])
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OBS Webhook Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .card { background: #f9f9f9; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            h1 { color: #0056ff; }
            input, button { padding: 8px; margin: 5px; }
        </style>
    </head>
    <body>
        <h1>🎬 OBS Webhook Server</h1>
        <p>Server is running and ready to receive comments!</p>

        <div class="card">
            <h3>📄 Available Endpoints:</h3>
            <ul>
                <li><b>POST /webhook</b> - Receive OBS comments (JSON)</li>
                <li><b>GET /comments</b> - View all received comments</li>
                <li><b>GET /health</b> - Check server status</li>
                <li><b>POST /clear</b> - Clear all comments</li>
                <li><b>GET /</b> - Facebook Webhook Verification</li>
                <li><b>POST /</b> - Facebook Webhook Events</li>
            </ul>
        </div>

        <div class="card">
            <h3>🚀 Quick Test:</h3>
            <form action="/webhook" method="post" onsubmit="sendComment(event)">
                <input type="text" id="comment" placeholder="Enter test comment" required>
                <input type="text" id="user" value="TestUser">
                <button type="submit">Send Test Comment</button>
            </form>
        </div>

        <div class="card">
            <h3>📊 Stats:</h3>
            <p>Total comments received: <span id="count">0</span></p>
            <p>Server status: 🟢 Running</p>
            <p>Server time: <span id="time"></span></p>
        </div>

        <script>
            async function sendComment(event) {
                event.preventDefault();
                const comment = document.getElementById("comment").value;
                const user = document.getElementById("user").value;
                await fetch("/webhook", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ comment, user })
                });
                alert("Comment sent!");
                loadStats();
            }

            async function loadStats() {
                const res = await fetch("/comments");
                const data = await res.json();
                document.getElementById("count").innerText = data.length;

                const health = await fetch("/health");
                const h = await health.json();
                document.getElementById("time").innerText = h.time;
            }
            loadStats();
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
